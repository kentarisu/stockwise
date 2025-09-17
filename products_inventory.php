<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
session_start();
ini_set('display_errors', 0); // Suppress errors in output to ensure clean JSON
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

// Set timezone
date_default_timezone_set('Asia/Manila');

require_once 'config.php';

// --- GET: Return all active products with price (for JS live total) ---
if (isset($_GET['action']) && $_GET['action'] === 'get_active_products') {
    $stmt = $pdo->prepare("SELECT p.product_id, p.name, p.price, p.size, i.stock FROM products p LEFT JOIN inventory i ON p.product_id = i.product_id WHERE p.status = 'Active'");
    $stmt->execute();
    $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
    header('Content-Type: application/json');
    echo json_encode(['success' => true, 'data' => $products]);
    exit;
}

// --- GET: Return all products for AJAX table/grid ---
if (isset($_GET['action']) && $_GET['action'] === 'get_products') {
    $search = $_GET['search'] ?? '';
    $filter = $_GET['filter'] ?? 'All Products';
    $sortColumn = $_GET['sort_column'] ?? 'name';
    $sortOrder = strtoupper($_GET['sort_order'] ?? 'ASC');

    $allowedSortColumns = ['name', 'stock', 'date_added'];
    if (!in_array($sortColumn, $allowedSortColumns)) {
        $sortColumn = 'name';
    }
    if (!in_array($sortOrder, ['ASC', 'DESC'])) {
        $sortOrder = 'ASC';
    }
    $allowedFilters = ['All Products', 'Active', 'Discontinued'];
    if (!in_array($filter, $allowedFilters)) {
        $filter = 'All Products';
    }

    $query = "
        SELECT 
            p.product_id, p.name, p.status, p.date_added, p.image,
            p.price, p.cost, p.size,
            COALESCE(i.stock, 0) AS stock
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
    ";
    $params = [];
    $conditions = [];
    if ($search) {
        if (is_numeric($search)) {
            $conditions[] = "(p.product_id = ? OR LOWER(p.name) LIKE LOWER(?) OR LOWER(p.size) LIKE LOWER(?))";
            $params[] = $search;
            $params[] = "%$search%";
            $params[] = "%$search%";
        } else {
            $conditions[] = "(LOWER(p.name) LIKE LOWER(?) OR LOWER(p.size) LIKE LOWER(?))";
            $params[] = "%$search%";
            $params[] = "%$search%";
        }
    }
    if ($filter !== 'All Products') {
        $conditions[] = "p.status = ?";
        $params[] = $filter;
    }
    if (!empty($conditions)) {
        $query .= " WHERE " . implode(" AND ", $conditions);
    }
    switch ($sortColumn) {
        case 'stock':
            $query .= " ORDER BY COALESCE(i.stock, 0) $sortOrder";
            break;
        case 'date_added':
            $query .= " ORDER BY p.date_added $sortOrder";
            break;
        default:
            $query .= " ORDER BY p.name $sortOrder";
    }
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    $products = $stmt->fetchAll(PDO::FETCH_ASSOC);

    header('Content-Type: application/json');
    echo json_encode(['success' => true, 'data' => $products]);
    exit;
}

// --- GET: Return a single product for editing ---
if (isset($_GET['action']) && $_GET['action'] === 'get_product' && isset($_GET['id'])) {
    $productId = intval($_GET['id']);
    $stmt = $pdo->prepare("SELECT p.product_id, p.name, p.status, p.date_added, p.image, p.price, p.cost, p.size, COALESCE(i.stock, 0) AS stock FROM products p LEFT JOIN inventory i ON p.product_id = i.product_id WHERE p.product_id = ?");
    $stmt->execute([$productId]);
    $product = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($product) {
        header('Content-Type: application/json');
        echo json_encode(['success' => true, 'data' => $product]);
    } else {
        header('Content-Type: application/json');
        echo json_encode(['success' => false, 'message' => 'Product not found']);
    }
    exit;
}

