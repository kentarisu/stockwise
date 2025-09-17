<?php
echo "<!-- USER ROLE: " . htmlspecialchars($user['role']) . " -->";
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --primary: #d32f2f;
            --primary-light: rgba(211, 47, 47, 0.1);
            --success: #2e7d32;
            --success-light: rgba(46, 125, 50, 0.1);
            --danger: #c62828;
            --danger-light: rgba(198, 40, 40, 0.1);
            --warning: #f57c00;
            --warning-light: rgba(245, 124, 0, 0.1);
            --info: #0277bd;
            --info-light: rgba(2, 119, 189, 0.1);
            --dark: #212529;
            --sidebar-width: 280px;
            --sidebar-collapsed-width: 80px;
            --topbar-height: 70px;
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
            position: sticky;
            top: 0;
            z-index: 1020;
        }

        .search-bar {
            max-width: 400px;
            background: #f1f3f5;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .search-bar:focus-within {
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .stat-card {
            border: none;
            border-radius: 12px;
            background: #fff;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            overflow: hidden;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }

        .stat-icon {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: #fff;
        }

        .modal-content {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .modal-header {
            border-bottom: none;
            padding: 20px 24px;
            background: linear-gradient(135deg, var(--primary-light), #fff);
        }

        .modal-footer {
            border-top: none;
            padding: 20px 24px;
        }

        .btn-primary {
            background: var(--primary);
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            background: #b71c1c;
            transform: translateY(-1px);
        }

        .btn-outline-secondary {
            border-radius: 8px;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }

        .table {
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .table-hover tbody tr:hover {
            background: #f8f9fa;
        }

        .card {
            border: none;
            border-radius: 12px;
            background: #fff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .card-title {
            font-weight: 600;
            color: #1a1a1a;
        }

        .form-control, .form-select {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            transition: all 0.3s ease;
        }

        .form-control:focus, .form-select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .list-group-item {
            border: none;
            padding: 15px 20px;
            transition: background 0.3s ease;
        }

        .list-group-item:hover {
            background: #f8f9fa;
        }

        .bg-danger-light { background-color: var(--danger-light); }
        .bg-warning-light { background-color: var(--warning-light); }
        .bg-success-light { background-color: var(--success-light); }

        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            border: 0;
        }

        /* Back to Top Button Styles */
        #backToTopBtn {
            display: none;
            position: fixed;
            bottom: 32px;
            right: 32px;
            z-index: 1050;
            background: var(--primary);
            color: #fff;
            border: none;
            border-radius: 50%;
            width: 48px;
            height: 48px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.18);
            font-size: 1.7rem;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: opacity 0.3s, visibility 0.3s;
        }
        #backToTopBtn.show {
            display: flex;
            opacity: 1;
            visibility: visible;
        }
        #backToTopBtn:active {
            background: #b71c1c;
        }
        @media (max-width: 576px) {
            #backToTopBtn {
                bottom: 16px;
                right: 16px;
                width: 40px;
                height: 40px;
                font-size: 1.3rem;
            }
        }
    </style>
    <?php if (isset(
        $user) && $user['role'] === 'user'): ?>
    <style>
        /* Secretary-only dashboard stat alignment */
        div.row.g-4.mb-4.secretary-stats-row {
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: center !important;
            align-items: stretch !important;
            gap: 2rem 1.5rem !important;
            background: #ffeeba !important; /* DEBUG: yellow background */
        }
        div.row.g-4.mb-4.secretary-stats-row > div.col-lg-4,
        div.row.g-4.mb-4.secretary-stats-row > div.col-md-6 {
            flex: 1 1 260px !important;
            max-width: 320px !important;
            min-width: 220px !important;
            display: flex !important;
            align-items: stretch !important;
            justify-content: center !important;
        }
        .stat-card {
            width: 100% !important;
            min-width: 0 !important;
            margin-bottom: 0 !important;
        }
        @media (max-width: 991.98px) {
            div.row.g-4.mb-4.secretary-stats-row {
                gap: 1.2rem 0.5rem !important;
            }
            div.row.g-4.mb-4.secretary-stats-row > div.col-lg-4,
            div.row.g-4.mb-4.secretary-stats-row > div.col-md-6 {
                max-width: 100% !important;
            }
        }
        @media (max-width: 600px) {
            div.row.g-4.mb-4.secretary-stats-row {
                flex-direction: column !important;
                gap: 0.7rem !important;
            }
            div.row.g-4.mb-4.secretary-stats-row > div.col-lg-4,
            div.row.g-4.mb-4.secretary-stats-row > div.col-md-6 {
                min-width: 0 !important;
                max-width: 100% !important;
            }
        }
    </style>
    <?php endif; ?>
    <style>
    /* Sidebar overlay for mobile */
    #sidebarOverlay {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.35);
        z-index: 1029;
    }
    @media (max-width: 768px) {
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            height: 100vh;
            z-index: 1031;
            box-shadow: 2px 0 10px rgba(0,0,0,0.15);
            border-radius: 0 var(--radius) var(--radius) 0;
            transition: transform 0.3s cubic-bezier(.4,0,.2,1);
            transform: translateX(-100%);
            display: block;
        }
        .sidebar.active {
            transform: translateX(0);
        }
        #sidebarOverlay.active {
            display: block;
        }
        .sidebar-close-btn {
            display: block;
            position: absolute;
            top: 10px;
            right: 10px;
            background: none;
            border: none;
            color: #fff;
            font-size: 1.5rem;
            z-index: 1040;
        }
        .navbar {
            padding: 0.5rem !important;
            margin-bottom: 1rem;
            border-radius: 0 0 12px 12px;
        }
        .navbar .container-fluid {
            padding: 0.5rem !important;
        }
        .navbar .btn {
            padding: 0.375rem 0.75rem;
            font-size: 0.9rem;
        }
        .navbar .nav-link img {
            width: 32px !important;
            height: 32px !important;
        }
        .search-bar {
            max-width: none !important;
            width: 100% !important;
            margin: 0.5rem 0 !important;
        }
        .search-bar .input-group {
            flex-wrap: nowrap !important;
        }
        .search-bar .form-control {
            flex: 1 1 auto !important;
        }
        .search-bar .btn {
            flex: 0 0 auto !important;
        }
    }
    .sidebar-close-btn {
        display: none;
    }
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- Sidebar Backdrop for mobile -->
        <div id="sidebarOverlay"></div>

        <!-- Sidebar -->
        <nav id="sidebar" class="sidebar" aria-label="Main navigation">
            <button type="button" class="sidebar-close-btn" id="sidebarCloseBtn" aria-label="Close sidebar">&times;</button>
            <div class="sidebar-header">
                <div class="d-flex align-items-center">
                    <i class="bi bi-basket-fill me-2 text-primary fs-4" aria-hidden="true"></i>
                    <h3>StockWise</h3>
                </div>
                <button type="button" id="sidebarCollapseSidebar" class="btn btn-sm d-md-none" title="Toggle sidebar menu" aria-label="Toggle sidebar menu">
                    <i class="bi bi-list text-white" aria-hidden="true"></i>
                </button>
            </div>
            <ul class="list-unstyled components">
                <li class="active">
                    <a href="dashboard.php" aria-current="page"><i class="bi bi-speedometer2 me-2" aria-hidden="true"></i><span>Dashboard</span></a>
                </li>
                <li>
                    <a href="products_inventory.php"><i class="bi bi-basket me-2" aria-hidden="true"></i><span>Fruit Inventory</span></a>
                </li>
                <li>
                    <a href="sales.php"><i class="bi bi-cart me-2" aria-hidden="true"></i><span>Sales</span></a>
                </li>
                <?php if ($user['role'] === 'admin'): ?>
                <li>
                    <a href="reports.php"><i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i><span>Reports</span></a>
                </li>
                <?php endif; ?>
                <li>
                    <a href="profile.php"><i class="bi bi-person me-2" aria-hidden="true"></i><span>Profile</span></a>
                </li>
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
                    <div class="ms-auto d-flex align-items-center flex-wrap gap-2">
                        <div class="input-group search-bar me-3">
                            <label for="globalSearch" class="sr-only">Search</label>
                            <span class="input-group-text bg-transparent border-0"><i class="bi bi-search" aria-hidden="true"></i></span>
                            <input type="text" class="form-control border-0" id="globalSearch" placeholder="Search..." value="<?php echo htmlspecialchars($search ?? ''); ?>" aria-describedby="searchFeedback">
                            <button type="button" class="btn btn-primary" id="searchBtn" aria-label="Search"><i class="bi bi-search" aria-hidden="true"></i> Search</button>
                        </div>
                        <div class="dropdown me-3">
                            <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="filterDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                                <span id="jsFilterLabel"></span>
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="filterDropdown">
                                <li><a class="dropdown-item filter-link" data-filter="Daily" href="#">Daily (<span id="jsDailyRange"></span>)</a></li>
                                <?php if ($user['role'] === 'admin'): ?>
                                <li><a class="dropdown-item filter-link" data-filter="Weekly" href="#">Weekly (<span id="jsWeeklyRange"></span>)</a></li>
                                <?php endif; ?>
                            </ul>
                        </div>
                        <div class="dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-label="User menu">
                                <img src="<?php echo htmlspecialchars($user['profile_picture'] ?: 'https://via.placeholder.com/32'); ?>" class="rounded-circle" width="32" height="32" alt="User profile picture">
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
                <div id="alertContainer" role="alert">
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
                    <?php if ($warning): ?>
                        <div class="alert alert-warning alert-dismissible fade show">
                            <?php echo htmlspecialchars($warning); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h2 class="mb-1 fw-bold">Dashboard</h2>
                        <p class="text-muted">Welcome back, <?php echo htmlspecialchars($user['username']); ?>! Here's what's happening with your inventory today.</p>
                    </div>
                    <div class="col-md-6 text-md-end d-flex justify-content-md-end align-items-center flex-wrap gap-2">
                        <button class="btn btn-outline-secondary" id="refreshDashboard" aria-label="Refresh dashboard data" title="Reload dashboard data">
                            <i class="bi bi-arrow-clockwise me-1" aria-hidden="true"></i> Refresh
                        </button>
                    </div>
                </div>
                <?php if ($user['role'] === 'secretary'): ?>
                <div class="row g-4 mb-4 secretary-stats-row">
                    <div class="col-lg-4 col-md-6">
                        <div class="card stat-card" role="region" aria-labelledby="totalProductsLabel">
                            <div class="card-body d-flex align-items-center">
                                <div class="stat-icon me-3 bg-primary">
                                    <i class="bi bi-basket" aria-hidden="true"></i>
                                </div>
                                <div>
                                    <p class="text-muted mb-1" id="totalProductsLabel">Total Fruits</p>
                                    <h4 class="mb-0" id="totalProducts"><?php echo $totalProducts; ?></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4 col-md-6">
                        <div class="card stat-card" role="region" aria-labelledby="totalBoxesSoldLabel">
                            <div class="card-body d-flex align-items-center">
                                <div class="stat-icon me-3 bg-info">
                                    <i class="bi bi-box-seam" aria-hidden="true"></i>
                                </div>
                                <div>
                                    <p class="text-muted mb-1" id="totalBoxesSoldLabel">Total Boxes Sold (Daily - <span id="jsCurrentDate"></span>)</p>
                                    <h4 class="mb-0" id="totalBoxesSold"><?php echo $totalBoxesSold; ?></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4 col-md-6">
                        <div class="card stat-card" role="region" aria-labelledby="restockAlertsLabel">
                            <div class="card-body d-flex align-items-center">
                                <div class="stat-icon me-3 bg-danger">
                                    <i class="bi bi-exclamation-triangle-fill" aria-hidden="true"></i>
                                </div>
                                <div>
                                    <p class="text-muted mb-1" id="restockAlertsLabel">Restock Alerts</p>
                                    <h4 class="mb-0" id="restockAlerts"><?php echo $restock_alerts; ?></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <script>
                function updateCurrentDate() {
                    const now = new Date();
                    const options = { month: 'short', day: '2-digit', year: 'numeric' };
                    document.getElementById('jsCurrentDate').textContent = now.toLocaleDateString('en-US', options);
                }

                // Initial update
                updateCurrentDate();

                // Update every minute
                setInterval(updateCurrentDate, 60000);

                // Ensure immediate update on page load
                document.addEventListener('DOMContentLoaded', updateCurrentDate);
                </script>
                <?php else: ?>
                <div class="row g-4 mb-4">
    <div class="col-lg-3 col-md-6">
        <div class="card stat-card" role="region" aria-labelledby="totalProductsLabel">
            <div class="card-body d-flex align-items-center">
                <div class="stat-icon me-3 bg-primary">
                    <i class="bi bi-basket" aria-hidden="true"></i>
                </div>
                <div>
                    <p class="text-muted mb-1" id="totalProductsLabel">Total Fruits</p>
                    <h4 class="mb-0" id="totalProducts"><?php echo $totalProducts; ?></h4>
                </div>
            </div>
        </div>
    </div>
    <?php if ($user['role'] === 'admin'): ?>
    <div class="col-lg-3 col-md-6">
        <div class="card stat-card" role="region" aria-labelledby="totalSalesLabel">
            <div class="card-body d-flex align-items-center">
                <div class="stat-icon me-3 bg-success">
                    <i class="bi bi-currency-exchange" aria-hidden="true"></i>
                </div>
                <div>
                    <p class="text-muted mb-1" id="totalSalesLabel">Total Sales (<span id="jsTotalSalesRange"></span>)</p>
                    <h4 class="mb-0" id="totalSales">₱<?php echo number_format($totalSales, 2); ?></h4>
                </div>
            </div>
        </div>
    </div>
    <?php endif; ?>
    <div class="col-lg-3 col-md-6">
        <div class="card stat-card" role="region" aria-labelledby="totalBoxesSoldLabel">
            <div class="card-body d-flex align-items-center">
                <div class="stat-icon me-3 bg-info">
                    <i class="bi bi-box-seam" aria-hidden="true"></i>
                </div>
                <div>
                    <p class="text-muted mb-1" id="totalBoxesSoldLabel">Total Boxes Sold (<span id="jsTotalBoxesSoldRange"></span>)</p>
                    <h4 class="mb-0" id="totalBoxesSold"><?php echo $totalBoxesSold; ?></h4>
                </div>
            </div>
        </div>
    </div>
    <div class="col-lg-3 col-md-6">
        <div class="card stat-card" role="region" aria-labelledby="restockAlertsLabel">
            <div class="card-body d-flex align-items-center">
                <div class="stat-icon me-3 bg-danger">
                    <i class="bi bi-exclamation-triangle-fill" aria-hidden="true"></i>
                </div>
                <div>
                    <p class="text-muted mb-1" id="restockAlertsLabel">Restock Alerts</p>
                    <h4 class="mb-0" id="restockAlerts"><?php echo $restock_alerts; ?></h4>
                </div>
            </div>
        </div>
    </div>
