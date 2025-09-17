<?php
session_start();
include 'config.php';

// Check if user is logged in
if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}

// Fetch user details
$userId = $_SESSION['user_id'];
$stmt = $pdo->prepare("SELECT username, role, profile_picture FROM users WHERE user_id = ?");
$stmt->execute([$userId]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);
if (!$user) {
    $error = 'User not found.';
    include 'dashboard_template.php';
    exit;
}
// Ensure session user_role is always in sync
$_SESSION['user_role'] = $user['role'];

// Initialize messages
$success = '';
$warning = '';
$error = '';

// Check if required tables exist
$requiredTables = ['sales', 'sale_items', 'products', 'inventory', 'users'];
foreach ($requiredTables as $table) {
    $stmt = $pdo->query("SHOW TABLES LIKE '$table'");
    if ($stmt->rowCount() === 0) {
        $error = "Table '$table' does not exist in the database.";
        include 'dashboard_template.php';
        exit;
    }
}

// Handle filter and search
$filter = filter_input(INPUT_GET, 'filter', FILTER_SANITIZE_STRING) ?? 'Daily';
$search = filter_input(INPUT_GET, 'search', FILTER_SANITIZE_STRING) ?? '';

// If secretary, force filter to Daily
if ($user['role'] === 'secretary') {
    $filter = 'Daily';
}

// Determine date range based on filter and local time
if (isset($_GET['local_time'])) {
    $userLocalTime = $_GET['local_time'];
    $currentDate = date('Y-m-d', strtotime($userLocalTime));
} else {
    $currentDate = date('Y-m-d');
}
// Calculate days for filter
$days = ($filter === 'Weekly') ? 6 : 0;

// Define low stock threshold
$lowStockThreshold = 10;
$highStockThreshold = 30;

