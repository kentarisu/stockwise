<?php
session_start();
include 'config.php';

// Set the timezone for PHP
date_default_timezone_set('Asia/Manila');

// Enable error logging
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

// Check if user is logged in
if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}

// Check if user is not an admin
if ($_SESSION['role'] === 'user') {
    header("Location: dashboard.php");
    exit;
}

// Set the database session timezone to match PHP timezone
$pdo->exec("SET time_zone = '+08:00'"); // Asia/Manila is UTC+8

// Fetch user details
$userId = $_SESSION['user_id'];
try {
    $stmt = $pdo->prepare("SELECT username, role, profile_picture FROM users WHERE user_id = ?");
    $stmt->execute([$userId]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$user) {
        $error = 'User not found.';
        include 'reports_template.php';
        exit;
    }
    // Ensure profile_picture is set, even if null
    $user['profile_picture'] = $user['profile_picture'] ?: null;
} catch (PDOException $e) {
    error_log("User Fetch Error: " . $e->getMessage());
    $error = 'Error fetching user data.';
    include 'reports_template.php';
    exit;
}

// Initialize messages
$success = '';
$error = '';

// Handle query parameters
$filter = filter_input(INPUT_GET, 'filter', FILTER_SANITIZE_STRING) ?? 'Daily';
$search = filter_input(INPUT_GET, 'search', FILTER_SANITIZE_STRING) ?? '';
$startDate = filter_input(INPUT_GET, 'start_date', FILTER_SANITIZE_STRING) ?? '';
$endDate = filter_input(INPUT_GET, 'end_date', FILTER_SANITIZE_STRING) ?? '';

// Build date filter conditions
$today = date('Y-m-d');
$conditions = [];
$params = [];