</div>
                <?php endif; ?>
                <hr class="my-4" style="border-top: 2px solid #e0e0e0;">
                <div style="margin-bottom: 2.5rem;"></div>
                <div class="row g-4 mb-4">
                    <?php if ($user['role'] === 'admin'): ?>
                    <div class="col-lg-4">
                        <div class="card stat-card" role="region" aria-labelledby="salesSummaryLabel">
                            <div class="card-header">
                                <h5 class="card-title mb-0" id="salesSummaryLabel">Sales Summary (<span id="jsSalesSummaryRange"></span>)</h5>
                            </div>
                            <div class="card-body">
                                <div class="row g-3">
                                    <?php if ($user['role'] !== 'secretary'): ?>
                                    <div class="col-12">
                                        <p class="text-muted mb-1 small">Total Sales</p>
                                        <h5 class="mb-0" id="totalSalesOverview">₱<?php echo number_format($totalSales, 2); ?></h5>
                                    </div>
                                    <?php endif; ?>
                                    <div class="col-12">
                                        <p class="text-muted mb-1 small">Total Transactions</p>
                                        <h5 class="mb-0" id="transactionCountOverview"><?php echo $transactionCount; ?></h5>
                                    </div>
                                    <?php if ($topSellingProduct): ?>
                                    <div class="col-12">
                                        <p class="text-muted mb-1 small">Top-Selling Product</p>
                                        <h6 class="mb-0">
                                            <?php 
                                            $displayName = htmlspecialchars($topSellingProduct['name']);
                                            if (!empty($topSellingProduct['size'])) {
                                                $displayName .= ' (' . htmlspecialchars($topSellingProduct['size']) . ')';
                                            }
                                            echo $displayName;
                                            ?>
                                            <span class="text-muted small">(₱<?php echo number_format($topSellingProduct['total'], 2); ?>)</span>
                                        </h6>
                                    </div>
                                    <?php endif; ?>
                                </div>
                            </div>
                            <div class="card-footer bg-white">
                                <a href="sales.php" class="btn btn-link text-decoration-none w-100">
                                    View Sales Details
                                    <i class="bi bi-arrow-right ms-1" aria-hidden="true"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                    <?php endif; ?>
                    <div class="col-lg-<?php echo ($user['role'] === 'secretary') ? '6' : '4'; ?>">
                        <div class="card stat-card" role="region" aria-labelledby="inventoryStatusLabel">
                            <div class="card-header">
                                <h5 class="card-title mb-0" id="inventoryStatusLabel">Inventory Status</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-hover align-middle" id="inventoryStatusTable" aria-label="Inventory status">
                                        <thead class="visually-hidden">
                                            <tr>
                                                <th scope="col">Product Name</th>
                                                <th scope="col">Stock</th>
                                                <th scope="col">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <?php foreach (array_slice($inventoryStatus, 0, 3) as $item): ?>
                                                <tr>
                                                    <td><?php 
                                                        $displayName = htmlspecialchars($item['name']);
                                                        if (!empty($item['size'])) {
                                                            $displayName .= ' (' . htmlspecialchars($item['size']) . ')';
                                                        }
                                                        echo $displayName;
                                                    ?></td>
                                                    <td><?php echo $item['stock'] . ' ' . ($item['stock'] == 1 ? 'box' : 'boxes'); ?></td>
                                                    <td><span class="badge <?php echo $item['statusClass']; ?>" role="status"><?php echo $item['statusText']; ?></span></td>
                                                </tr>
                                            <?php endforeach; ?>
                                            <?php if (empty($inventoryStatus)): ?>
                                                <tr>
                                                    <td colspan="3" class="text-muted">No inventory data available.</td>
                                                </tr>
                                            <?php endif; ?>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="card-footer bg-white">
                                <a href="products_inventory.php" class="btn btn-link text-decoration-none w-100">
                                    View Inventory Details
                                    <i class="bi bi-arrow-right ms-1" aria-hidden="true"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                    <?php if ($user['role'] === 'admin'): ?>