// Function to fetch all dashboard data
function fetchDashboardData($pdo, $days, $search, $lowStockThreshold, $highStockThreshold, $recentSalesRange = 'today') {
    $data = [
        'totalProducts' => 0,
        'totalSales' => 0.0,
        'restock_alerts' => 0,
        'transactionCount' => 0,
        'totalUnitsSold' => 0,
        'totalBoxesSold' => 0,
        'recentSales' => [],
        'topSellingProduct' => null,
        'inventoryStatus' => [],
        'warning' => ''
    ];

    try {
        // Build date condition for sales queries (historical: last $days days)
        $dateCondition = "DATE(recorded_at) BETWEEN DATE_SUB(CURDATE(), INTERVAL ? DAY) AND CURDATE()";
        $params = [$days];

        // Build search condition
        $searchCondition = $search ? "AND (LOWER(p.name) LIKE ? OR LOWER(p.size) LIKE ?)" : "";
        $searchParams = $search ? ["%" . strtolower($search) . "%", "%" . strtolower($search) . "%"] : [];

        // Total Products (Active products only)
        $stmt = $pdo->prepare("SELECT COUNT(DISTINCT p.product_id) 
                              FROM products p 
                              WHERE p.status = 'Active' " . $searchCondition);
        if ($searchCondition) {
            $stmt->execute($searchParams);
        } else {
            $stmt->execute();
        }
        $data['totalProducts'] = (int)$stmt->fetchColumn();

        // Total Sales (historical) - Only for admin
        if (isset($_SESSION['user_role']) && $_SESSION['user_role'] === 'admin') {
            $salesQuery = "SELECT COALESCE(SUM(s.total), 0) 
                          FROM sales s 
                          WHERE s.status = 'Completed' AND $dateCondition";
            $stmt = $pdo->prepare($salesQuery);
            $stmt->execute($params);
            $data['totalSales'] = (float)$stmt->fetchColumn();

            // Transaction Count (historical) - Only for admin
            $countQuery = "SELECT COUNT(*) 
                          FROM sales 
                          WHERE status = 'Completed' AND $dateCondition";
            $stmt = $pdo->prepare($countQuery);
            $stmt->execute($params);
            $data['transactionCount'] = (int)$stmt->fetchColumn();
        }

        // Total Boxes Sold (historical) - For both roles
        $boxesQuery = "SELECT COALESCE(SUM(si.quantity), 0) 
                      FROM sale_items si 
                      JOIN sales s ON si.sale_id = s.sale_id 
                      JOIN products p ON si.product_id = p.product_id
                      WHERE s.status = 'Completed' 
                      AND $dateCondition " . $searchCondition;
        $stmt = $pdo->prepare($boxesQuery);
        if ($searchCondition) {
            $stmt->execute(array_merge($params, $searchParams));
        } else {
            $stmt->execute($params);
        }
        $data['totalBoxesSold'] = (int)$stmt->fetchColumn();

        // Restock Alerts (items that need restocking based on current stock)
        $restockQuery = "SELECT COUNT(DISTINCT p.product_id)
                        FROM products p
                        JOIN inventory i ON p.product_id = i.product_id
                        WHERE p.status = 'Active'
                        AND i.stock < ? " . $searchCondition;
        $stmt = $pdo->prepare($restockQuery);
        if ($searchCondition) {
            $stmt->execute(array_merge([$lowStockThreshold], $searchParams));
        } else {
            $stmt->execute([$lowStockThreshold]);
        }
        $data['restock_alerts'] = (int)$stmt->fetchColumn();

        // Top Selling Product (for sales summary card)
        $topSellingQuery = "
            SELECT p.product_id, p.name, p.size, COALESCE(SUM(si.quantity * si.price), 0) as total
            FROM sale_items si 
            JOIN sales s ON si.sale_id = s.sale_id 
            JOIN products p ON si.product_id = p.product_id 
            WHERE s.status = 'Completed' " . 
            ($recentSalesRange === '7days' ? 
                "AND DATE(s.recorded_at) >= DATE_SUB(CURDATE(), INTERVAL 6 DAY) AND DATE(s.recorded_at) <= CURDATE()" : 
                "AND DATE(s.recorded_at) = CURDATE()") . 
            " " . $searchCondition . "
            GROUP BY p.product_id, p.name, p.size
            ORDER BY total DESC 
            LIMIT 1
        ";
        $stmt = $pdo->prepare($topSellingQuery);
        if ($searchCondition) {
            $stmt->execute($searchParams);
        } else {
            $stmt->execute();
        }
        $data['topSellingProduct'] = $stmt->fetch(PDO::FETCH_ASSOC);

        // Recent Sales logic - For both roles
        if ($recentSalesRange === '7days') {
            $recentSalesQuery = "
                SELECT p.product_id, p.name, p.size, COALESCE(SUM(si.quantity), 0) as items, COALESCE(SUM(si.quantity * si.price), 0) as total
                FROM sale_items si 
                JOIN sales s ON si.sale_id = s.sale_id 
                JOIN products p ON si.product_id = p.product_id 
                WHERE DATE(s.recorded_at) >= DATE_SUB(CURDATE(), INTERVAL 6 DAY) AND DATE(s.recorded_at) <= CURDATE() AND s.status = 'Completed' " . $searchCondition . "
                GROUP BY p.product_id, p.name, p.size
                ORDER BY s.recorded_at DESC 
                LIMIT 5
            ";
        } else {
            $recentSalesQuery = "
                SELECT p.product_id, p.name, p.size, COALESCE(SUM(si.quantity), 0) as items, COALESCE(SUM(si.quantity * si.price), 0) as total
                FROM sale_items si 
                JOIN sales s ON si.sale_id = s.sale_id 
                JOIN products p ON si.product_id = p.product_id 
                WHERE DATE(s.recorded_at) = CURDATE() AND s.status = 'Completed' " . $searchCondition . "
                GROUP BY p.product_id, p.name, p.size
                ORDER BY s.recorded_at DESC 
                LIMIT 5
            ";
        }
        $stmt = $pdo->prepare($recentSalesQuery);
        if ($searchCondition) {
            $stmt->execute($searchParams);
        } else {
            $stmt->execute();
        }
        $data['recentSales'] = $stmt->fetchAll(PDO::FETCH_ASSOC);

        // Inventory Status (lowest low, lowest mid, lowest high stock)
        $inventoryQuery = "
            SELECT p.name, p.size, i.stock 
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            WHERE p.status = 'Active'
            ORDER BY i.stock ASC
        ";
        $stmt = $pdo->prepare($inventoryQuery);
        $stmt->execute();
        $allInventory = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $low = null;
        $mid = null;
        $high = null;
        foreach ($allInventory as $item) {
            if ($low === null && $item['stock'] < $lowStockThreshold) {
                $low = $item;
                $low['statusClass'] = 'bg-danger-light text-danger';
                $low['statusText'] = 'Low Stock';
            } elseif ($mid === null && $item['stock'] >= $lowStockThreshold && $item['stock'] <= $highStockThreshold) {
                $mid = $item;
                $mid['statusClass'] = 'bg-warning-light text-warning';
                $mid['statusText'] = 'Medium Stock';
            } elseif ($high === null && $item['stock'] > $highStockThreshold) {
                $high = $item;
                $high['statusClass'] = 'bg-success-light text-success';
                $high['statusText'] = 'High Stock';
            }
            if ($low && $mid && $high) break;
        }
        $data['inventoryStatus'] = array_values(array_filter([$low, $mid, $high]));

    } catch (PDOException $e) {
        error_log("Database error in fetchDashboardData: " . $e->getMessage());
        throw new Exception('Database error: ' . $e->getMessage());
    }

    return $data;
}

// Handle AJAX requests
if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
    header('Content-Type: application/json');
    $response = ['success' => false, 'data' => []];
    $action = filter_input(INPUT_GET, 'action', FILTER_SANITIZE_STRING);

    if ($action === 'fetch_dashboard') {
        try {
            // Get filter and search parameters
            $filter = filter_input(INPUT_GET, 'filter', FILTER_SANITIZE_STRING) ?? 'Daily';
            $search = filter_input(INPUT_GET, 'search', FILTER_SANITIZE_STRING) ?? '';
            
            // If secretary, force filter to Daily
            if ($user['role'] === 'secretary') {
                $filter = 'Daily';
            }

            // Calculate days for filter
            $days = ($filter === 'Weekly') ? 6 : 0;

            // Fetch dashboard data
            $data = fetchDashboardData($pdo, $days, $search, $lowStockThreshold, $highStockThreshold);
            
            // Ensure role-appropriate data is returned
            if ($user['role'] !== 'admin') {
                // Remove admin-only data for secretary role
                unset($data['totalSales']);
                unset($data['transactionCount']);
            }

            $response['success'] = true;
            $response['data'] = $data;
            
            if ($data['warning']) {
                $response['warning'] = $data['warning'];
            }
        } catch (Exception $e) {
            $response['message'] = $e->getMessage();
            error_log("AJAX error: " . $e->getMessage());
        }
        echo json_encode($response);
        exit;
    }
}

