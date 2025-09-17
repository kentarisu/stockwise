<?php
// Generate CSV template
function generateCsvTemplate($pdo) {
    $stmt = $pdo->query("SELECT name, size FROM products WHERE status = 'Active' ORDER BY name");
    $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $headers = ['Purchase Date'];
    foreach ($products as $product) {
        $fullName = $product['size'] ? "{$product['name']} ({$product['size']})" : $product['name'];
        $headers[] = $fullName;
    }
    
    $csv = fopen('php://temp', 'rw');
    fputcsv($csv, $headers);
    fputcsv($csv, array_merge(['YYYY-MM-DD'], array_fill(0, count($headers) - 1, '0')));
    rewind($csv);
    $content = stream_get_contents($csv);
    fclose($csv);
    return $content;
}

// Handle template download
if (isset($_GET['action']) && $_GET['action'] === 'download_template' && isset($pdo)) {
    header('Content-Type: text/csv');
    header('Content-Disposition: attachment; filename="purchases_template.csv"');
    echo generateCsvTemplate($pdo);
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Import Purchases</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary: #d32f2f;
            --primary-light: rgba(211, 47, 47, 0.1);
            --dark: #212529;
            --sidebar-width: 280px;
            --sidebar-collapsed-width: 80px;
        }

        body {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            overflow-x: hidden;
            margin: 0;
        }

        .wrapper {
            display: flex;
            width: 100%;
            min-height: 100vh;
        }

        .sidebar {
            width: var(--sidebar-width);
            background: var(--dark);
            color: #fff;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            z-index: 1030;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
        }

        .sidebar.collapsed {
            width: var(--sidebar-collapsed-width);
        }

        .sidebar-header {
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .sidebar-header h3 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }

        .sidebar .list-unstyled {
            padding: 1.5rem 0;
            flex-grow: 1;
        }

        .sidebar .list-unstyled li a {
            padding: 12px 20px;
            display: flex;
            align-items: center;
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
            font-weight: 500;
            font-size: 1rem;
        }

        .sidebar .list-unstyled li a:hover,
        .sidebar .list-unstyled li.active a {
            color: #fff;
            background: rgba(255, 255, 255, 0.15);
            border-left-color: var(--primary);
        }

        .sidebar.collapsed .list-unstyled li a span,
        .sidebar.collapsed .sidebar-header h3 {
            display: none;
        }

        .sidebar.collapsed .list-unstyled li a {
            justify-content: center;
            padding: 15px;
        }

        .sidebar-footer {
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            gap: 10px;
        }

        #content {
            margin-left: var(--sidebar-width);
            width: calc(100% - var(--sidebar-width));
            transition: all 0.3s ease;
            padding: 20px;
        }

        .sidebar.collapsed + #content {
            margin-left: var(--sidebar-collapsed-width);
            width: calc(100% - var(--sidebar-collapsed-width));
        }

        @media (max-width: 768px) {
            .sidebar {
                width: var(--sidebar-width);
                transform: translateX(calc(-1 * var(--sidebar-width)));
            }
            .sidebar.active {
                transform: translateX(0);
            }
            .sidebar.active .list-unstyled li a span,
            .sidebar.active .sidebar-header h3 {
                display: inline;
            }
            #content {
                margin-left: 0;
                width: 100%;
            }
            .sidebar.active + #content {
                margin-left: 0;
                transform: translateX(var(--sidebar-width));
            }
        }

        .navbar {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            padding: 15px 20px;
            margin-bottom: 20px;
        }

        .card {
            border: none;
            border-radius: 12px;
            background: #fff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .btn-primary {
            background: var(--primary);
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            background: #b71c1c;
            transform: translateY(-1px);
        }

        .btn-outline-primary {
            border-color: var(--primary);
            color: var(--primary);
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .btn-outline-primary:hover {
            background: var(--primary);
            color: #fff;
            transform: translateY(-1px);
        }

        .form-control {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            padding: 0.75rem;
            font-size: 1rem;
        }

        .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .alert {
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <nav id="sidebar" class="sidebar" aria-label="Main navigation">
            <div class="sidebar-header">
                <div class="d-flex align-items-center">
                    <i class="bi bi-basket-fill me-2 text-primary fs-4" aria-hidden="true"></i>
                    <h3>StockWise</h3>
                </div>
                <button type="button" id="sidebarCollapse" class="btn btn-sm d-md-none" aria-label="Toggle navigation">
                    <i class="bi bi-list text-white" aria-hidden="true"></i>
                </button>
            </div>
            <ul class="list-unstyled components">
                <li><a href="dashboard.php"><i class="bi bi-speedometer2 me-2" aria-hidden="true"></i><span>Dashboard</span></a></li>
                <li><a href="products_inventory.php"><i class="bi bi-basket me-2" aria-hidden="true"></i><span>Fruit Inventory</span></a></li>
                <li><a href="sales.php"><i class="bi bi-cart me-2" aria-hidden="true"></i><span>Sales</span></a></li>
                <li><a href="reports.php"><i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i><span>Reports</span></a></li>
                <li><a href="profile.php"><i class="bi bi-person me-2" aria-hidden="true"></i><span>Profile</span></a></li>
                <li class="active"><a href="import_purchases.php" aria-current="page"><i class="bi bi-upload me-2" aria-hidden="true"></i><span>Import Purchases</span></a></li>
            </ul>
            <div class="sidebar-footer">
                <a href="profile.php" class="btn btn-outline-light btn-sm"><i class="bi bi-person me-2" aria-hidden="true"></i>Profile</a>
                <a href="logout.php" class="btn btn-outline-light btn-sm"><i class="bi bi-box-arrow-right me-2" aria-hidden="true"></i>Logout</a>
            </div>
        </nav>
        <div id="content">
            <nav class="navbar navbar-expand-lg" aria-label="Top navigation">
                <div class="container-fluid">
                    <button type="button" id="sidebarCollapseBtn" class="btn btn-light me-2" aria-label="Toggle sidebar">
                        <i class="bi bi-list" aria-hidden="true"></i>
                    </button>
                    <div class="ms-auto d-flex align-items-center">
                        <div class="dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-label="User menu" aria-expanded="false">
                                <img src="<?php echo htmlspecialchars($user['profile_picture'] ?? 'https://via.placeholder.com/32'); ?>" class="rounded-circle" width="32" height="32" alt="User profile picture">
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end shadow" aria-labelledby="userDropdown">
                                <li><a class="dropdown-item" href="profile.php"><i class="bi bi-person me-2" aria-hidden="true"></i>Profile</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="logout.php"><i class="bi bi-box-arrow-right me-2" aria-hidden="true"></i>Logout</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </nav>
            <div class="container-fluid">
                <div id="alertContainer" role="alert" aria-live="polite">
                    <?php if ($success): ?>
                        <div class="alert alert-success alert-dismissible fade show">
                            <?php echo htmlspecialchars($success); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                    <?php if ($error): ?>
                        <div class="alert alert-danger alert-dismissible fade show">
                            <?php echo htmlspecialchars($error); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h2 class="mb-1 fw-bold">Import Purchases</h2>
                        <p class="text-muted">Upload a CSV file to import purchase records, <?php echo htmlspecialchars($user['username'] ?? 'User'); ?>.</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-lg-8">
                        <div class="card">
                            <div class="card-body">
                                <form action="import_purchases.php" method="post" enctype="multipart/form-data" class="needs-validation" novalidate>
                                    <div class="mb-4">
                                        <label for="csvFile" class="form-label">Upload CSV File</label>
                                        <input type="file" class="form-control" id="csvFile" name="csvFile" accept=".csv" required aria-describedby="csvFileFeedback">
                                        <div id="csvFileFeedback" class="invalid-feedback">Please select a valid CSV file.</div>
                                        <div class="form-text">
                                            The CSV file must have 'Purchase Date' as the first column (format: YYYY-MM-DD, e.g., 2025-01-01), followed by columns for active products as shown in the Fruit Inventory page (e.g., 'Apples (Green) (120-150)'). Use commas (,) as delimiters. Download the template below for the correct format.
                                        </div>
                                    </div>
                                    <div class="button-group">
                                        <button type="submit" class="btn btn-primary" aria-label="Import purchases"><i class="bi bi-upload me-2" aria-hidden="true"></i>Import Purchases</button>
                                        <a href="import_purchases.php?action=download_template" class="btn btn-outline-primary" aria-label="Download CSV template"><i class="bi bi-download me-2" aria-hidden="true"></i>Download Template</a>
                                        <button type="button" class="btn btn-primary" id="refreshButton" aria-label="Refresh page"><i class="bi bi-arrow-clockwise me-2" aria-hidden="true"></i>Refresh</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Sidebar toggle
            document.getElementById('sidebarCollapseBtn').addEventListener('click', function() {
                document.getElementById('sidebar').classList.toggle('collapsed');
            });
            document.getElementById('sidebarCollapse').addEventListener('click', function() {
                document.getElementById('sidebar').classList.toggle('active');
            });

            // Form validation
            const form = document.querySelector('.needs-validation');
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });

            // Refresh button
            document.getElementById('refreshButton').addEventListener('click', function() {
                location.reload();
            });
        });
    </script>
</body>
</html>