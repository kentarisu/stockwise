<?php
session_start();
include 'config.php';

// Set timezone
date_default_timezone_set('Asia/Manila');

// Enable error logging
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

// Check login
if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit;
}

// Delete voided sales older than 30 days
try {
    $pdo->exec("DELETE FROM sales WHERE status = 'Voided' AND voided_at IS NOT NULL AND voided_at < (NOW() - INTERVAL 30 DAY)");
} catch (Exception $e) {
    error_log('Failed to delete old voided sales: ' . $e->getMessage());
}

// Verify database connection
if (!$pdo) {
    error_log("Database connection failed.");
    $error = "Unable to connect to the database.";
    include 'sales_template.php';
    exit;
}

// Fetch user
$userId = $_SESSION['user_id'];
try {
    $stmt = $pdo->prepare("SELECT username, role, profile_picture FROM users WHERE user_id = ?");
    $stmt->execute([$userId]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$user) {
        $error = 'User not found.';
        include 'sales_template.php';
        exit;
    }
} catch (Exception $e) {
    error_log("User Fetch Error: " . $e->getMessage());
    $error = 'Error fetching user data.';
    include 'sales_template.php';
    exit;
}

// Initialize messages
$success = '';
$error = '';

// Initialize variables
$filter = filter_input(INPUT_GET, 'filter', FILTER_SANITIZE_STRING) ?? 'Daily';
$search = filter_input(INPUT_GET, 'search', FILTER_SANITIZE_STRING) ?? '';
$startDate = filter_input(INPUT_GET, 'start_date', FILTER_SANITIZE_STRING) ?? '';
$endDate = filter_input(INPUT_GET, 'end_date', FILTER_SANITIZE_STRING) ?? '';
$today = date('Y-m-d');

// Build date filter conditions
$conditions = [];
$params = [];