<div class="col-lg-4">
    <div class="card stat-card" role="region" aria-labelledby="recentSalesLabel">
        <div class="card-header">
            <h5 class="card-title mb-0" id="recentSalesLabel">Recent Sales</h5>
        </div>
        <div class="card-body p-0">
            <div class="list-group list-group-flush recent-sales-list" id="recentSalesList" aria-label="Recent sales">
                <?php foreach (array_slice($recentSales, 0, 3) as $sale): ?>
                    <div class="list-group-item">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <p class="mb-0 fw-medium"><?php 
                                    $displayName = htmlspecialchars($sale['name']);
                                    if (!empty($sale['size'])) {
                                        $displayName .= ' (' . htmlspecialchars($sale['size']) . ')';
                                    }
                                    echo $displayName;
                                ?></p>
                                <p class="text-muted small mb-0"><?php 
                                    $boxes = ceil($sale['items'] / 10);
                                    echo $boxes . ' ' . ($boxes == 1 ? 'box' : 'boxes');
                                ?></p>
                            </div>
                            <div class="fw-medium">₱<?php echo number_format($sale['total'], 2); ?></div>
                        </div>
                    </div>
                <?php endforeach; ?>
                <?php if (empty($recentSales)): ?>
                    <div class="list-group-item text-muted">No sales recorded.</div>
                <?php endif; ?>
            </div>
            <div class="mt-3" id="recentSalesStats">
                <p class="text-muted mb-1 small">Total Recent Sales: <strong><?php echo count($recentSales); ?></strong></p>
                <p class="text-muted mb-1 small">Highest Sale: <strong>
                    <?php 
                    if (!empty($recentSales)) {
                        $maxSale = null;
                        foreach ($recentSales as $sale) {
                            if ($maxSale === null || $sale['total'] > $maxSale['total']) {
                                $maxSale = $sale;
                            }
                        }
                        if ($maxSale) {
                            $displayName = htmlspecialchars($maxSale['name']);
                            if (!empty($maxSale['size'])) {
                                $displayName .= ' (' . htmlspecialchars($maxSale['size']) . ')';
                            }
                            echo $displayName . ' - ₱' . number_format($maxSale['total'], 2);
                        } else {
                            echo 'N/A';
                        }
                    } else {
                        echo 'N/A';
                    }
                    ?>
                </strong></p>
            </div>
        </div>
        <div class="card-footer bg-white">
            <a href="sales.php" class="btn btn-link text-decoration-none w-100">
                View All Sales
                <i class="bi bi-arrow-right ms-1" aria-hidden="true"></i>
            </a>
        </div>
    </div>