// Get user's local date/time from GET param if present
if (isset($_GET['local_time'])) {
    $userLocalTime = $_GET['local_time'];
    // Optionally, use this for date-sensitive queries
    // Example: $currentDate = date('Y-m-d', strtotime($userLocalTime));
}

// Fetch data for initial page load
try {
    // For secretary, only today. For admin, get both today and 7 days.
    $recentSalesRange = ($filter === 'Weekly') ? '7days' : 'today';
    $dashboardData = fetchDashboardData($pdo, $days, $search, $lowStockThreshold, $highStockThreshold, $recentSalesRange);
    $recentSales = $dashboardData['recentSales'];
    $topSellingProduct = $dashboardData['topSellingProduct'];
    $recentSales7Days = [];
    $totalProducts = $dashboardData['totalProducts'];
    $totalSales = $dashboardData['totalSales'];
    $restock_alerts = $dashboardData['restock_alerts'];
    $transactionCount = $dashboardData['transactionCount'];
    $totalUnitsSold = $dashboardData['totalUnitsSold'];
    $totalBoxesSold = $dashboardData['totalBoxesSold'];
    $inventoryStatus = $dashboardData['inventoryStatus'];
    $warning = $dashboardData['warning'] ?? $warning;
} catch (Exception $e) {
    $error = $e->getMessage();
    $totalProducts = 0;
    $totalSales = 0.0;
    $restock_alerts = 0;
    $transactionCount = 0;
    $totalUnitsSold = 0;
    $totalBoxesSold = 0;
    $recentSales = [];
    $inventoryStatus = [];
    error_log("Initial load error: " . $e->getMessage());
}

// Include the template
include 'dashboard_template.php'; // recentSales and recentSales7Days are now available
?>