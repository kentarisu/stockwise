<?php
session_start();
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

date_default_timezone_set('Asia/Manila');

try {
    require_once 'config.php';
} catch (Exception $e) {
    error_log("Failed to include config.php: " . $e->getMessage());
    die("Server error: Unable to load configuration.");
}

// Check if user is logged in
if (!isset($_SESSION['user_id'])) {
    error_log("User not logged in, redirecting to login.php");
    header('Location: login.php');
    exit;
}

// Initialize variables
$user = [];
$success = '';
$error = '';

// Verify database connection
if (!$pdo) {
    error_log("Database connection is null.");
    $error = "Unable to connect to the database.";
    require 'import_purchases_template.php';
    exit;
}

// Fetch user details
try {
    $stmt = $pdo->prepare("SELECT username, profile_picture FROM users WHERE user_id = ?");
    $stmt->execute([$_SESSION['user_id']]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$user) {
        error_log("User not found for user_id: " . $_SESSION['user_id']);
        header('Location: logout.php');
        exit;
    }
} catch (Exception $e) {
    error_log("Error fetching user: " . $e->getMessage());
    $error = "Failed to load user data.";
}

// Handle CSV file upload
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['csvFile'])) {
    try {
        $pdo->beginTransaction();

        // Validate file
        $file = $_FILES['csvFile'];
        error_log("Received file: " . json_encode($file));
        $allowedTypes = ['text/csv', 'application/csv', 'text/plain', 'application/octet-stream'];
        if (!isset($file['tmp_name']) || !is_uploaded_file($file['tmp_name'])) {
            throw new Exception("No file uploaded or upload error.");
        }
        if (!in_array($file['type'], $allowedTypes) || $file['size'] > 5 * 1024 * 1024) {
            throw new Exception("Invalid file. Please upload a CSV file (.csv, max 5MB).");
        }
        if ($file['size'] == 0) {
            throw new Exception("Uploaded file is empty.");
        }

        // Ensure Uploads directory exists
        $uploadDir = 'Uploads';
        if (!is_dir($uploadDir)) {
            if (!mkdir($uploadDir, 0755, true)) {
                throw new Exception("Failed to create Uploads directory.");
            }
        }
        if (!is_writable($uploadDir)) {
            throw new Exception("Uploads directory is not writable.");
        }

        // Move file to Uploads directory
        $filePath = $uploadDir . '/import_' . time() . '_' . basename($file['name']);
        error_log("Attempting to move file to: " . $filePath);
        if (!move_uploaded_file($file['tmp_name'], $filePath)) {
            throw new Exception("Failed to move uploaded file.");
        }

        // Verify file readability
        if (!is_readable($filePath)) {
            throw new Exception("Uploaded file is not readable.");
        }

        // Read raw file content
        $fileContent = file_get_contents($filePath);
        if ($fileContent === false) {
            throw new Exception("Failed to read file content.");
        }
        error_log("Raw file content (first 500 chars): " . substr($fileContent, 0, 500));
        error_log("First line (hex): " . bin2hex(strtok($fileContent, "\n")));

        // Validate basic CSV structure
        if (!preg_match('/,/', $fileContent)) {
            throw new Exception("File does not appear to be a valid CSV. No commas found. Ensure the file uses comma (,) delimiters. Download the CSV template for the correct format.");
        }

        // Enforce comma delimiter
        $delimiter = ',';
        $firstLine = strtok($fileContent, "\n");
        $fields = str_getcsv($firstLine, $delimiter);
        if (count($fields) <= 1) {
            throw new Exception("Invalid CSV format. Expected comma-separated values, but found none. Ensure the file uses comma (,) delimiters. Download the CSV template for the correct format.");
        }
        error_log("Using delimiter: comma");

        // Read CSV file
        $rows = [];
        error_log("Reading CSV file: " . $filePath . " with delimiter: comma");
        if (($handle = fopen($filePath, 'r')) !== false) {
            while (($data = fgetcsv($handle, 1000, $delimiter)) !== false) {
                $rows[] = array_map('trim', $data);
            }
            fclose($handle);
        } else {
            throw new Exception("Failed to open CSV file: " . $filePath);
        }
        unlink($filePath); // Clean up uploaded file

        if (empty($rows)) {
            throw new Exception("CSV file is empty or could not be parsed. Ensure it uses comma (,) delimiters and proper formatting.");
        }

        // Validate headers (case-insensitive, strip BOM)
        $headers = array_shift($rows); // First row is headers
        $headers = array_map(function($header) {
            return preg_replace('/^\xEF\xBB\xBF/', '', trim($header)); // Remove BOM
        }, $headers);
        error_log("Parsed headers: " . implode("|", $headers));

        // First column must be Purchase Date
        if (count($headers) < 2 || strtolower($headers[0]) !== 'purchase date') {
            throw new Exception("CSV file must have 'Purchase Date' as the first column, followed by product columns. Found: '" . ($headers[0] ?? 'empty') . "'. Ensure the file uses comma (,) delimiters and headers are properly formatted. Download the CSV template for the correct format.");
        }

        // Remaining headers are product names with optional sizes
        $productHeaders = array_slice($headers, 1);
        if (empty($productHeaders)) {
            throw new Exception("CSV file must include at least one product column after 'Purchase Date'.");
        }

        // Fetch all active products with sizes
        $stmt = $pdo->query("SELECT product_id, name, size, price FROM products WHERE status = 'Active'");
        $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
        if (empty($products)) {
            throw new Exception("No active products found in the database.");
        }

        // Create product map with full names (name (size) or name)
        $productMap = [];
        $validProductNames = [];
        foreach ($products as $product) {
            $fullName = $product['size'] ? "{$product['name']} ({$product['size']})" : $product['name'];
            $productMap[$fullName] = [
                'product_id' => $product['product_id'],
                'price' => $product['price']
            ];
            $validProductNames[] = $fullName;
        }

        // Validate product headers
        $invalidProducts = array_diff($productHeaders, array_keys($productMap));
        if (!empty($invalidProducts)) {
            $errorMsg = "Invalid product columns: " . implode(", ", $invalidProducts) . ". Products must match active products in the format 'Fruit (Variant) (Size)' or 'Fruit' as shown in the Fruit Inventory page. Valid products: " . implode(", ", $validProductNames) . ". Download the CSV template for the correct format.";
            throw new Exception($errorMsg);
        }

        $errors = [];
        $processed = 0;
        $maxAllowedDate = '2025-05-07';

        foreach ($rows as $rowNum => $row) {
            // Ensure row has at least the purchase date
            if (count($row) < 1) {
                $errors[] = "Row " . ($rowNum + 2) . ": Insufficient columns.";
                continue;
            }

            $purchaseDate = trim($row[0]);

            // Validate and normalize date
            if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $purchaseDate)) {
                // Already in YYYY-MM-DD
                $normalizedDate = $purchaseDate;
            } elseif (preg_match('/^(0[1-9]|1[0-2])\/(0[1-9]|[12]\d|3[01])\/(\d{4})$/', $purchaseDate)) {
                // Try MM/DD/YYYY
                try {
                    $dateObj = DateTime::createFromFormat('m/d/Y', $purchaseDate);
                    if ($dateObj && $dateObj->format('m/d/Y') === $purchaseDate) {
                        $normalizedDate = $dateObj->format('Y-m-d');
                        error_log("Converted MM/DD/YYYY date '$purchaseDate' to '$normalizedDate' in row " . ($rowNum + 2));
                    } else {
                        $errors[] = "Row " . ($rowNum + 2) . ": Invalid date format '$purchaseDate'. Use YYYY-MM-DD (e.g., 2025-01-01) or MM/DD/YYYY (e.g., 01/01/2025).";
                        continue;
                    }
                } catch (Exception $e) {
                    $errors[] = "Row " . ($rowNum + 2) . ": Invalid date format '$purchaseDate'. Use YYYY-MM-DD (e.g., 2025-01-01) or MM/DD/YYYY (e.g., 01/01/2025).";
                    error_log("Date parsing error in row " . ($rowNum + 2) . ": " . $e->getMessage());
                    continue;
                }
            } else {
                $errors[] = "Row " . ($rowNum + 2) . ": Invalid date format '$purchaseDate'. Use YYYY-MM-DD (e.g., 2025-01-01) or MM/DD/YYYY (e.g., 01/01/2025).";
                error_log("Invalid date format in row " . ($rowNum + 2) . ": '$purchaseDate'");
                continue;
            }

            // Check if date is within allowed range
            if ($normalizedDate > $maxAllowedDate) {
                $errors[] = "Row " . ($rowNum + 2) . ": Purchase date '$normalizedDate' is in the future (beyond 2025-05-07).";
                continue;
            }

            // Process each product quantity
            $hasValidPurchase = false;
            $saleItems = [];
            $totalAmount = 0;

            for ($i = 0; $i < count($productHeaders); $i++) {
                $productName = $productHeaders[$i];
                $quantity = isset($row[$i + 1]) ? trim($row[$i + 1]) : '';
                $quantity = ($quantity === '') ? 0 : intval($quantity);

                if ($quantity <= 0) {
                    continue; // Skip zero or empty quantities
                }

                // Validate stock
                $productId = $productMap[$productName]['product_id'];
                $stmt = $pdo->prepare("SELECT stock FROM inventory WHERE product_id = ?");
                $stmt->execute([$productId]);
                $currentStock = $stmt->fetchColumn();
                if ($currentStock === false) {
                    $errors[] = "Row " . ($rowNum + 2) . ": No inventory record for '$productName'.";
                    continue;
                }
                $currentStock = (int)$currentStock;

                if ($quantity > $currentStock) {
                    $errors[] = "Row " . ($rowNum + 2) . ": Insufficient stock for '$productName' (available: $currentStock, requested: $quantity).";
                    continue;
                }

                // Add to sale items
                $saleItems[] = [
                    'product_id' => $productId,
                    'quantity' => $quantity,
                    'price' => $productMap[$productName]['price']
                ];
                $totalAmount += $productMap[$productName]['price'] * $quantity;
                $hasValidPurchase = true;
            }

            if (!$hasValidPurchase) {
                $errors[] = "Row " . ($rowNum + 2) . ": No valid purchases (all quantities are zero or invalid).";
                continue;
            }

            if (!empty($errors)) {
                continue; // Skip row if there are errors
            }

            // Insert into sales
            $purchaseDateTime = "$normalizedDate " . date('H:i:s');
            $stmt = $pdo->prepare("
                INSERT INTO sales (recorded_at, total, status, user_id)
                VALUES (?, ?, 'Completed', ?)
            ");
            $stmt->execute([$purchaseDateTime, $totalAmount, $_SESSION['user_id']]);
            $saleId = $pdo->lastInsertId();

            // Insert into sale_items and update inventory
            foreach ($saleItems as $item) {
                // Insert sale item
                $stmt = $pdo->prepare("
                    INSERT INTO sale_items (sale_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ");
                $stmt->execute([$saleId, $item['product_id'], $item['quantity'], $item['price']]);

                // Update inventory
                $stmt = $pdo->prepare("
                    UPDATE inventory 
                    SET stock = stock - ?, last_updated = NOW()
                    WHERE product_id = ?
                ");
                $stmt->execute([$item['quantity'], $item['product_id']]);
            }

            $processed++;
        }

        $pdo->commit();

        if (!empty($errors)) {
            $error = "Processed $processed rows successfully, but some rows had errors:<br>" . implode("<br>", $errors);
        } else {
            $success = "Successfully imported $processed purchase rows.";
        }

    } catch (Exception $e) {
        $pdo->rollBack();
        error_log("Import error: " . $e->getMessage());
        $error = $e->getMessage();
    }
}

require 'import_purchases_template.php';
?>