// --- GET: Return stock details for a product ---
if (isset($_GET['action']) && $_GET['action'] === 'get_stock_details' && isset($_GET['product_id'])) {
    $productId = intval($_GET['product_id']);
    try {
        $stmt = $pdo->prepare("SELECT batch_id, date_added, quantity, remaining_quantity FROM stock_additions WHERE product_id = ? ORDER BY date_added ASC");
        $stmt->execute([$productId]);
        $batches = $stmt->fetchAll(PDO::FETCH_ASSOC);

        // Format for frontend
        $data = [];
        foreach ($batches as $batch) {
            $data[] = [
                'batch_id' => $batch['batch_id'],
                'date_added' => $batch['date_added'],
                'quantity' => $batch['quantity'],
                'remaining' => $batch['remaining_quantity']
            ];
        }
        header('Content-Type: application/json');
        echo json_encode(['success' => true, 'data' => $data]);
    } catch (Exception $e) {
        header('Content-Type: application/json');
        echo json_encode(['success' => false, 'message' => $e->getMessage()]);
    }
    exit;
}

// --- GET: Return sale details for receipt ---
if (isset($_GET['action']) && $_GET['action'] === 'get_sale_details' && isset($_GET['sale_id'])) {
    try {
        $sale_id = intval($_GET['sale_id']);
        $stmt = $pdo->prepare("
            SELECT s.sale_id, s.or_number, s.recorded_at, s.total, s.status, u.username
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE s.sale_id = ?
        ");
        $stmt->execute([$sale_id]);
        $sale = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$sale) {
            throw new Exception('Sale not found');
        }

        // Get sale items
        $stmt = $pdo->prepare("
            SELECT 
                si.product_id, 
                p.name,
                CASE 
                    WHEN p.name LIKE '%(%)' 
                    THEN SUBSTRING_INDEX(SUBSTRING_INDEX(p.name, '(', -1), ')', 1)
                    ELSE ''
                END as variant,
                p.size, 
                si.quantity, 
                si.price
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            WHERE si.sale_id = ?
        ");
        $stmt->execute([$sale_id]);
        $items = $stmt->fetchAll(PDO::FETCH_ASSOC);

        header('Content-Type: application/json');
        echo json_encode([
            'success' => true,
            'sale' => $sale,
            'items' => $items
        ]);
    } catch (Exception $e) {
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'message' => $e->getMessage()
        ]);
    }
    exit;
}

// Check if user is logged in
if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

// Initialize variables
$products = [];
$search = $_GET['search'] ?? '';
$filter = $_GET['filter'] ?? 'All Products';
$tab = $_GET['tab'] ?? 'inventory';
$success = '';
$error = '';
$user = [];
$totalProducts = 0;
$activeProducts = 0;
$totalStock = 0;

// Verify database connection
if (!$pdo) {
    error_log("Database connection failed.");
    $error = "Unable to connect to the database.";
    if (!isset($_SERVER['HTTP_X_REQUESTED_WITH'])) {
        require 'products_inventory_template.php';
    } else {
        header('Content-Type: application/json');
        echo json_encode(['success' => false, 'message' => 'Database connection failed']);
    }
    exit;
}

// Fetch user details
try {
    $stmt = $pdo->prepare("SELECT username, profile_picture, role FROM users WHERE user_id = ?");
    $stmt->execute([$_SESSION['user_id']]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$user) {
        header('Location: logout.php');
        exit;
    }
} catch (Exception $e) {
    error_log("Error fetching user: " . $e->getMessage());
    $error = "Failed to load user data.";
}

// Fetch inventory data
try {
    $query = "
        SELECT 
            p.product_id, p.name, p.status, p.date_added, p.image,
            p.price, p.cost, p.size,
            COALESCE(i.stock, 0) AS stock
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
    ";
    $params = [];
    if ($search || $filter !== 'All Products') {
        $query .= " WHERE 1=1";
        if ($search) {
            if (is_numeric($search)) {
                $query .= " AND (p.product_id = ? OR LOWER(p.name) LIKE LOWER(?) OR LOWER(p.size) LIKE LOWER(?))";
                $params[] = $search;
                $params[] = "%$search%";
                $params[] = "%$search%";
            } else {
                $query .= " AND (LOWER(p.name) LIKE LOWER(?) OR LOWER(p.size) LIKE LOWER(?))";
                $params[] = "%$search%";
                $params[] = "%$search%";
            }
        }
        if ($filter === 'Active' || $filter === 'Discontinued') {
            $query .= " AND p.status = ?";
            $params[] = $filter;
        }
    }
    $query .= " ORDER BY p.name";
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    $products = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $totalProducts = count($products);
    $activeProducts = count(array_filter($products, fn($p) => $p['status'] === 'Active'));
    $totalStock = array_sum(array_column($products, 'stock') ?: [0]);

    // Calculate restock alerts
    $lowStockThreshold = 10;
    $restockAlerts = count(array_filter($products, function($p) use ($lowStockThreshold) {
        return $p['status'] === 'Active' && $p['stock'] < $lowStockThreshold;
    }));
} catch (Exception $e) {
    error_log("Error fetching products: " . $e->getMessage());
    $error = "Failed to load inventory data.";
}