// Handle search input (name, ID, or date)
if ($search) {
    $search = trim($search);
    $isDateSearch = false;
    $dateSearchCondition = '';

    // Check if search is a year (e.g., "2025")
    if (preg_match('/^\d{4}$/', $search)) {
        $isDateSearch = true;
        $year = intval($search);
        error_log("Year search detected: $year");
        
        // First check if there are any records for this year
        $yearCheckStmt = $pdo->prepare("
            SELECT COUNT(*) as count 
            FROM sales 
            WHERE YEAR(recorded_at) = ? AND status = 'Completed'
        ");
        $yearCheckStmt->execute([$year]);
        $yearCount = $yearCheckStmt->fetch(PDO::FETCH_ASSOC)['count'];
        error_log("Records found for year $year: $yearCount");
        
        if ($yearCount > 0) {
            $dateSearchCondition = 'YEAR(s.recorded_at) = ?';
            $params[] = $year;
            error_log("Applying year filter for $year");
        } else {
            // If no records found for this year, set a condition that will return no results
            $dateSearchCondition = '1 = 0';
            error_log("No records found for year $year, setting condition to return no results");
        }
    } else {
        // Try parsing as other date formats
        $parsedDate = @strtotime($search);
        if ($parsedDate !== false) {
            $isDateSearch = true;
            $date = new DateTime($search, new DateTimeZone('Asia/Manila'));

            // Check if search is a month and year (e.g., "May 2025")
            if (preg_match('/^[A-Za-z]+\s+\d{4}$/', $search)) {
                $month = $date->format('m');
                $year = $date->format('Y');
                // Check if there are any records for this month and year
                $monthYearCheckStmt = $pdo->prepare("
                    SELECT COUNT(*) as count 
                    FROM sales 
                    WHERE YEAR(recorded_at) = ? 
                    AND MONTH(recorded_at) = ? 
                    AND status = 'Completed'
                ");
                $monthYearCheckStmt->execute([$year, $month]);
                $monthYearCount = $monthYearCheckStmt->fetch(PDO::FETCH_ASSOC)['count'];
                
                if ($monthYearCount > 0) {
                    $dateSearchCondition = 'YEAR(s.recorded_at) = ? AND MONTH(s.recorded_at) = ?';
                    $params[] = $year;
                    $params[] = $month;
                } else {
                    $dateSearchCondition = '1 = 0';
                }
            }
            // Check if search is a full date (e.g., "May 6, 2025" or "May 06, 2025")
            elseif (preg_match('/^[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}$/', $search) || 
                    preg_match('/^[A-Za-z]+\s+\d{1,2}\s+\d{4}$/', $search)) {
                $dateStr = $date->format('Y-m-d');
                // Check if there are any records for this date
                $dateCheckStmt = $pdo->prepare("
                    SELECT COUNT(*) as count 
                    FROM sales 
                    WHERE DATE(recorded_at) = ? AND status = 'Completed'
                ");
                $dateCheckStmt->execute([$dateStr]);
                $dateCount = $dateCheckStmt->fetch(PDO::FETCH_ASSOC)['count'];
                
                if ($dateCount > 0) {
                    $dateSearchCondition = 'DATE(s.recorded_at) = ?';
                    $params[] = $dateStr;
                } else {
                    $dateSearchCondition = '1 = 0';
                }
            }
            // Check if search is just a month (e.g., "May")
            elseif (preg_match('/^[A-Za-z]+$/', $search)) {
                $month = $date->format('m');
                // Check if there are any records for this month
                $monthCheckStmt = $pdo->prepare("
                    SELECT COUNT(*) as count 
                    FROM sales 
                    WHERE MONTH(recorded_at) = ? AND status = 'Completed'
                ");
                $monthCheckStmt->execute([$month]);
                $monthCount = $monthCheckStmt->fetch(PDO::FETCH_ASSOC)['count'];
                
                if ($monthCount > 0) {
                    $dateSearchCondition = 'MONTH(s.recorded_at) = ?';
                    $params[] = $month;
                } else {
                    $dateSearchCondition = '1 = 0';
                }
            }
        }
    }

    if ($isDateSearch) {
        $conditions[] = $dateSearchCondition;
        error_log("Date search condition added: $dateSearchCondition");
    } else {
        // Check if search is a sale ID
        if (is_numeric($search)) {
            // Check if the sale ID exists
            $saleCheckStmt = $pdo->prepare("
                SELECT COUNT(*) as count 
                FROM sales 
                WHERE sale_id = ? AND status = 'Completed'
            ");
            $saleCheckStmt->execute([$search]);
            $saleCount = $saleCheckStmt->fetch(PDO::FETCH_ASSOC)['count'];
            
            if ($saleCount > 0) {
                $conditions[] = "s.sale_id = ?";
                $params[] = $search;
            } else {
                $conditions[] = '1 = 0';
            }
        } else {
            // Search by fruit name or size (case-insensitive)
            $conditions[] = "EXISTS (
                SELECT 1 FROM sale_items si2 
                JOIN products p ON si2.product_id = p.product_id 
                WHERE si2.sale_id = s.sale_id 
                AND (
                    LOWER(p.name) LIKE ? 
                    OR LOWER(p.size) LIKE ?
                )
            )";
            $searchTerm = "%" . strtolower($search) . "%";
            $params[] = $searchTerm;
            $params[] = $searchTerm;
        }
    }
}

// Build date filter conditions
if ($filter === 'Daily') {
    $conditions[] = 'DATE(s.recorded_at) = ?';
    $params[] = $today;
} elseif ($filter === 'Weekly') {
    $conditions[] = 's.recorded_at >= ?';
    $params[] = date('Y-m-d H:i:s', strtotime('-7 days'));
} elseif ($filter === 'Monthly') {
    $conditions[] = 's.recorded_at >= ?';
    $params[] = date('Y-m-d H:i:s', strtotime('-1 month'));
} elseif ($filter === 'Custom') {
    if ($startDate && $endDate && strtotime($startDate) && strtotime($endDate)) {
        $conditions[] = 'DATE(s.recorded_at) BETWEEN ? AND ?';
        $params[] = $startDate;
        $params[] = $endDate;
    } else {
        $error = 'Invalid custom date range.';
        $filter = 'Daily'; // Fallback to Daily if invalid
        $conditions[] = 'DATE(s.recorded_at) = ?';
        $params[] = $today;
    }
} elseif ($filter === 'All Time') {
    // No date condition for All Time, but still keep the status filter
    $conditions[] = "s.status = 'Completed'";
}

// Modify the whereClause construction to be more explicit
$whereClause = '';
if (!empty($conditions)) {
    $whereClause = 'WHERE ' . implode(' AND ', $conditions);
} else {
    $whereClause = "WHERE s.status = 'Completed'";
}
error_log("Final WHERE clause: $whereClause");
error_log("Filter type: $filter");
error_log("Query parameters: " . json_encode($params));

// Handle AJAX requests
if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
    header('Content-Type: application/json');
    $response = ['success' => false, 'data' => []];
    $action = filter_input(INPUT_GET, 'action', FILTER_SANITIZE_STRING);

    if ($action === 'fetch_reports') {
        try {
            // Sales Summary with debug logging
            $salesSummaryQuery = "
                SELECT 
                    COALESCE(SUM(si.quantity * si.price), 0) as total_revenue, 
                    COUNT(DISTINCT s.sale_id) as transaction_count,
                    COALESCE(SUM(si.quantity), 0) as total_items_sold,
                    MIN(s.recorded_at) as earliest_date,
                    MAX(s.recorded_at) as latest_date
                FROM sales s 
                JOIN sale_items si ON s.sale_id = si.sale_id 
                $whereClause
            ";
            error_log("Sales Summary Query: $salesSummaryQuery");
            error_log("Query Parameters: " . json_encode($params));
            
            $stmt = $pdo->prepare($salesSummaryQuery);
            $stmt->execute($params);
            $salesSummary = $stmt->fetch(PDO::FETCH_ASSOC);
            error_log("Sales Summary Results: " . json_encode($salesSummary));
            
            $salesSummary['avg_order_value'] = $salesSummary['transaction_count'] > 0 ? 
                $salesSummary['total_revenue'] / $salesSummary['transaction_count'] : 0;

            // Top Fruits
            $stmt = $pdo->prepare("
                SELECT 
                    p.product_id,
                    p.name, 
                    p.size, 
                    SUM(si.quantity) as boxes_sold, 
                    COALESCE(SUM(si.quantity * p.price), 0) as revenue 
                FROM sale_items si 
                JOIN products p ON si.product_id = p.product_id 
                JOIN sales s ON si.sale_id = s.sale_id 
                $whereClause 
                GROUP BY p.product_id, p.name, p.size 
                ORDER BY boxes_sold DESC 
                LIMIT 5
            ");
            $stmt->execute($params);
            $topFruits = $stmt->fetchAll(PDO::FETCH_ASSOC);
            error_log("Top Fruits Query: " . json_encode($topFruits));

            // Fruit Summary
            $stmt = $pdo->prepare("
                SELECT 
                    p.product_id,
                    p.name, 
                    p.size, 
                    SUM(si.quantity) as boxes_sold, 
                    p.price as price_per_box,
                    COALESCE(SUM(si.quantity * p.price), 0) as revenue 
                FROM sale_items si 
                JOIN products p ON si.product_id = p.product_id 
                JOIN sales s ON si.sale_id = s.sale_id 
                $whereClause 
                GROUP BY p.product_id, p.name, p.size, p.price 
                ORDER BY revenue DESC
            ");
            $stmt->execute($params);
            $fruitSummary = $stmt->fetchAll(PDO::FETCH_ASSOC);
            error_log("Fruit Summary Query: " . json_encode($fruitSummary));

            // Low Stock Fruits
            $stmt = $pdo->prepare("
                SELECT 
                    p.product_id,
                    p.name,
                    p.size,
                    latest.stock,
                    COALESCE(p.price, 0.00) as price 
                FROM products p 
                LEFT JOIN (
                    SELECT product_id, stock 
                    FROM inventory i1 
                    WHERE i1.last_updated = (
                        SELECT MAX(i2.last_updated) 
                        FROM inventory i2 
                        WHERE i2.product_id = i1.product_id
                    )
                ) latest ON p.product_id = latest.product_id 
                WHERE latest.stock <= 10 AND p.status = 'Active' 
                ORDER BY latest.stock ASC
            ");
            $stmt->execute();
            $lowStockFruits = $stmt->fetchAll(PDO::FETCH_ASSOC);

            // Process variants in low stock fruits
            foreach ($lowStockFruits as &$fruit) {
                $fruit['variant'] = '';
                if (preg_match('/^(.*?)\s*\((.*?)\)$/', $fruit['name'], $matches)) {
                    $fruit['name'] = trim($matches[1]);
                    $fruit['variant'] = trim($matches[2]);
                }
            }
            error_log("Low Stock Query: " . json_encode($lowStockFruits));

            // Recent Transactions
            $transactionsQuery = "
                SELECT 
                    s.sale_id, 
                    s.recorded_at, 
                    s.total, 
                    s.status, 
                    COUNT(DISTINCT si.sale_item_id) as fruit_count, 
                    SUM(si.quantity) as total_boxes,
                    GROUP_CONCAT(DISTINCT p.name SEPARATOR ', ') as fruits,
                    GROUP_CONCAT(DISTINCT p.size SEPARATOR ', ') as sizes
                FROM sales s 
                LEFT JOIN sale_items si ON s.sale_id = si.sale_id 
                LEFT JOIN products p ON si.product_id = p.product_id 
                $whereClause 
                GROUP BY s.sale_id 
                ORDER BY s.recorded_at DESC";

            // Only apply LIMIT for non-All Time filters
            if ($filter !== 'All Time') {
                $transactionsQuery .= " LIMIT 10";
            }

            try {
                $stmt = $pdo->prepare($transactionsQuery);
                $stmt->execute($params);
                $transactions = $stmt->fetchAll(PDO::FETCH_ASSOC);
                error_log("Transactions Query: " . $transactionsQuery);
                error_log("Transactions found: " . count($transactions));
            } catch (PDOException $e) {
                $error = 'Error fetching transactions: ' . $e->getMessage();
                error_log("Transactions Query Error: " . $e->getMessage());
                $transactions = [];
            }

            // Fetch Daily and Weekly Revenue Breakdown
            try {
                // Daily Revenue Breakdown
                $dailyRevenueQuery = "
                    SELECT 
                        p.product_id,
                        p.name,
                        p.size,
                        DATE(s.recorded_at) as sale_date,
                        SUM(si.quantity) as boxes_sold,
                        COALESCE(SUM(si.quantity * si.price), 0) as daily_revenue
                    FROM sales s 
                    JOIN sale_items si ON s.sale_id = si.sale_id 
                    JOIN products p ON si.product_id = p.product_id 
                    WHERE s.status = 'Completed' 
                    AND s.recorded_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    GROUP BY p.product_id, p.name, p.size, DATE(s.recorded_at)
                    ORDER BY sale_date DESC, daily_revenue DESC
                ";
                $stmt = $pdo->prepare($dailyRevenueQuery);
                $stmt->execute();
                $dailyRevenue = $stmt->fetchAll(PDO::FETCH_ASSOC);

                // Weekly Revenue Breakdown
                $weeklyRevenueQuery = "
                    SELECT 
                        p.product_id,
                        p.name,
                        p.size,
                        YEARWEEK(s.recorded_at) as year_week,
                        MIN(DATE(s.recorded_at)) as week_start,
                        MAX(DATE(s.recorded_at)) as week_end,
                        SUM(si.quantity) as boxes_sold,
                        COALESCE(SUM(si.quantity * si.price), 0) as weekly_revenue
                    FROM sales s 
                    JOIN sale_items si ON s.sale_id = si.sale_id 
                    JOIN products p ON si.product_id = p.product_id 
                    WHERE s.status = 'Completed' 
                    AND s.recorded_at >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
                    GROUP BY p.product_id, p.name, p.size, YEARWEEK(s.recorded_at)
                    ORDER BY year_week DESC, weekly_revenue DESC
                ";
                $stmt = $pdo->prepare($weeklyRevenueQuery);
                $stmt->execute();
                $weeklyRevenue = $stmt->fetchAll(PDO::FETCH_ASSOC);

                // Process the data for easier display
                $dailyRevenueByDate = [];
                foreach ($dailyRevenue as $record) {
                    $date = $record['sale_date'];
                    if (!isset($dailyRevenueByDate[$date])) {
                        $dailyRevenueByDate[$date] = [];
                    }
                    $dailyRevenueByDate[$date][] = $record;
                }

                $weeklyRevenueByWeek = [];
                foreach ($weeklyRevenue as $record) {
                    $weekKey = $record['year_week'];
                    if (!isset($weeklyRevenueByWeek[$weekKey])) {
                        $weeklyRevenueByWeek[$weekKey] = [
                            'week_start' => $record['week_start'],
                            'week_end' => $record['week_end'],
                            'items' => []
                        ];
                    }
                    $weeklyRevenueByWeek[$weekKey]['items'][] = $record;
                }

                error_log("Daily Revenue Data: " . json_encode($dailyRevenueByDate));
                error_log("Weekly Revenue Data: " . json_encode($weeklyRevenueByWeek));
            } catch (PDOException $e) {
                $error = 'Error fetching revenue breakdown: ' . $e->getMessage();
                error_log("Revenue Breakdown Error: " . $e->getMessage());
                $dailyRevenueByDate = [];
                $weeklyRevenueByWeek = [];
            }

            $response['success'] = true;
            $response['data'] = [
                'sales_summary' => $salesSummary,
                'top_fruits' => $topFruits,
                'fruit_summary' => $fruitSummary,
                'low_stock' => $lowStockFruits,
                'transactions' => $transactions,
                'daily_revenue' => $dailyRevenueByDate,
                'weekly_revenue' => $weeklyRevenueByWeek
            ];
        } catch (PDOException $e) {
            $response['message'] = 'Error fetching reports: ' . $e->getMessage();
            error_log("Fetch Reports Error: " . $e->getMessage());
        }
    } elseif ($action === 'fetch_transaction_details') {
        $saleId = filter_input(INPUT_GET, 'sale_id', FILTER_VALIDATE_INT);
        if (!$saleId) {
            $response['message'] = 'Invalid sale ID.';
            echo json_encode($response);
            exit;
        }
        try {
            $stmt = $pdo->prepare("
                SELECT s.sale_id, s.recorded_at, s.total, s.status, s.or_number, u.username,
                       si.product_id, p.name as fruit_name, p.size, si.quantity, p.price
                FROM sales s
                LEFT JOIN sale_items si ON s.sale_id = si.sale_id
                LEFT JOIN products p ON si.product_id = p.product_id
                LEFT JOIN users u ON s.user_id = u.user_id
                WHERE s.sale_id = ?
            ");
            $stmt->execute([$saleId]);
            $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
            if (empty($items)) {
                $response['message'] = 'Transaction not found.';
                echo json_encode($response);
                exit;
            }
            $transaction = [
                'sale_id' => $items[0]['sale_id'],
                'date' => date('M d, Y, h:i A', strtotime($items[0]['recorded_at'])),
                'total' => $items[0]['total'],
                'status' => $items[0]['status'],
                'or_number' => $items[0]['or_number'],
                'username' => $items[0]['username'],
                'items' => []
            ];
            foreach ($items as $item) {
                if ($item['product_id']) {
                    $transaction['items'][] = [
                        'product_id' => $item['product_id'],
                        'fruit_name' => $item['fruit_name'],
                        'size' => $item['size'],
                        'quantity' => $item['quantity'],
                        'price' => $item['price'],
                        'subtotal' => $item['quantity'] * $item['price']
                    ];
                }
            }
            $response['success'] = true;
            $response['data'] = $transaction;
            error_log("Transaction Details for sale_id $saleId: " . json_encode($transaction));
        } catch (PDOException $e) {
            $response['message'] = 'Error fetching transaction details: ' . $e->getMessage();
            error_log("Transaction Details Error for sale_id $saleId: " . $e->getMessage());
        }
    }
    echo json_encode($response);
    exit;
}

// Check if required tables exist
$requiredTables = ['sales', 'sale_items', 'products', 'inventory', 'users'];
foreach ($requiredTables as $table) {
    $stmt = $pdo->query("SHOW TABLES LIKE '$table'");
    if ($stmt->rowCount() === 0) {
        $error = "Table '$table' does not exist in the database.";
        include 'reports_template.php';
        exit;
    }
}

// Fetch Sales Summary
try {
    $stmt = $pdo->prepare("
        SELECT 
            COALESCE(SUM(si.quantity * si.price), 0) as total_revenue, 
            COUNT(DISTINCT s.sale_id) as transaction_count,
            COALESCE(SUM(si.quantity), 0) as total_items_sold,
            MIN(s.recorded_at) as earliest_date,
            MAX(s.recorded_at) as latest_date
        FROM sales s 
        JOIN sale_items si ON s.sale_id = si.sale_id 
        $whereClause
    ");
    $stmt->execute($params);
    $salesSummary = $stmt->fetch(PDO::FETCH_ASSOC);
    $totalRevenue = $salesSummary['total_revenue'];
    $transactionCount = $salesSummary['transaction_count'];
    $totalItemsSold = $salesSummary['total_items_sold'];
    $avgOrderValue = $transactionCount > 0 ? $totalRevenue / $transactionCount : 0;
    error_log("Initial Sales Summary: " . json_encode($salesSummary));
} catch (PDOException $e) {
    $error = 'Error fetching sales summary: ' . $e->getMessage();
    error_log("Initial Sales Summary Error: " . $e->getMessage());
}

// Fetch Top Fruits
try {
    $stmt = $pdo->prepare("
        SELECT 
            p.product_id,
            p.name, 
            p.size, 
            SUM(si.quantity) as boxes_sold, 
            COALESCE(SUM(si.quantity * p.price), 0) as revenue 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.product_id 
        JOIN sales s ON si.sale_id = s.sale_id 
        $whereClause 
        GROUP BY p.product_id, p.name, p.size 
        ORDER BY boxes_sold DESC 
        LIMIT 5
    ");
    $stmt->execute($params);
    $topFruits = $stmt->fetchAll(PDO::FETCH_ASSOC);
    error_log("Initial Top Fruits: " . json_encode($topFruits));
} catch (PDOException $e) {
    $error = 'Error fetching top fruits: ' . $e->getMessage();
    error_log("Initial Top Fruits Error: " . $e->getMessage());
}

// Fetch Fruit Summary
try {
    $stmt = $pdo->prepare("
        SELECT 
            p.product_id,
            p.name, 
            p.size, 
            SUM(si.quantity) as boxes_sold, 
            p.price as price_per_box,
            COALESCE(SUM(si.quantity * p.price), 0) as revenue 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.product_id 
        JOIN sales s ON si.sale_id = s.sale_id 
        $whereClause 
        GROUP BY p.product_id, p.name, p.size, p.price 
        ORDER BY revenue DESC
    ");
    $stmt->execute($params);
    $fruitSummary = $stmt->fetchAll(PDO::FETCH_ASSOC);
    error_log("Initial Fruit Summary: " . json_encode($fruitSummary));
} catch (PDOException $e) {
    $error = 'Error fetching fruit summary: ' . $e->getMessage();
    error_log("Initial Fruit Summary Error: " . $e->getMessage());
}

// Fetch Low Stock Fruits
try {
    $stmt = $pdo->prepare("
        SELECT 
            p.product_id,
            p.name,
            p.size,
            latest.stock,
            COALESCE(p.price, 0.00) as price 
        FROM products p 
        LEFT JOIN (
            SELECT product_id, stock 
            FROM inventory i1 
            WHERE i1.last_updated = (
                SELECT MAX(i2.last_updated) 
                FROM inventory i2 
                WHERE i2.product_id = i1.product_id
            )
        ) latest ON p.product_id = latest.product_id 
        WHERE latest.stock <= 10 AND p.status = 'Active' 
        ORDER BY latest.stock ASC
    ");
    $stmt->execute();
    $lowStockFruits = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Process variants in low stock fruits
    foreach ($lowStockFruits as &$fruit) {
        $fruit['variant'] = '';
        if (preg_match('/^(.*?)\s*\((.*?)\)$/', $fruit['name'], $matches)) {
            $fruit['name'] = trim($matches[1]);
            $fruit['variant'] = trim($matches[2]);
        }
    }
    error_log("Low Stock Query: " . json_encode($lowStockFruits));
} catch (PDOException $e) {
    $error = 'Error fetching low stock fruits: ' . $e->getMessage();
    error_log("Initial Low Stock Error: " . $e->getMessage());
}

// Fetch Recent Transactions (initial load)
try {
    $stmt = $pdo->prepare("
        SELECT s.sale_id, s.recorded_at, s.total, s.status, 
               COUNT(si.sale_item_id) as fruit_count, 
               SUM(si.quantity) as total_boxes, 
               GROUP_CONCAT(p.name SEPARATOR ', ') as fruits 
        FROM sales s 
        LEFT JOIN sale_items si ON s.sale_id = si.sale_id 
        LEFT JOIN products p ON si.product_id = p.product_id 
        $whereClause 
        GROUP BY s.sale_id 
        ORDER BY s.recorded_at DESC 
        " . ($filter !== 'All Time' ? 'LIMIT 10' : '')
    );
    $stmt->execute($params);
    $transactions = $stmt->fetchAll(PDO::FETCH_ASSOC);
    error_log("Initial Transactions: " . json_encode($transactions));
} catch (PDOException $e) {
    $error = 'Error fetching transactions: ' . $e->getMessage();
    error_log("Initial Transactions Error: " . $e->getMessage());
}

// Handle CSV export (admin only)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $user['role'] === 'admin') {
    $action = filter_input(INPUT_POST, 'action', FILTER_SANITIZE_STRING);
    if ($action === 'export') {
        $reportType = filter_input(INPUT_POST, 'report_type', FILTER_SANITIZE_STRING);
        header('Content-Type: text/csv');
        header('Content-Disposition: attachment; filename="' . $reportType . '_report_' . date('Ymd') . '.csv"');
        $output = fopen('php://output', 'w');
        
        if ($reportType === 'sales_summary') {
            fputcsv($output, ['Report', 'Total Revenue', 'Transactions', 'Total Boxes Sold', 'Avg. Order Value']);
            fputcsv($output, ['Sales Summary', number_format($totalRevenue, 2), $transactionCount, $totalItemsSold, number_format($avgOrderValue, 2)]);
        } elseif ($reportType === 'top_fruits') {
            fputcsv($output, ['Fruit Name', 'Size', 'Boxes Sold', 'Revenue']);
            foreach ($topFruits as $fruit) {
                fputcsv($output, [$fruit['name'], $fruit['size'] ?: 'N/A', $fruit['boxes_sold'], number_format($fruit['revenue'], 2)]);
            }
        } elseif ($reportType === 'fruit_summary') {
            fputcsv($output, ['Fruit Name', 'Size', 'Boxes Sold', 'Price per Box', 'Revenue']);
            foreach ($fruitSummary as $fruit) {
                fputcsv($output, [$fruit['name'], $fruit['size'] ?: 'N/A', $fruit['boxes_sold'], number_format($fruit['price_per_box'], 2), number_format($fruit['revenue'], 2)]);
            }
        } elseif ($reportType === 'low_stock') {
            fputcsv($output, ['Fruit Name', 'Size', 'Stock (boxes)', 'Price']);
            foreach ($lowStockFruits as $fruit) {
                fputcsv($output, [$fruit['name'], $fruit['size'] ?: 'N/A', $fruit['stock'], number_format($fruit['price'], 2)]);
            }
        } elseif ($reportType === 'transactions') {
            fputcsv($output, ['Sale ID', 'Date', 'Fruits', 'Fruit Types', 'Boxes', 'Total', 'Status']);
            foreach ($transactions as $transaction) {
                fputcsv($output, [
                    $transaction['sale_id'],
                    date('M d, Y, h:i A', strtotime($transaction['recorded_at'])),
                    $transaction['fruits'] ?: 'N/A',
                    $transaction['fruit_count'],
                    $transaction['total_boxes'],
                    number_format($transaction['total'], 2),
                    $transaction['status']
                ]);
            }
        }
        fclose($output);
        exit;
    }
}

// Include the template
include 'reports_template.php';
?>