</div>

<?php else: ?>
<div class="col-lg-6">
    <div class="card stat-card" role="region" aria-labelledby="recentSalesLabel">
        <div class="card-header">
            <h5 class="card-title mb-0" id="recentSalesLabel">Recent Sales</h5>
        </div>
        <div class="card-body p-0">
            <div class="list-group list-group-flush" id="recentSalesList" aria-label="Recent sales">
                <?php foreach (array_slice($recentSales, 0, 3) as $sale): ?>
                    <div class="list-group-item">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <p class="mb-0 fw-medium"><?php 
                                    $displayName = htmlspecialchars($sale['name']);
                                    if (!empty($sale['size'])) {
                                        $displayName .= ' (' . htmlspecialchars($sale['size']) . ')';
                                    }
                                    echo $displayName;
                                ?></p>
                                <p class="text-muted small mb-0"><?php 
                                    $boxes = ceil($sale['items'] / 10);
                                    echo $boxes . ' ' . ($boxes == 1 ? 'box' : 'boxes');
                                ?></p>
                            </div>
                            <div class="fw-medium">₱<?php echo number_format($sale['total'], 2); ?></div>
                        </div>
                    </div>
                <?php endforeach; ?>
                <?php if (empty($recentSales)): ?>
                    <div class="list-group-item text-muted">No sales recorded today.</div>
                <?php endif; ?>
            </div>
            <div class="mt-3">
                <p class="text-muted mb-1 small">Total Recent Sales: <strong><?php echo count($recentSales); ?></strong></p>
                <p class="text-muted mb-1 small">Highest Sale: <strong>
                    <?php 
                    if (!empty($recentSales)) {
                        $maxSale = null;
                        foreach ($recentSales as $sale) {
                            if ($maxSale === null || $sale['total'] > $maxSale['total']) {
                                $maxSale = $sale;
                            }
                        }
                        if ($maxSale) {
                            $displayName = htmlspecialchars($maxSale['name']);
                            if (!empty($maxSale['size'])) {
                                $displayName .= ' (' . htmlspecialchars($maxSale['size']) . ')';
                            }
                            echo $displayName . ' - ₱' . number_format($maxSale['total'], 2);
                        } else {
                            echo 'N/A';
                        }
                    } else {
                        echo 'N/A';
                    }
                    ?>
                </strong></p>
            </div>
        </div>
        <div class="card-footer bg-white">
            <a href="sales.php" class="btn btn-link text-decoration-none w-100">
                View All Sales
                <i class="bi bi-arrow-right ms-1" aria-hidden="true"></i>
            </a>
        </div>
    </div>