// Before rendering the template, add debug output
error_log('PRODUCTS COUNT: ' . count($products));
foreach ($products as $p) {
    error_log('PRODUCT: ' . $p['product_id'] . ' - ' . $p['name']);
}

// --- Handle POST actions FIRST ---
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $pdo->beginTransaction();
        if ($_POST['action'] === 'update_status') {
            $productId = intval($_POST['product_id'] ?? 0);
            $status = $_POST['status'] ?? '';
            if (!$productId || !in_array($status, ['Active', 'Discontinued'])) {
                throw new Exception('Invalid product or status.');
            }
            $stmt = $pdo->prepare("UPDATE products SET status = ? WHERE product_id = ?");
            $stmt->execute([$status, $productId]);
            $pdo->commit();
            header('Content-Type: application/json');
            echo json_encode(['success' => true, 'message' => 'Status updated successfully.']);
            exit;
        }
        if ($_POST['action'] === 'add') {
            $name = ucwords(strtolower(trim($_POST['productName'])));
            $variant = trim($_POST['variant']) ? ucwords(strtolower(trim($_POST['variant']))) : '';
            $size = ucwords(strtolower(trim($_POST['size'])));
            $cost = floatval($_POST['cost']);
            $price = floatval($_POST['price']);
            $status = $_POST['status'];
            $stock = intval($_POST['initialStock']);
            $dateAdded = $_POST['dateAdded'];

            if (preg_match('/^(.*?)(?:\s*\([^)]*\))?$/', $name, $matches)) {
                $name = trim($matches[1]);
            }
            $fullName = $variant ? "$name ($variant)" : $name;

            if (empty($fullName) || $cost < 0 || $price < 0 || $stock < 0 || !in_array($status, ['Active', 'Discontinued'])) {
                throw new Exception("Invalid input data. Required fields: name, cost, price, stock, status.");
            }

            $imagePath = null;
            if (!empty($_FILES['productImage']['name'])) {
                $allowed = ['image/jpeg', 'image/png'];
                if (!in_array($_FILES['productImage']['type'], $allowed) || $_FILES['productImage']['size'] > 2 * 1024 * 1024) {
                    throw new Exception("Invalid image. Use JPG/PNG, max 2MB.");
                }
                $ext = pathinfo($_FILES['productImage']['name'], PATHINFO_EXTENSION);
                $imagePath = "Uploads/product_" . time() . "_" . rand(1000, 9999) . ".$ext";
                if (!is_dir('Uploads')) {
                    mkdir('Uploads', 0755, true);
                }
                if (!move_uploaded_file($_FILES['productImage']['tmp_name'], $imagePath)) {
                    throw new Exception("Failed to upload image.");
                }
            }

            $stmt = $pdo->prepare("SELECT COUNT(*) FROM products WHERE name = ? AND size = ?");
            $stmt->execute([$fullName, $size]);
            if ($stmt->fetchColumn() > 0) {
                throw new Exception("A fruit with this name and size already exists.");
            }

            $stmt = $pdo->prepare("
                INSERT INTO products (name, status, date_added, image, price, cost, size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ");
            $stmt->execute([$fullName, $status, $dateAdded, $imagePath, $price, $cost, $size]);
            $productId = $pdo->lastInsertId();

            if ($stock > 0) {
                $batchId = generateBatchId($pdo, $productId, $name, $variant);
                $stmt = $pdo->prepare("
                    INSERT INTO stock_additions (product_id, batch_id, quantity, date_added, remaining_quantity, created_at)
                    VALUES (?, ?, ?, ?, ?, NOW())
                ");
                $stmt->execute([$productId, $batchId, $stock, $dateAdded, $stock]);
                error_log("Added stock addition for product_id: $productId, batch_id: $batchId, quantity: $stock");

                $stmt = $pdo->prepare("
                    INSERT INTO inventory (product_id, stock, last_updated)
                    VALUES (?, ?, NOW())
                ");
                $stmt->execute([$productId, $stock]);
            }
            $success = "Fruit added successfully.";
        } elseif ($_POST['action'] === 'edit') {
            $productId = $_POST['productId'] ?? null;
            $name = ucwords(strtolower(trim($_POST['productName'])));
            $variant = trim($_POST['variant']) ? ucwords(strtolower(trim($_POST['variant']))) : '';
            $size = ucwords(strtolower(trim($_POST['size'])));
            $cost = floatval($_POST['cost']);
            $price = floatval($_POST['price']);
            $status = $_POST['status'];
            $stock = intval($_POST['initialStock']);
            $dateAdded = $_POST['dateAdded'];

            if (preg_match('/^(.*?)(?:\s*\([^)]*\))?$/', $name, $matches)) {
                $name = trim($matches[1]);
            }
            $fullName = $variant ? "$name ($variant)" : $name;

            if (empty($fullName) || $cost < 0 || $price < 0 || $stock < 0 || !in_array($status, ['Active', 'Discontinued'])) {
                throw new Exception("Invalid input data. Required fields: name, cost, price, stock, status.");
            }

            $imagePath = null;
            if (!empty($_FILES['productImage']['name'])) {
                $allowed = ['image/jpeg', 'image/png'];
                if (!in_array($_FILES['productImage']['type'], $allowed) || $_FILES['productImage']['size'] > 2 * 1024 * 1024) {
                    throw new Exception("Invalid image. Use JPG/PNG, max 2MB.");
                }
                $ext = pathinfo($_FILES['productImage']['name'], PATHINFO_EXTENSION);
                $imagePath = "Uploads/product_" . time() . "_" . rand(1000, 9999) . ".$ext";
                if (!is_dir('Uploads')) {
                    mkdir('Uploads', 0755, true);
                }
                if (!move_uploaded_file($_FILES['productImage']['tmp_name'], $imagePath)) {
                    throw new Exception("Failed to upload image.");
                }
            }

            $stmt = $pdo->prepare("SELECT COUNT(*) FROM products WHERE name = ? AND size = ? AND product_id != ?");
            $stmt->execute([$fullName, $size, $productId]);
            if ($stmt->fetchColumn() > 0) {
                throw new Exception("A fruit with this name and size already exists.");
            }

            $stmt = $pdo->prepare("
                UPDATE products 
                SET name = ?, status = ?, date_added = ?, price = ?, cost = ?, size = ?
                " . ($imagePath ? ", image = ?" : "") . "
                WHERE product_id = ?
            ");
            $params = [$fullName, $status, $dateAdded, $price, $cost, $size];
            if ($imagePath) $params[] = $imagePath;
            $params[] = $productId;
            $stmt->execute($params);

            $stmt = $pdo->prepare("SELECT stock FROM inventory WHERE product_id = ?");
            $stmt->execute([$productId]);
            $current_stock = $stmt->fetchColumn() ?: 0;

            $difference = $stock - $current_stock;
            if ($difference > 0) {
                $batchId = generateBatchId($pdo, $productId, $name, $variant);
                $stmt = $pdo->prepare("
                    INSERT INTO stock_additions (product_id, batch_id, quantity, date_added, remaining_quantity, created_at)
                    VALUES (?, ?, ?, ?, ?, NOW())
                ");
                // Include the actual delivery/date_added so FIFO history and ordering are correct
                $stmt->execute([$productId, $batchId, $difference, $dateAdded, $difference]);
                error_log("Added stock addition for product_id: $productId, batch_id: $batchId, quantity: $difference");
            } elseif ($difference < 0) {
                $to_remove = abs($difference);
                $stmt = $pdo->prepare("
                    SELECT batch_id, remaining_quantity
                    FROM stock_additions
                    WHERE product_id = ? AND remaining_quantity > 0
                    ORDER BY date_added ASC
                ");
                $stmt->execute([$productId]);
                $batches = $stmt->fetchAll(PDO::FETCH_ASSOC);
                $remaining_to_remove = $to_remove;

                foreach ($batches as $batch) {
                    if ($remaining_to_remove <= 0) break;
                    $remove_from_batch = min($remaining_to_remove, $batch['remaining_quantity']);
                    $stmt = $pdo->prepare("
                        UPDATE stock_additions
                        SET remaining_quantity = remaining_quantity - ?
                        WHERE batch_id = ?
                    ");
                    $stmt->execute([$remove_from_batch, $batch['batch_id']]);
                    $remaining_to_remove -= $remove_from_batch;
                    error_log("Deducted $remove_from_batch from batch {$batch['batch_id']} for product_id: $productId");
                }

                if ($remaining_to_remove > 0) {
                    $stmt = $pdo->prepare("
                        UPDATE stock_additions
                        SET remaining_quantity = 0
                        WHERE product_id = ?
                    ");
                    $stmt->execute([$productId]);
                    error_log("Set remaining_quantity to 0 for product_id: $productId due to insufficient batch stock");
                }
            } elseif ($stock == 0) {
                $stmt = $pdo->prepare("
                    UPDATE stock_additions
                    SET remaining_quantity = 0
                    WHERE product_id = ?
                ");
                $stmt->execute([$productId]);
                error_log("Cleared all remaining_quantity for product_id: $productId");
            }

            $stmt = $pdo->prepare("SELECT inventory_id FROM inventory WHERE product_id = ?");
            $stmt->execute([$productId]);
            $inventoryId = $stmt->fetchColumn();

            if ($inventoryId) {
                $stmt = $pdo->prepare("
                    UPDATE inventory 
                    SET stock = ?, last_updated = NOW()
                    WHERE inventory_id = ?
                ");
                $stmt->execute([$stock, $inventoryId]);
            } else {
                $stmt = $pdo->prepare("
                    INSERT INTO inventory (product_id, stock, last_updated) 
                    VALUES (?, ?, NOW())
                ");
                $stmt->execute([$productId, $stock]);
            }
            $success = "Fruit updated successfully.";
        } elseif ($_POST['action'] === 'buy') {
            if (!isset($_POST['items']) || !isset($_POST['purchase_date'])) {
                throw new Exception('Missing required fields');
            }

            $items = json_decode($_POST['items'], true);
            $purchase_date = $_POST['purchase_date'];

            if (!is_array($items) || empty($items)) {
                throw new Exception('Invalid items data');
            }

            // Generate a unique OR number: OR-YYYY-XXXX (incremental per year)
            $year = date('Y');
            $stmt = $pdo->prepare("SELECT COUNT(*) FROM sales WHERE YEAR(recorded_at) = ?");
            $stmt->execute([$year]);
            $or_seq = $stmt->fetchColumn() + 1;
            $or_number = sprintf('OR-%s-%04d', $year, $or_seq);

            $amount_paid = isset($_POST['amount_paid']) ? floatval($_POST['amount_paid']) : 0;
            $change = $amount_paid; // Will be updated after total is calculated

            $stmt = $pdo->prepare("
                INSERT INTO sales (or_number, recorded_at, total, amount_paid, change_given, status, user_id)
                VALUES (?, NOW(), 0, ?, ?, 'Completed', ?)
            ");
            $stmt->execute([$or_number, $amount_paid, 0, $_SESSION['user_id']]);
            $sale_id = $pdo->lastInsertId();

            $total_amount = 0;

            foreach ($items as $item) {
                if (!isset($item['product_id']) || !isset($item['quantity'])) {
                    throw new Exception('Invalid item data');
                }

                $product_id = $item['product_id'];
                $quantity = (int)$item['quantity'];

                if ($quantity <= 0) {
                    throw new Exception('Invalid quantity');
                }

                $stmt = $pdo->prepare("SELECT * FROM products WHERE product_id = ? AND status = 'Active'");
                $stmt->execute([$product_id]);
                $product = $stmt->fetch(PDO::FETCH_ASSOC);

                if (!$product) {
                    throw new Exception('Product not found or inactive');
                }

                $stmt = $pdo->prepare("SELECT stock FROM inventory WHERE product_id = ?");
                $stmt->execute([$product_id]);
                $current_stock = $stmt->fetchColumn() ?: 0;

                if ($quantity > $current_stock) {
                    throw new Exception("Insufficient stock for product ID $product_id. Available: $current_stock, Requested: $quantity");
                }

                deductStockFIFO($pdo, $product_id, $quantity);

                $stmt = $pdo->prepare("
                    INSERT INTO sale_items (sale_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ");
                $stmt->execute([$sale_id, $product_id, $quantity, $product['price']]);

                $total_amount += $product['price'] * $quantity;
            }

            $change = $amount_paid - $total_amount;
            $stmt = $pdo->prepare("UPDATE sales SET total = ?, amount_paid = ?, change_given = ? WHERE sale_id = ?");
            $stmt->execute([$total_amount, $amount_paid, $change, $sale_id]);

            // After $sale_id is set and before sending the JSON response for a successful sale
            // Fetch the username
            $stmt = $pdo->prepare("SELECT username FROM users WHERE user_id = ?");
            $stmt->execute([$_SESSION['user_id']]);
            $username = $stmt->fetchColumn();

            $pdo->commit();

            header('Content-Type: application/json');
            echo json_encode([
                'success' => true,
                'message' => 'Sale recorded successfully',
                'or_number' => $or_number,
                'sale_id' => $sale_id,
                'total' => $total_amount,
                'amount_paid' => $amount_paid,
                'change' => $change,
                'username' => $username
            ]);
            exit;
        } elseif ($_POST['action'] === 'add_stock') {
            $dateAdded = $_POST['date_added'];
            if (isset($_POST['items'])) {
                $items = json_decode($_POST['items'], true);
            } else {
                // Fallback for single add stock modal
                $items = [[
                    'product_id' => $_POST['product_id'] ?? null,
                    'quantity' => $_POST['quantity'] ?? null
                ]];
            }
            if (empty($items) || empty($dateAdded)) {
                throw new Exception("Invalid input for adding stock.");
            }
            foreach ($items as $item) {
                $productId = $item['product_id'] ?? null;
                $quantity = intval($item['quantity'] ?? 0);
                if (empty($productId) || $quantity <= 0) {
                    throw new Exception("Invalid product or quantity for adding stock.");
                }
                $stmt = $pdo->prepare("SELECT name, size FROM products WHERE product_id = ?");
                $stmt->execute([$productId]);
                $product = $stmt->fetch(PDO::FETCH_ASSOC);
                if (!$product) {
                    throw new Exception("Product not found (ID: $productId).");
                }
                $name = $product['name'];
                $size = $product['size'] ?? '';
                $variant = '';
                if (preg_match('/^(.*?)\s*\((.*?)\)$/', $name, $matches)) {
                    $name = trim($matches[1]);
                    $variant = trim($matches[2]);
                }
                // Serial: [Fruit Acronym][Variant Acronym][Size Acronym][MMDDYYYY]
                $fruitAcr = getAcronym($name);
                $variantAcr = getAcronym($variant);
                $sizeAcr = getAcronym($size);
                $dateObj = new DateTime($dateAdded);
                $mm = $dateObj->format('m');
                $dd = $dateObj->format('d');
                $yyyy = $dateObj->format('Y');
                $serial = $fruitAcr . $variantAcr . $sizeAcr . $mm . $dd . $yyyy;
                // Merge logic: check if batch with same serial (batch_id), product, and date exists
                $stmt = $pdo->prepare("SELECT addition_id, quantity, remaining_quantity FROM stock_additions WHERE product_id = ? AND batch_id = ? AND date_added = ?");
                $stmt->execute([$productId, $serial, $dateObj->format('Y-m-d')]);
                $existing = $stmt->fetch(PDO::FETCH_ASSOC);
                if ($existing) {
                    // Update existing batch
                    $newQty = $existing['quantity'] + $quantity;
                    $newRem = $existing['remaining_quantity'] + $quantity;
                    $stmt = $pdo->prepare("UPDATE stock_additions SET quantity = ?, remaining_quantity = ? WHERE addition_id = ?");
                    $stmt->execute([$newQty, $newRem, $existing['addition_id']]);
                } else {
                    // Insert new batch
                    $stmt = $pdo->prepare("
                        INSERT INTO stock_additions (product_id, batch_id, quantity, date_added, remaining_quantity, created_at)
                        VALUES (?, ?, ?, ?, ?, NOW())
                    ");
                    $stmt->execute([$productId, $serial, $quantity, $dateObj->format('Y-m-d'), $quantity]);
                }
                // Update inventory
                $stmt = $pdo->prepare("SELECT inventory_id FROM inventory WHERE product_id = ?");
                $stmt->execute([$productId]);
                $inventoryId = $stmt->fetchColumn();
                if ($inventoryId) {
                    $stmt = $pdo->prepare("
                        UPDATE inventory
                        SET stock = stock + ?,
                            last_updated = NOW()
                        WHERE inventory_id = ?
                    ");
                    $stmt->execute([$quantity, $inventoryId]);
                } else {
                    $stmt = $pdo->prepare("
                        INSERT INTO inventory (product_id, stock, last_updated)
                        VALUES (?, ?, NOW())
                    ");
                    $stmt->execute([$productId, $quantity]);
                }
            }
            $success = "Stock added successfully.";
        }
        $pdo->commit();
        if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
            header('Content-Type: application/json');
            echo json_encode(['success' => empty($error), 'message' => $success ?: $error]);
            exit;
        }
    } catch (Exception $e) {
        $pdo->rollBack();
        error_log("Form submission error: " . $e->getMessage());
        $error = $e->getMessage();
        if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
            header('Content-Type: application/json');
            echo json_encode(['success' => false, 'message' => $e->getMessage()]);
            exit;
        }
    }
}
// --- THEN handle generic AJAX requests ---
// ... existing code ...

// Function to generate batch ID
function generateBatchId($pdo, $productId, $productName, $variant) {
    // Get product details
    $stmt = $pdo->prepare("SELECT size, date_added FROM products WHERE product_id = ?");
    $stmt->execute([$productId]);
    $product = $stmt->fetch(PDO::FETCH_ASSOC);
    
    // Get fruit name without variant
    $baseName = $productName;
    if ($variant) {
        $baseName = trim(preg_replace('/\s*\(.*?\)$/', '', $productName));
    }
    
    // Get acronyms
    $fruitAcr = getAcronym($baseName);
    $variantAcr = $variant ? getAcronym($variant) : '';
    $sizeAcr = $product['size'] ? getAcronym($product['size']) : '';
    
    // Build the batch ID
    $batchId = $fruitAcr;
    if ($variantAcr) $batchId .= $variantAcr;
    if ($sizeAcr) $batchId .= $sizeAcr;
    
    // Get date components
    $dateObj = new DateTime($product['date_added']);
    $mm = $dateObj->format('m');
    $dd = $dateObj->format('d');
    $yyyy = $dateObj->format('Y');
    
    // Combine to form batch ID
    $batchId .= $mm . $dd . $yyyy;
    return $batchId;
}

function deductStockFIFO($pdo, $product_id, $quantity) {
    $stmt = $pdo->prepare("
        SELECT batch_id, remaining_quantity
        FROM stock_additions
        WHERE product_id = ? AND remaining_quantity > 0
        ORDER BY date_added ASC
    ");
    $stmt->execute([$product_id]);
    $batches = $stmt->fetchAll(PDO::FETCH_ASSOC);
    $remaining_to_deduct = $quantity;

    foreach ($batches as $batch) {
        if ($remaining_to_deduct <= 0) break;
        $deduct_amount = min($remaining_to_deduct, $batch['remaining_quantity']);
        $stmt2 = $pdo->prepare("
            UPDATE stock_additions
            SET remaining_quantity = remaining_quantity - ?
            WHERE batch_id = ?
        ");
        $stmt2->execute([$deduct_amount, $batch['batch_id']]);
        $remaining_to_deduct -= $deduct_amount;
    }

    if ($remaining_to_deduct > 0) {
        throw new Exception("Insufficient stock in batches for product ID $product_id.");
    }

    // Update inventory table
    $stmt = $pdo->prepare("SELECT SUM(remaining_quantity) FROM stock_additions WHERE product_id = ?");
    $stmt->execute([$product_id]);
    $newTotal = $stmt->fetchColumn() ?: 0;
    $stmt = $pdo->prepare("UPDATE inventory SET stock = ?, last_updated = NOW() WHERE product_id = ?");
    $stmt->execute([$newTotal, $product_id]);
}

// Helper to get acronym from a string (e.g., 'Green Apple' => 'GA')
function getAcronym($str) {
    if (!$str) return '';
    $words = preg_split('/\s+/', $str);
    $acronym = '';
    foreach ($words as $w) {
        $acronym .= strtoupper($w[0]);
    }
    return $acronym;
}

// Function to generate OR number
function generateORNumber($pdo) {
    $year = date('Y');
    $stmt = $pdo->prepare("SELECT MAX(CAST(SUBSTRING(or_number, 4) AS UNSIGNED)) as max_num FROM sales WHERE or_number LIKE ?");
    $stmt->execute(["OR$year%"]);
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    $nextNum = ($result['max_num'] ?? 0) + 1;
    return "OR$year" . str_pad($nextNum, 6, '0', STR_PAD_LEFT);
}

// Function to check if user can print receipt (limit only for non-admins)
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
    $response = ['success' => false, 'data' => []];
    $action = filter_input(INPUT_GET, 'action', FILTER_SANITIZE_STRING);

    if ($action === 'check_print_limit') {
        $saleId = filter_input(INPUT_GET, 'sale_id', FILTER_VALIDATE_INT);
        if (!$saleId) {
            $response['success'] = false;
            $response['message'] = 'Invalid sale ID.';
            echo json_encode($response);
            exit;
        }
        $canPrint = canPrintReceipt($pdo, $saleId, $_SESSION['user_id'], $user['role']);
        $response['success'] = true;
        $response['data'] = ['can_print' => $canPrint];
        echo json_encode($response);
        exit;
    }

    if ($action === 'record_print') {
        if (!isset($_GET['sale_id'])) {
            echo json_encode(['success' => false, 'message' => 'Sale ID is required']);
            exit;
        }
        
        $saleId = (int)$_GET['sale_id'];
        $userId = $_SESSION['user_id'];
        
        error_log("Attempting to record print - Sale ID: $saleId, User ID: $userId");
        
        try {
            $stmt = $pdo->prepare("INSERT INTO receipt_prints (sale_id, user_id) VALUES (?, ?)");
            if ($stmt->execute([$saleId, $userId])) {
                error_log("Successfully recorded print - Sale ID: $saleId, User ID: $userId");
                echo json_encode(['success' => true]);
            } else {
                error_log("Failed to record print - PDO Error: " . implode(", ", $stmt->errorInfo()));
                echo json_encode(['success' => false, 'message' => 'Failed to record print']);
            }
        } catch (Exception $e) {
            error_log("Error recording receipt print: " . $e->getMessage());
            echo json_encode(['success' => false, 'message' => 'Error recording print']);
        }
        exit;
    }

    // Check if product exists
    if (isset($_GET['action']) && $_GET['action'] === 'check_product_exists') {
        try {
            $input = json_decode(file_get_contents('php://input'), true);
            if (!$input) {
                throw new Exception('Invalid input data');
            }

            $name = ucwords(strtolower(trim($input['name'])));
            $variant = trim($input['variant']) ? ucwords(strtolower(trim($input['variant']))) : '';
            $size = ucwords(strtolower(trim($input['size'])));
            $productId = $input['product_id'] ?? null;

            if (empty($name) || empty($size)) {
                throw new Exception('Name and size are required');
            }

            $fullName = $variant ? "$name ($variant)" : $name;

            // Check if product exists
            $query = "SELECT COUNT(*) FROM products WHERE name = ? AND size = ?";
            $params = [$fullName, $size];
            
            if ($productId) {
                $query .= " AND product_id != ?";
                $params[] = $productId;
            }

            $stmt = $pdo->prepare($query);
            $stmt->execute($params);
            $exists = $stmt->fetchColumn() > 0;

            echo json_encode(['success' => true, 'exists' => $exists]);
            exit;
        } catch (Exception $e) {
            echo json_encode(['success' => false, 'message' => $e->getMessage()]);
            exit;
        }
    }

    // ... existing AJAX handlers ...
}

if (!isset($_SERVER['HTTP_X_REQUESTED_WITH'])) {
    require 'products_inventory_template.php';
}
?>