// Handle search input
if ($search) {
    // Check if search is a date
    $parsedDate = @strtotime($search);
    if ($parsedDate !== false) {
        $date = new DateTime($search, new DateTimeZone('Asia/Manila'));
        
        // Check if search is a month and year (e.g., "May 2025")
        if (preg_match('/^[A-Za-z]+\s+\d{4}$/', $search)) {
            $month = $date->format('m');
            $year = $date->format('Y');
            $conditions[] = 'YEAR(s.recorded_at) = ? AND MONTH(s.recorded_at) = ?';
            $params[] = $year;
            $params[] = $month;
        }
        // Check if search is a full date (e.g., "May 6, 2025" or "May 06, 2025")
        elseif (preg_match('/^[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}$/', $search) || 
                preg_match('/^[A-Za-z]+\s+\d{1,2}\s+\d{4}$/', $search)) {
            $conditions[] = 'DATE(s.recorded_at) = ?';
            $params[] = $date->format('Y-m-d');
        }
    } else {
        // Check if search is a sale ID
        if (is_numeric($search)) {
            $conditions[] = "s.sale_id = ?";
            $params[] = $search;
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

// Add filter conditions
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
    // No date condition for All Time
}

// Always filter by Completed status
$conditions[] = "s.status = 'Completed'";

// Build the WHERE clause
$whereClause = '';
if (!empty($conditions)) {
    $whereClause = 'WHERE ' . implode(' AND ', $conditions);
} else {
    $whereClause = "WHERE s.status = 'Completed'";
}

// Log the query details for debugging
error_log("Filter type: $filter");
error_log("Final WHERE clause: $whereClause");
error_log("Query parameters: " . json_encode($params));

// Calculate statistics
try {
    $stmt = $pdo->prepare("SELECT COUNT(DISTINCT s.sale_id) as total_sales FROM sales s $whereClause");
    $stmt->execute($params);
    $totalSales = $stmt->fetchColumn();

    $stmt = $pdo->prepare("SELECT SUM(si.quantity) as total_boxes FROM sale_items si JOIN sales s ON si.sale_id = s.sale_id $whereClause");
    $stmt->execute($params);
    $totalBoxes = $stmt->fetchColumn() ?: 0;

    $stmt = $pdo->prepare("SELECT SUM(s.total) as total_revenue FROM sales s $whereClause");
    $stmt->execute($params);
    $totalRevenue = $stmt->fetchColumn() ?: 0;

    // Check if required tables exist
    $requiredTables = ['sales', 'sale_items', 'products', 'inventory', 'users', 'receipt_prints'];
    foreach ($requiredTables as $table) {
        $stmt = $pdo->query("SHOW TABLES LIKE '$table'");
        if ($stmt->rowCount() === 0) {
            if ($table === 'receipt_prints') {
                // Create receipt_prints table
                $pdo->exec("CREATE TABLE IF NOT EXISTS receipt_prints (
                    print_id INT AUTO_INCREMENT PRIMARY KEY,
                    sale_id INT NOT NULL,
                    user_id INT NOT NULL,
                    print_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    INDEX idx_sale_user (sale_id, user_id)
                )");
                error_log("Created receipt_prints table");
            } else {
                $error = "Table '$table' does not exist in the database.";
                include 'sales_template.php';
                exit;
            }
        }
    }

    // Function to check if user can print receipt
    function canPrintReceipt($pdo, $saleId, $userId, $userRole) {
        if ($userRole === 'admin') {
            return true; // Admins have unlimited prints
        }
        
        try {
            // Count prints for this sale by this user
            $stmt = $pdo->prepare("SELECT COUNT(*) as print_count FROM receipt_prints WHERE sale_id = ? AND user_id = ?");
            $stmt->execute([$saleId, $userId]);
            $result = $stmt->fetch(PDO::FETCH_ASSOC);
            
            return $result['print_count'] < 3; // Non-admin users limited to 3 prints
        } catch (PDOException $e) {
            error_log("Error checking receipt prints: " . $e->getMessage());
            return false;
        }
    }

    // Function to record a receipt print
    function recordReceiptPrint($pdo, $saleId, $userId) {
        try {
            $stmt = $pdo->prepare("INSERT INTO receipt_prints (sale_id, user_id) VALUES (?, ?)");
            return $stmt->execute([$saleId, $userId]);
        } catch (PDOException $e) {
            error_log("Error recording receipt print: " . $e->getMessage());
            return false;
        }
    }

    // Handle AJAX requests
    if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
        header('Content-Type: application/json');
        header('Cache-Control: no-cache, no-store, must-revalidate');
        header('Pragma: no-cache');
        header('Expires: 0');
        $response = ['success' => false, 'data' => [], 'message' => '', 'refresh_voided' => false];

        try {
            $action = filter_input(INPUT_GET, 'action', FILTER_SANITIZE_STRING) ?? filter_input(INPUT_POST, 'action', FILTER_SANITIZE_STRING) ?? '';

            // Restrict sensitive actions to admin only
            $adminOnlyActions = ['void_sale', 'correct_quantity', 'complete_sale'];
            if (in_array($action, $adminOnlyActions) && $user['role'] !== 'admin') {
                $response['message'] = 'Unauthorized: Only admins can perform this action.';
                echo json_encode($response);
                exit;
            }

            if ($action === 'fetch_sales') {
                $queryParams = [];
                $conditions = ["s.status = 'Completed'"];
                $query = "
                    SELECT s.sale_id, s.recorded_at, s.voided_at, COUNT(si.sale_item_id) as product_count, SUM(si.quantity) as total_boxes, s.total, s.status
                    FROM sales s 
                    LEFT JOIN sale_items si ON s.sale_id = si.sale_id ";

                if ($search) {
                    $search = trim($search);
                    $isDateSearch = false;
                    $dateSearchCondition = '';

                    // Check if search is a year (e.g., "2025")
                    if (preg_match('/^\d{4}$/', $search)) {
                        $isDateSearch = true;
                        $year = intval($search);
                        $conditions[] = 'YEAR(s.recorded_at) = ?';
                        $queryParams[] = $year;
                    } else {
                        // Try parsing as other date formats
                        $parsedDate = @strtotime($search);
                        if ($parsedDate !== false) {
                            $date = new DateTime($search, new DateTimeZone('Asia/Manila'));

                            // Check if search is a month and year (e.g., "May 2025")
                            if (preg_match('/^[A-Za-z]+\s+\d{4}$/', $search)) {
                                $month = $date->format('m');
                                $year = $date->format('Y');
                                $conditions[] = 'YEAR(s.recorded_at) = ? AND MONTH(s.recorded_at) = ?';
                                $queryParams[] = $year;
                                $queryParams[] = $month;
                            }
                            // Check if search is a full date (e.g., "May 6, 2025" or "May 06, 2025")
                            elseif (preg_match('/^[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}$/', $search) || 
                                    preg_match('/^[A-Za-z]+\s+\d{1,2}\s+\d{4}$/', $search)) {
                                $dateStr = $date->format('Y-m-d');
                                $conditions[] = 'DATE(s.recorded_at) = ?';
                                $queryParams[] = $dateStr;
                            }
                            // Check if search is just a month (e.g., "May")
                            elseif (preg_match('/^[A-Za-z]+$/', $search)) {
                                $month = $date->format('m');
                                $conditions[] = 'MONTH(s.recorded_at) = ?';
                                $queryParams[] = $month;
                            }
                        } else {
                            // Check if search is a sale ID
                            if (is_numeric($search)) {
                                $conditions[] = "s.sale_id = ?";
                                $queryParams[] = $search;
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
                                $queryParams[] = $searchTerm;
                                $queryParams[] = $searchTerm;
                            }
                        }
                    }
                }

                if ($filter === 'Daily') {
                    $conditions[] = 'DATE(s.recorded_at) = ?';
                    $queryParams[] = $today;
                } elseif ($filter === 'Weekly') {
                    $conditions[] = 's.recorded_at >= ?';
                    $queryParams[] = date('Y-m-d H:i:s', strtotime('-7 days'));
                } elseif ($filter === 'Monthly') {
                    $conditions[] = 's.recorded_at >= ?';
                    $queryParams[] = date('Y-m-d H:i:s', strtotime('-1 month'));
                } elseif ($filter === 'Custom') {
                    if ($startDate && $endDate) {
                        $conditions[] = 'DATE(s.recorded_at) BETWEEN ? AND ?';
                        $queryParams[] = $startDate;
                        $queryParams[] = $endDate;
                    } else {
                        $conditions[] = 'DATE(s.recorded_at) = ?';
                        $queryParams[] = $today;
                    }
                }

                if (!empty($conditions)) {
                    $query .= " WHERE " . implode(' AND ', $conditions);
                }
                $query .= " GROUP BY s.sale_id ORDER BY s.recorded_at DESC";
                error_log("Sales Query: " . $query);
                error_log("Query Parameters: " . json_encode($queryParams));
                
                $stmt = $pdo->prepare($query);
                $stmt->execute($queryParams);
                $sales = $stmt->fetchAll(PDO::FETCH_ASSOC);

                foreach ($sales as &$sale) {
                    $sale['recorded_at'] = date('M d, Y h:i A', strtotime($sale['recorded_at']));
                    $stmtItems = $pdo->prepare("
                        SELECT p.product_id, p.name as product_name, si.quantity, p.price, (si.quantity * p.price) as subtotal, p.size
                        FROM sale_items si
                        JOIN products p ON si.product_id = p.product_id
                        WHERE si.sale_id = ?
                    ");
                    $stmtItems->execute([$sale['sale_id']]);
                    $sale['items'] = $stmtItems->fetchAll(PDO::FETCH_ASSOC);
                    $sale['products'] = implode(', ', array_map(function($item) {
                        return $item['product_name'];
                    }, $sale['items']));
                    $sale['items_json'] = json_encode($sale['items']);
                    // Add days-until-deletion for voided sales using voided_at from the query
                    if ($sale['status'] === 'Voided') {
                        $voidedAt = $sale['voided_at'];
                        if ($voidedAt) {
                            $voidedDate = new DateTime($voidedAt);
                            $now = new DateTime();
                            $interval = $now->diff($voidedDate);
                            $daysPassed = $interval->days;
                            $daysUntilDeletion = max(0, 30 - $daysPassed);
                            $sale['days_until_deletion'] = $daysUntilDeletion;
                        } else {
                            $sale['days_until_deletion'] = 30;
                        }
                    }
                }
                $response['success'] = true;
                $response['data'] = $sales;
            } elseif ($action === 'fetch_voided_sales') {
                $stmt = $pdo->prepare("DELETE FROM sales WHERE status = 'Voided' AND voided_at < NOW() - INTERVAL 30 DAY");
                $stmt->execute();

                $queryParams = [];
                $conditions = ["s.status = 'Voided'"];
                $query = "
                    SELECT s.sale_id, s.recorded_at, s.voided_at, COUNT(si.sale_item_id) as product_count, 
                           SUM(si.quantity) as total_boxes, s.total, s.status,
                           DATEDIFF(DATE_ADD(s.voided_at, INTERVAL 30 DAY), NOW()) as days_until_deletion
                    FROM sales s 
                    LEFT JOIN sale_items si ON s.sale_id = si.sale_id ";

                if ($search) {
                    $search = trim($search);
                    $isDateSearch = false;
                    $dateSearchCondition = '';

                    // Check if search is a year (e.g., "2025")
                    if (preg_match('/^\d{4}$/', $search)) {
                        $isDateSearch = true;
                        $year = intval($search);
                        $conditions[] = 'YEAR(s.recorded_at) = ?';
                        $queryParams[] = $year;
                    } else {
                        // Try parsing as other date formats
                        $parsedDate = @strtotime($search);
                        if ($parsedDate !== false) {
                            $date = new DateTime($search, new DateTimeZone('Asia/Manila'));

                            // Check if search is a month and year (e.g., "May 2025")
                            if (preg_match('/^[A-Za-z]+\s+\d{4}$/', $search)) {
                                $month = $date->format('m');
                                $year = $date->format('Y');
                                $conditions[] = 'YEAR(s.recorded_at) = ? AND MONTH(s.recorded_at) = ?';
                                $queryParams[] = $year;
                                $queryParams[] = $month;
                            }
                            // Check if search is a full date (e.g., "May 6, 2025" or "May 06, 2025")
                            elseif (preg_match('/^[A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}$/', $search) || 
                                    preg_match('/^[A-Za-z]+\s+\d{1,2}\s+\d{4}$/', $search)) {
                                $dateStr = $date->format('Y-m-d');
                                $conditions[] = 'DATE(s.recorded_at) = ?';
                                $queryParams[] = $dateStr;
                            }
                            // Check if search is just a month (e.g., "May")
                            elseif (preg_match('/^[A-Za-z]+$/', $search)) {
                                $month = $date->format('m');
                                $conditions[] = 'MONTH(s.recorded_at) = ?';
                                $queryParams[] = $month;
                            }
                        } else {
                            // Check if search is a sale ID
                            if (is_numeric($search)) {
                                $conditions[] = "s.sale_id = ?";
                                $queryParams[] = $search;
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
                                $queryParams[] = $searchTerm;
                                $queryParams[] = $searchTerm;
                            }
                        }
                    }
                }

                if (!empty($conditions)) {
                    $query .= " WHERE " . implode(' AND ', $conditions);
                }
                $query .= " GROUP BY s.sale_id ORDER BY s.recorded_at DESC";
                error_log("Voided Sales Query: " . $query);
                error_log("Voided Sales Query Parameters: " . json_encode($queryParams));

                $stmt = $pdo->prepare($query);
                $stmt->execute($queryParams);
                $voidedSales = $stmt->fetchAll(PDO::FETCH_ASSOC);

                foreach ($voidedSales as &$sale) {
                    $sale['recorded_at'] = date('M d, Y h:i A', strtotime($sale['recorded_at']));
                    $stmtItems = $pdo->prepare("
                        SELECT p.product_id, p.name as product_name, si.quantity, p.price, 
                               (si.quantity * p.price) as subtotal, p.size
                        FROM sale_items si
                        JOIN products p ON si.product_id = p.product_id
                        WHERE si.sale_id = ?
                    ");
                    $stmtItems->execute([$sale['sale_id']]);
                    $sale['items'] = $stmtItems->fetchAll(PDO::FETCH_ASSOC);
                    $sale['products'] = implode(', ', array_map(function($item) {
                        return $item['product_name'];
                    }, $sale['items']));
                    $sale['items_json'] = json_encode($sale['items']);
                    
                    // Ensure days_until_deletion is properly set
                    if ($sale['voided_at']) {
                        $voidedDate = new DateTime($sale['voided_at']);
                        $now = new DateTime();
                        $interval = $now->diff($voidedDate);
                        $daysPassed = $interval->days;
                        $sale['days_until_deletion'] = max(0, 30 - $daysPassed);
                    } else {
                        $sale['days_until_deletion'] = 30;
                    }
                }
                $response['success'] = true;
                $response['data'] = $voidedSales;
            } elseif ($action === 'void_sale') {
                if ($_SERVER['REQUEST_METHOD'] !== 'POST') throw new Exception('Invalid request method.');
                $saleId = filter_input(INPUT_POST, 'sale_id', FILTER_VALIDATE_INT);
                if (!$saleId) throw new Exception('Invalid sale ID.');

                $pdo->beginTransaction();
                try {
                    $stmt = $pdo->prepare("SELECT status, stock_restored FROM sales WHERE sale_id = ?");
                    $stmt->execute([$saleId]);
                    $sale = $stmt->fetch(PDO::FETCH_ASSOC);
                    if (!$sale) throw new Exception('Sale not found.');
                    if ($sale['status'] === 'Voided') throw new Exception('Sale is already voided.');

                    if ($sale['stock_restored'] == 0) {
                        $stmt = $pdo->prepare("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?");
                        $stmt->execute([$saleId]);
                        $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
                        foreach ($items as $item) {
                            $stmt = $pdo->prepare("
                                SELECT stock 
                                FROM inventory 
                                WHERE product_id = ?
                            ");
                            $stmt->execute([$item['product_id']]);
                            $currentStock = $stmt->fetchColumn() ?: 0;
                            $newStock = $currentStock + $item['quantity'];

                            $stmt = $pdo->prepare("
                                UPDATE inventory 
                                SET stock = ?, last_updated = NOW()
                                WHERE product_id = ?
                            ");
                            $stmt->execute([$newStock, $item['product_id']]);

                            // If no rows were updated, insert a new record
                            if ($stmt->rowCount() == 0) {
                                $stmt = $pdo->prepare("
                                    INSERT INTO inventory (product_id, stock, last_updated)
                                    VALUES (?, ?, NOW())
                                ");
                                $stmt->execute([$item['product_id'], $newStock]);
                            }
                        }
                    }

                    $stmt = $pdo->prepare("UPDATE sales SET status = 'Voided', voided_at = NOW(), stock_restored = 1 WHERE sale_id = ?");
                    $stmt->execute([$saleId]);

                    $pdo->commit();
                    $response['success'] = true;
                    $response['message'] = 'Sale marked as Voided successfully!';
                    $response['refresh_voided'] = true;
                } catch (Exception $e) {
                    $pdo->rollBack();
                    throw $e;
                }
            } elseif ($action === 'complete_sale') {
                if ($_SERVER['REQUEST_METHOD'] !== 'POST') throw new Exception('Invalid request method.');
                $saleId = filter_input(INPUT_POST, 'sale_id', FILTER_VALIDATE_INT);
                if (!$saleId) throw new Exception('Invalid sale ID.');

                $pdo->beginTransaction();
                try {
                    $stmt = $pdo->prepare("SELECT status, stock_restored FROM sales WHERE sale_id = ?");
                    $stmt->execute([$saleId]);
                    $sale = $stmt->fetch(PDO::FETCH_ASSOC);
                    if (!$sale) throw new Exception('Sale not found.');
                    if ($sale['status'] === 'Completed') throw new Exception('Sale is already completed.');

                    if ($sale['stock_restored'] == 1) {
                        $stmt = $pdo->prepare("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?");
                        $stmt->execute([$saleId]);
                        $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
                        foreach ($items as $item) {
                            $stmt = $pdo->prepare("
                                SELECT stock 
                                FROM inventory 
                                WHERE product_id = ?
                            ");
                            $stmt->execute([$item['product_id']]);
                            $currentStock = $stmt->fetchColumn();
                            if ($currentStock === false || $currentStock < $item['quantity']) {
                                throw new Exception("Insufficient stock for product ID {$item['product_id']}.");
                            }
                            $newStock = $currentStock - $item['quantity'];

                            $stmt = $pdo->prepare("
                                UPDATE inventory 
                                SET stock = ?, last_updated = NOW()
                                WHERE product_id = ?
                            ");
                            $stmt->execute([$newStock, $item['product_id']]);

                            // If no rows were updated, insert a new record
                            if ($stmt->rowCount() == 0) {
                                $stmt = $pdo->prepare("
                                    INSERT INTO inventory (product_id, stock, last_updated)
                                    VALUES (?, ?, NOW())
                                ");
                                $stmt->execute([$item['product_id'], $newStock]);
                            }
                        }
                    }

                    $stmt = $pdo->prepare("UPDATE sales SET status = 'Completed', voided_at = NULL, stock_restored = 0 WHERE sale_id = ?");
                    $stmt->execute([$saleId]);

                    $pdo->commit();
                    $response['success'] = true;
                    $response['message'] = 'Sale marked as Completed successfully!';
                    $response['refresh_voided'] = true;
                } catch (Exception $e) {
                    $pdo->rollBack();
                    throw $e;
                }
            } elseif ($action === 'correct_quantity') {
                if ($_SERVER['REQUEST_METHOD'] !== 'POST' || $user['role'] !== 'admin') throw new Exception('Only admins can correct quantities.');
                $saleId = filter_input(INPUT_POST, 'sale_id', FILTER_VALIDATE_INT);
                $productId = filter_input(INPUT_POST, 'product_id', FILTER_VALIDATE_INT);
                $newQuantity = filter_input(INPUT_POST, 'new_quantity', FILTER_VALIDATE_INT);
                if (!$saleId || !$productId || $newQuantity === false || $newQuantity < 0) throw new Exception('Invalid input.');

                $pdo->beginTransaction();
                try {
                    $stmt = $pdo->prepare("
                        SELECT si.quantity, p.price 
                        FROM sale_items si 
                        JOIN products p ON si.product_id = p.product_id 
                        WHERE si.sale_id = ? AND si.product_id = ?
                    ");
                    $stmt->execute([$saleId, $productId]);
                    $item = $stmt->fetch(PDO::FETCH_ASSOC);
                    if (!$item) throw new Exception('Sale item not found.');

                    $stmt = $pdo->prepare("
                        SELECT stock 
                        FROM inventory 
                        WHERE product_id = ?
                    ");
                    $stmt->execute([$productId]);
                    $currentStock = $stmt->fetchColumn();
                    if ($currentStock === false) throw new Exception("No stock record for product ID $productId.");

                    $stockDifference = $item['quantity'] - $newQuantity;
                    $newStock = $currentStock + $stockDifference;
                    if ($newStock < 0) throw new Exception('Correction would result in negative stock.');

                    $stmt = $pdo->prepare("
                        UPDATE inventory 
                        SET stock = ?, last_updated = NOW()
                        WHERE product_id = ?
                    ");
                    $stmt->execute([$newStock, $productId]);

                    // If no rows were updated, insert a new record
                    if ($stmt->rowCount() == 0) {
                        $stmt = $pdo->prepare("
                            INSERT INTO inventory (product_id, stock, last_updated)
                            VALUES (?, ?, NOW())
                        ");
                        $stmt->execute([$productId, $newStock]);
                    }

                    $stmt = $pdo->prepare("UPDATE sale_items SET quantity = ? WHERE sale_id = ? AND product_id = ?");
                    $stmt->execute([$newQuantity, $saleId, $productId]);

                    $stmt = $pdo->prepare("
                        SELECT SUM(si.quantity * p.price) as total 
                        FROM sale_items si 
                        JOIN products p ON si.product_id = p.product_id 
                        WHERE si.sale_id = ?
                    ");
                    $stmt->execute([$saleId]);
                    $newTotal = $stmt->fetchColumn();

                    $stmt = $pdo->prepare("UPDATE sales SET total = ? WHERE sale_id = ?");
                    $stmt->execute([$newTotal, $saleId]);

                    $pdo->commit();
                    $response['success'] = true;
                    $response['message'] = 'Quantity corrected successfully!';
                } catch (Exception $e) {
                    $pdo->rollBack();
                    throw $e;
                }
            } elseif ($action === 'get_sale_details') {
                $saleId = filter_input(INPUT_GET, 'sale_id', FILTER_VALIDATE_INT);
                if (!$saleId) {
                    $response['success'] = false;
                    $response['message'] = 'Invalid sale ID.';
                    echo json_encode($response);
                    exit;
                }
                // Fetch sale main details
                $stmt = $pdo->prepare("SELECT s.sale_id, s.or_number, s.recorded_at, s.status, s.total, s.amount_paid, s.change_given, u.username
                    FROM sales s
                    LEFT JOIN users u ON s.user_id = u.user_id
                    WHERE s.sale_id = ?");
                $stmt->execute([$saleId]);
                $sale = $stmt->fetch(PDO::FETCH_ASSOC);
                if (!$sale) {
                    $response['success'] = false;
                    $response['message'] = 'Sale not found.';
                    $response['data'] = null;
                    echo json_encode($response);
                    exit;
                }
                // Fetch sale items
                $stmtItems = $pdo->prepare("
                    SELECT p.product_id, p.name as product_name, si.quantity, p.price, (si.quantity * p.price) as subtotal, p.size
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.product_id
                    WHERE si.sale_id = ?
                ");
                $stmtItems->execute([$saleId]);
                $items = $stmtItems->fetchAll(PDO::FETCH_ASSOC);
                // Extract variant from product_name if present (e.g., 'Apple (Red)')
                foreach ($items as &$item) {
                    $item['variant'] = '';
                    if (preg_match('/^(.+?) \((.+)\)$/', $item['product_name'], $matches)) {
                        $item['product_name'] = $matches[1];
                        $item['variant'] = $matches[2];
                    }
                }
                $sale['items'] = $items;
                $response['success'] = true;
                $response['data'] = $sale;
                echo json_encode($response);
                exit;
            } elseif ($action === 'check_print_limit') {
                $saleId = filter_input(INPUT_GET, 'sale_id', FILTER_VALIDATE_INT);
                if (!$saleId) {
                    $response['message'] = 'Invalid sale ID.';
                    echo json_encode($response);
                    exit;
                }
                
                $canPrint = canPrintReceipt($pdo, $saleId, $_SESSION['user_id'], $user['role']);
                $response['success'] = true;
                $response['data'] = ['can_print' => $canPrint];
                echo json_encode($response);
                exit;
            } elseif ($action === 'record_print') {
                $saleId = filter_input(INPUT_GET, 'sale_id', FILTER_VALIDATE_INT);
                if (!$saleId) {
                    $response['message'] = 'Invalid sale ID.';
                    echo json_encode($response);
                    exit;
                }
                
                if (recordReceiptPrint($pdo, $saleId, $_SESSION['user_id'])) {
                    $response['success'] = true;
                    $response['message'] = 'Print recorded successfully.';
                } else {
                    $response['message'] = 'Failed to record print.';
                }
                echo json_encode($response);
                exit;
            } else {
                $response['message'] = 'Invalid action.';
            }
        } catch (Exception $e) {
            $response['message'] = $e->getMessage();
            error_log("AJAX Error: " . $e->getMessage());
        }
        echo json_encode($response);
        exit;
    }

    // Fetch products
    try {
        $stmt = $pdo->prepare("SELECT product_id, name, price, size FROM products ORDER BY name");
        $stmt->execute();
        $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        error_log("Products Fetch Error: " . $e->getMessage());
        $products = [];
    }

    // Initial sales fetch
    $queryParams = [];
    $conditions = ["s.status = 'Completed'"];
    if ($search) {
        $conditions[] = "EXISTS (SELECT 1 FROM sale_items si2 JOIN products p ON si2.product_id = p.product_id WHERE si2.sale_id = s.sale_id AND p.name LIKE ?)";
        $queryParams[] = "%$search%";
    }
    if ($filter === 'Daily') {
        $conditions[] = 'DATE(s.recorded_at) = ?';
        $queryParams[] = $today;
    } elseif ($filter === 'Weekly') {
        $conditions[] = 's.recorded_at >= ?';
        $queryParams[] = date('Y-m-d H:i:s', strtotime('-7 days'));
    } elseif ($filter === 'Monthly') {
        $conditions[] = 's.recorded_at >= ?';
        $queryParams[] = date('Y-m-d H:i:s', strtotime('-1 month'));
    } elseif ($filter === 'Custom') {
        if ($startDate && $endDate) {
            $conditions[] = 'DATE(s.recorded_at) BETWEEN ? AND ?';
            $queryParams[] = $startDate;
            $queryParams[] = $endDate;
        } else {
            $conditions[] = 'DATE(s.recorded_at) = ?';
            $queryParams[] = $today;
        }
    }
    $query = "
        SELECT s.sale_id, s.recorded_at, s.voided_at, COUNT(si.sale_item_id) as product_count, SUM(si.quantity) as total_boxes, s.total, s.status
        FROM sales s 
        LEFT JOIN sale_items si ON s.sale_id = si.sale_id ";
    if (!empty($conditions)) {
        $query .= " WHERE " . implode(' AND ', $conditions);
    }
    $query .= " GROUP BY s.sale_id ORDER BY s.recorded_at DESC";
    try {
        $stmt = $pdo->prepare($query);
        $stmt->execute($queryParams);
        $sales = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        error_log("Initial Sales Fetch Error: " . $e->getMessage());
        $sales = [];
    }

    foreach ($sales as &$sale) {
        $sale['recorded_at'] = date('M d, Y h:i A', strtotime($sale['recorded_at']));
        $stmtItems = $pdo->prepare("
            SELECT p.product_id, p.name as product_name, si.quantity, p.price, (si.quantity * p.price) as subtotal, p.size
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            WHERE si.sale_id = ?
        ");
        $stmtItems->execute([$sale['sale_id']]);
        $sale['items'] = $stmtItems->fetchAll(PDO::FETCH_ASSOC);
        $sale['products'] = implode(', ', array_map(function($item) {
            return $item['product_name'];
        }, $sale['items']));
        $sale['items_json'] = json_encode($sale['items']);
        // Add days-until-deletion for voided sales using voided_at from the query
        if ($sale['status'] === 'Voided') {
            $voidedAt = $sale['voided_at'];
            if ($voidedAt) {
                $voidedDate = new DateTime($voidedAt);
                $now = new DateTime();
                $interval = $now->diff($voidedDate);
                $daysPassed = $interval->days;
                $daysUntilDeletion = max(0, 30 - $daysPassed);
                $sale['days_until_deletion'] = $daysUntilDeletion;
            } else {
                $sale['days_until_deletion'] = 30;
            }
        }
    }

    // Initial voided sales fetch
    $voidedQuery = "
        SELECT s.sale_id, s.recorded_at, s.voided_at, COUNT(si.sale_item_id) as product_count, SUM(si.quantity) as total_boxes, s.total, s.status
        FROM sales s 
        LEFT JOIN sale_items si ON s.sale_id = si.sale_id 
        WHERE s.status = 'Voided'";
    $voidedParams = [];
    if ($search) {
        $voidedQuery .= " AND EXISTS (SELECT 1 FROM sale_items si2 JOIN products p ON si2.product_id = p.product_id WHERE si2.sale_id = s.sale_id AND p.name LIKE ?)";
        $voidedParams[] = "%$search%";
    }
    $voidedQuery .= " GROUP BY s.sale_id ORDER BY s.recorded_at DESC";
    try {
        $stmt = $pdo->prepare($voidedQuery);
        $stmt->execute($voidedParams);
        $voidedSales = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (Exception $e) {
        error_log("Initial Voided Sales Fetch Error: " . $e->getMessage());
        $voidedSales = [];
    }

    foreach ($voidedSales as &$sale) {
        $sale['recorded_at'] = date('M d, Y h:i A', strtotime($sale['recorded_at']));
        $stmtItems = $pdo->prepare("
            SELECT p.product_id, p.name as product_name, si.quantity, p.price, (si.quantity * p.price) as subtotal, p.size
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            WHERE si.sale_id = ?
        ");
        $stmtItems->execute([$sale['sale_id']]);
        $sale['items'] = $stmtItems->fetchAll(PDO::FETCH_ASSOC);
        $sale['products'] = implode(', ', array_map(function($item) {
            return $item['product_name'];
        }, $sale['items']));
        $sale['items_json'] = json_encode($sale['items']);
        // Calculate days until deletion using voided_at directly
        $voidedAt = $sale['voided_at'];
        if ($voidedAt) {
            $voidedDate = new DateTime($voidedAt);
            $now = new DateTime();
            $interval = $now->diff($voidedDate);
            $daysPassed = $interval->days;
            $daysUntilDeletion = max(0, 30 - $daysPassed);
            $sale['days_until_deletion'] = $daysUntilDeletion;
        } else {
            $sale['days_until_deletion'] = 30;
        }
    }

    // Check if there are any sales in the database
    $stmt = $pdo->query("SELECT COUNT(*) FROM sales");
    $salesCount = $stmt->fetchColumn();
    if ($salesCount == 0) {
        // Insert a test sale
        // $pdo->exec("INSERT INTO sales (sale_id, recorded_at, total, status) VALUES (1001, NOW(), 1234.56, 'Completed')");
        // $pdo->exec("INSERT INTO sale_items (sale_item_id, sale_id, product_id, quantity) VALUES (1, 1001, 1, 2)");
        $success = 'No sales yet';
        $sales = [];
        $voidedSales = [];
    }

} catch (Exception $e) {
    $error = 'An error occurred while fetching sales data.';
    error_log("Main Fetch Error: " . $e->getMessage());
}

include 'sales_template.php';
?>