</div>
<?php endif; ?>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Back to Top Button -->
    <button id="backToTopBtn" title="Back to top" aria-label="Back to top">
        <i class="bi bi-arrow-up"></i>
    </button>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
    // --- Dashboard Filter & Real-time Update Logic ---
    document.addEventListener('DOMContentLoaded', function() {
        // Helper: Format date as 'Mon DD, YYYY'
        function formatDate(date) {
            return date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
        }
        // Compute ranges
        const now = new Date();
        const todayStr = formatDate(now);
        const weekAgo = new Date(now);
        weekAgo.setDate(now.getDate() - 6);
        const weekRange = formatDate(weekAgo) + ' to ' + todayStr;
        // Update filter label
        const urlParams = new URLSearchParams(window.location.search);
        const filter = urlParams.get('filter') || 'Daily';
        const search = urlParams.get('search') || '';
        const jsFilterLabel = document.getElementById('jsFilterLabel');
        if (jsFilterLabel) {
            jsFilterLabel.textContent = filter + ' (' + (filter === 'Weekly' ? weekRange : todayStr) + ')';
        }
        // Update Sales Summary Range
        const jsSalesSummaryRange = document.getElementById('jsSalesSummaryRange');
        if (jsSalesSummaryRange) {
            jsSalesSummaryRange.textContent = (filter === 'Weekly' ? weekRange : todayStr);
        }
        // Update Total Sales Range
        const jsTotalSalesRange = document.getElementById('jsTotalSalesRange');
        if (jsTotalSalesRange) {
            jsTotalSalesRange.textContent = (filter === 'Weekly' ? weekRange : todayStr);
        }
        // Update Total Boxes Sold Range
        const jsTotalBoxesSoldRange = document.getElementById('jsTotalBoxesSoldRange');
        if (jsTotalBoxesSoldRange) {
            jsTotalBoxesSoldRange.textContent = (filter === 'Weekly' ? weekRange : todayStr);
        }
        // Update dropdown
        const jsDailyRange = document.getElementById('jsDailyRange');
        const jsWeeklyRange = document.getElementById('jsWeeklyRange');
        if (jsDailyRange) jsDailyRange.textContent = todayStr;
        if (jsWeeklyRange) jsWeeklyRange.textContent = weekRange;
        // Filter dropdown links
        document.querySelectorAll('.filter-link').forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const newFilter = link.getAttribute('data-filter');
                reloadDashboardWithLocalTime(newFilter, search);
            });
        });
        // Search button
        const searchBtn = document.getElementById('searchBtn');
        const searchInput = document.getElementById('globalSearch');
        if (searchBtn && searchInput) {
            searchBtn.addEventListener('click', function() {
                reloadDashboardWithLocalTime(filter, searchInput.value);
            });
        }
        // Refresh button
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                const btn = this;
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                
                // Reload the entire page after a short delay to show the loading state
                setTimeout(() => {
                    window.location.reload();
                }, 800);
            });
        }
        // Helper: Reload with local time
        function reloadDashboardWithLocalTime(filterVal, searchVal) {
            const localTime = new Date().toISOString();
            const params = new URLSearchParams();
            params.set('filter', filterVal);
            params.set('search', searchVal || '');
            params.set('local_time', localTime);
            window.location = 'dashboard.php?' + params.toString();
        }
    });
    </script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.getElementById('sidebar');
            const sidebarOverlay = document.getElementById('sidebarOverlay');
            const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
            const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
            const content = document.getElementById('content');

            function toggleSidebar() {
                if (window.innerWidth <= 768) {
                    sidebar.classList.toggle('active');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.toggle('active');
                    }
                    document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
                } else {
                    sidebar.classList.toggle('collapsed');
                    content.style.marginLeft = sidebar.classList.contains('collapsed') ? 
                        'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)';
                }
            }

            if (sidebarCollapseBtn) {
                sidebarCollapseBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    toggleSidebar();
                });
            }

            if (sidebarOverlay) {
                sidebarOverlay.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        sidebar.classList.remove('active');
                        sidebarOverlay.classList.remove('active');
                        document.body.style.overflow = '';
                    }
                });
            }

            if (sidebarCloseBtn) {
                sidebarCloseBtn.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        sidebar.classList.remove('active');
                        if (sidebarOverlay) {
                            sidebarOverlay.classList.remove('active');
                        }
                        document.body.style.overflow = '';
                    }
                });
            }

            window.addEventListener('resize', function() {
                if (window.innerWidth > 768) {
                    sidebar.classList.remove('active');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.remove('active');
                    }
                    document.body.style.overflow = '';
                    
                    content.style.marginLeft = sidebar.classList.contains('collapsed') ? 
                        'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)';
                } else {
                    sidebar.classList.remove('collapsed');
                    content.style.marginLeft = '0';
                }
            });

            if (window.innerWidth > 768) {
                content.style.marginLeft = sidebar.classList.contains('collapsed') ? 
                    'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)';
            }

            function showAlert(message, type) {
                const alertContainer = document.getElementById('alertContainer');
                const alert = document.createElement('div');
                alert.className = `alert alert-${type} alert-dismissible fade show`;
                alert.setAttribute('role', 'alert');
                alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
                alertContainer.appendChild(alert);
                setTimeout(() => alert.remove(), 5000);
            }

            const searchInput = document.getElementById('globalSearch');
            const searchBtn = document.getElementById('searchBtn');
            const searchFeedback = document.createElement('div');
            searchFeedback.id = 'searchFeedback';
            searchFeedback.className = 'invalid-feedback';
            searchInput.parentElement.appendChild(searchFeedback);

            if (searchInput && searchBtn) {
                searchBtn.addEventListener('click', function() {
                    const searchValue = searchInput.value.trim();
                    if (searchValue.length < 2) {
                        searchInput.classList.add('is-invalid');
                        searchFeedback.textContent = 'Search term must be at least 2 characters.';
                        return;
                    }
                    searchInput.classList.remove('is-invalid');
                    const currentUrl = new URL(window.location.href);
                    currentUrl.searchParams.set('search', searchValue);
                    currentUrl.searchParams.set('filter', '<?php echo urlencode($filter); ?>');
                    window.location.href = currentUrl.toString();
                });

                searchInput.addEventListener('keyup', function(e) {
                    if (e.key === 'Enter') {
                        searchBtn.click();
                    }
                });
            }

            function fetchDashboard() {
                const refreshButton = document.getElementById('refreshDashboard');
                refreshButton.disabled = true;
                refreshButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                
                // Reload the entire page after a short delay to show the loading state
                setTimeout(() => {
                    window.location.reload();
                }, 800);
            }

            function updateDashboard(data) {
                document.getElementById('totalProducts').textContent = data.totalProducts;
                document.getElementById('totalBoxesSold').textContent = data.totalBoxesSold;
                document.getElementById('restockAlerts').textContent = data.restock_alerts;

                const totalSalesElement = document.getElementById('totalSales');
                if (totalSalesElement) {
                    totalSalesElement.textContent = `₱${parseFloat(data.totalSales).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }

                const totalSalesOverviewElement = document.getElementById('totalSalesOverview');
                if (totalSalesOverviewElement) {
                    totalSalesOverviewElement.textContent = `₱${parseFloat(data.totalSales).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }

                const transactionCountOverviewElement = document.getElementById('transactionCountOverview');
                if (transactionCountOverviewElement) {
                    transactionCountOverviewElement.textContent = data.transactionCount;
                }

                const recentSalesList = document.getElementById('recentSalesList');
                if (recentSalesList) {
                    recentSalesList.innerHTML = '';
                    if (data.recentSales.length === 0) {
                        recentSalesList.innerHTML = '<div class="list-group-item text-muted">No sales recorded today.</div>';
                    } else {
                        data.recentSales.slice(0, 3).forEach(sale => {
                            const item = document.createElement('div');
                            item.className = 'list-group-item';
                            const items = parseFloat(sale.items);
                            const total = parseFloat(sale.total);
                            const boxes = items > 0 ? Math.ceil(items / 10) : 0;
                            item.innerHTML = `
                                <div class="d-flex align-items-center">
                                    <div class="flex-grow-1">
                                        <p class="mb-0 fw-medium">${sale.name}${sale.size ? ` (${sale.size})` : ''}</p>
                                        <p class="text-muted small mb-0">${boxes} ${boxes === 1 ? 'box' : 'boxes'}</p>
                                    </div>
                                    <div class="fw-medium">₱${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                                </div>
                            `;
                            recentSalesList.appendChild(item);
                        });
                    }
                }

                const inventoryTable = document.getElementById('inventoryStatusTable');
                if (inventoryTable) {
                    const tbody = inventoryTable.querySelector('tbody');
                    if (tbody) {
                        tbody.innerHTML = '';
                        if (data.inventoryStatus.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="3" class="text-muted">No inventory data available.</td></tr>';
                        } else {
                            data.inventoryStatus.slice(0, 3).forEach(item => {
                                const row = document.createElement('tr');
                                row.innerHTML = `
                                    <td>${item.name}${item.size ? ` (${item.size})` : ''}</td>
                                    <td>${item.stock} ${item.stock === 1 ? 'box' : 'boxes'}</td>
                                    <td><span class="badge ${item.statusClass}" role="status">${item.statusText}</span></td>
                                `;
                                tbody.appendChild(row);
                            });
                        }
                    }
                }
            }

            document.getElementById('refreshDashboard').addEventListener('click', fetchDashboard);

            const backToTopBtn = document.getElementById('backToTopBtn');
            window.addEventListener('scroll', function() {
                if (window.scrollY > 200) {
                    backToTopBtn.classList.add('show');
                } else {
                    backToTopBtn.classList.remove('show');
                }
            });
            backToTopBtn.addEventListener('click', function() {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    </script>
</body>
</html>