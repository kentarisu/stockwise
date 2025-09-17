<?php
// Prevent direct access to template
if (!isset($user)) {
    header("Location: login.php");
    exit;
}
// Map reports.php variables to template variables
$filter = $filter ?? 'Daily';
$search = $search ?? '';
$startDate = $startDate ?? '';
$endDate = $endDate ?? '';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Reports</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <style>
        :root {
            --primary: #d32f2f; /* Darker red for better contrast */
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
            min-height: 100vh;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
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
                padding: 15px;
            }
            .sidebar.active + #content {
                margin-left: 0;
                transform: translateX(var(--sidebar-width));
            }
        }

        .navbar {
            position: sticky;
            top: 0;
            z-index: 1020;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            padding: 15px 20px;
            margin-bottom: 20px;
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
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            min-height: 100px;
            display: flex;
            align-items: center;
            padding: 12px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
        }

        .stat-card .card-body {
            display: flex;
            align-items: center;
            width: 100%;
            padding: 0;
        }

        .stat-card-content {
            flex-grow: 1;
            text-align: left;
            padding-left: 10px;
        }

        .stat-card h3 {
            font-size: 1.2rem;
            margin: 0;
            font-weight: 700;
            color: #1a1a1a;
            overflow-wrap: break-word;
            word-break: break-all;
            line-height: 1.3;
        }

        .stat-card p {
            margin: 0;
            font-size: 0.9rem;
            color: #6c757d;
        }

        .stat-icon {
            width: 45px;
            height: 45px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: #fff;
            margin-right: 15px;
            flex-shrink: 0;
        }

        @media (max-width: 992px) {
            .stat-card {
                min-height: 110px;
                padding: 10px;
            }
            .stat-card h3 {
                font-size: 1.2rem;
            }
            .stat-icon {
                width: 40px;
                height: 40px;
                font-size: 24px;
                margin-right: 12px;
            }
        }

        @media (max-width: 576px) {
            .stat-card {
                min-height: 100px;
                padding: 8px;
            }
            .stat-card h3 {
                font-size: 1.1rem;
            }
            .stat-card p {
                font-size: 0.8rem;
            }
            .stat-icon {
                width: 36px;
                height: 36px;
                font-size: 20px;
                margin-right: 10px;
            }
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

        .btn-sm.btn-outline-primary {
            border-radius: 8px;
            padding: 5px 10px;
            font-size: 0.875rem;
            transition: all 0.3s ease;
        }

        .btn-sm.btn-outline-primary:hover,
        .btn-sm.btn-outline-primary.active {
            background-color: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }

        .card {
            border: none;
            border-radius: 12px;
            background: #fff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .table-responsive {
            border-radius: 12px;
            overflow: hidden;
            /* Always allow horizontal scroll on mobile */
            width: 100%;
            margin-bottom: 1rem;
            -webkit-overflow-scrolling: touch;
        }

        .table {
            background: #fff;
            margin-bottom: 0;
        }

        .table-hover tbody tr:hover {
            background: #f8f9fa;
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

        .flatpickr-input {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            padding: 10px;
            width: 100%;
        }

        .flatpickr-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .fruits-column {
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .fruits-column:hover {
            overflow: visible;
            white-space: normal;
            background-color: #f8f9fa;
            z-index: 10;
            position: relative;
            padding: 5px;
            border-radius: 5px;
        }

        .btn-sm {
            padding: 5px 10px;
            font-size: 0.875rem;
        }

        .badge {
            padding: 8px 12px;
            border-radius: 12px;
            font-weight: 500;
        }

        .options-dropdown {
            position: relative;
            z-index: 1000;
        }

        .options-btn {
            border: none;
            background: none;
            padding: 8px;
            font-size: 1.1rem;
            color: #6c757d;
            transition: all 0.2s ease;
            z-index: 1001;
        }

        .options-btn:hover {
            color: var(--primary);
        }

        .dropdown-menu {
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            min-width: 150px;
            z-index: 1002;
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 5px;
        }

        .dropdown-item {
            padding: 8px 16px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 1003;
        }

        .dropdown-item:hover {
            background-color: var(--primary-light);
            color: var(--primary);
        }

        .nav-tabs .nav-link {
            border-radius: 8px 8px 0 0;
            padding: 12px 20px;
            color: #6c757d;
            font-weight: 500;
        }

        .nav-tabs .nav-link.active {
            background-color: #fff;
            border-color: #dee2e6 #dee2e6 #fff;
            color: var(--primary);
        }

        .tab-content {
            background: #fff;
            border: 1px solid #dee2e6;
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 20px;
        }

        /* Accessibility Improvements */
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

        /* Ensure focus visibility */
        :focus {
            outline: 3px solid var(--primary-light);
            outline-offset: 2px;
        }

        /* --- NAVBAR ENHANCEMENTS --- */
        @media (max-width: 768px) {
            .navbar {
                padding: 0.25rem 0.5rem !important;
                margin-bottom: 0.5rem !important;
                border-radius: 0 0 12px 12px;
                min-height: 48px;
            }
            .navbar .container-fluid {
                display: flex !important;
                flex-direction: row !important;
                align-items: center !important;
                gap: 0.25rem !important;
                padding: 0 !important;
            }
            .navbar .ms-auto {
                display: flex !important;
                flex-direction: row !important;
                align-items: center !important;
                gap: 0.25rem !important;
                margin-left: 0 !important;
                flex: 1 1 0;
            }
            .search-bar,
            .input-group.search-bar {
                margin-bottom: 0 !important;
                width: 100% !important;
                min-width: 0 !important;
                max-width: 140px !important;
                flex: 1 1 0;
            }
            .search-bar .form-control {
                min-width: 0;
                width: 80px;
                font-size: 0.95rem;
                padding: 0.3rem 0.5rem;
                height: 32px;
            }
            .search-bar .btn {
                padding: 0.3rem 0.7rem;
                font-size: 0.95rem;
                height: 32px;
            }
            .dropdown,
            .dropdown .btn,
            .dropdown-toggle {
                min-width: 0 !important;
                max-width: 120px !important;
                font-size: 0.95rem;
                padding: 0.3rem 0.7rem !important;
                height: 32px;
            }
            .dropdown-menu {
                min-width: 120px !important;
                font-size: 0.95rem;
            }
            .navbar .nav-link img {
                width: 28px !important;
                height: 28px !important;
            }
            #sidebarCollapseBtn {
                margin-right: 0.5rem !important;
                margin-left: 0 !important;
                padding: 0.3rem 0.7rem !important;
                height: 32px;
            }
        }

        /* --- CONTENT ADJUSTMENTS --- */
        @media (max-width: 768px) {
            .wrapper {
                display: block;
                width: 100vw;
                min-height: 100vh;
            }
            .sidebar {
                display: block !important;
            }
            #content {
                margin-left: 0 !important;
                width: 100vw !important;
                max-width: 100vw !important;
                padding: 0.5rem 0.5rem 1.5rem 0.5rem !important;
            }
            .navbar {
                border-radius: 0;
                margin-bottom: 1rem;
                padding: 0.5rem 0.5rem;
            }
            .search-bar,
            .dropdown,
            .input-group {
                width: 100% !important;
                max-width: 100% !important;
            }
            .search-bar .form-control {
                min-width: 0;
                width: 100%;
            }
            .row.mb-4.align-items-center > .col-md-12 {
                flex-direction: column;
                align-items: stretch !important;
            }
            .row.mb-4.align-items-center .btn {
                width: 100%;
                margin-bottom: 0.5rem;
            }
            .stat-card {
                margin-bottom: 1rem !important;
                border-radius: 10px;
            }
            .stat-icon {
                width: 40px;
                height: 40px;
                font-size: 20px;
            }
            .card.stat-card {
                width: 100% !important;
                min-width: 0 !important;
            }
            .row.g-4.mb-4 > .col-lg-3,
            .row.g-4.mb-4 > .col-md-6 {
                width: 100% !important;
                max-width: 100% !important;
                flex: 0 0 100% !important;
            }
            .card-body {
                padding: 1rem !important;
            }
            h2 {
                font-size: 1.2rem;
            }
        }

        @media (max-width: 576px) {
            #content {
                padding: 0.25rem 0.25rem 1rem 0.25rem !important;
            }
            .navbar {
                padding: 0.25rem 0.25rem;
            }
            .card-body {
                padding: 0.75rem !important;
            }
            .stat-icon {
                width: 32px;
                height: 32px;
                font-size: 16px;
            }
            .stat-card h4 {
                font-size: 1.1rem;
            }
            .stat-card p {
                font-size: 0.95rem;
            }
            /* Mobile modal adjustments */
            .modal-dialog {
                max-width: 98vw !important;
                margin: 0.25rem auto !important;
            }
            .modal-content {
                border-radius: 8px;
                padding: 0.25rem;
            }
            .modal-header, .modal-body, .modal-footer {
                padding: 0.75rem !important;
            }
            .modal-title {
                font-size: 1.1rem;
            }
            /* Mobile form controls */
            .form-control, .form-select {
                font-size: 0.9rem;
                padding: 0.375rem 0.75rem;
                height: 36px;
                border-radius: 6px;
            }
            .btn {
                font-size: 0.9rem;
                padding: 0.375rem 0.75rem;
                height: 36px;
                border-radius: 6px;
            }
            /* Mobile dropdown adjustments */
            .dropdown-menu {
                min-width: 90vw !important;
                font-size: 0.9rem;
                border-radius: 6px;
            }
            .dropdown-item {
                padding: 0.5rem 0.75rem;
                font-size: 0.9rem;
            }
        }

        /* --- Mobile Table & Card Overflow Fixes --- */
        @media (max-width: 600px) {
            .navbar .container-fluid {
                flex-direction: column;
                align-items: stretch;
                gap: 0.5rem;
            }
            .navbar .ms-auto {
                flex-direction: column;
                align-items: stretch;
                gap: 0.5rem;
            }
            .navbar .search-bar {
                margin-bottom: 0.5rem;
            }
            .navbar .input-group.search-bar,
            .navbar .dropdown,
            .navbar .dropdown-menu,
            .navbar .btn,
            .navbar .form-control {
                width: 100% !important;
                max-width: 100% !important;
                margin-bottom: 0.5rem;
            }
            .navbar .input-group {
                flex-direction: column;
                gap: 0.5rem;
            }
            .navbar .input-group .form-control {
                margin-bottom: 0.5rem;
            }
            .navbar .input-group .btn {
                width: 100%;
            }
        }

        /* --- Compact Search Bar & Button on Mobile --- */
        @media (max-width: 600px) {
            .search-bar, .input-group.search-bar {
                padding: 0.25rem 0.25rem;
                border-radius: 6px;
            }
            .search-bar .form-control, .input-group .form-control {
                font-size: 0.95rem;
                padding: 0.4rem 0.6rem;
                height: 36px;
                border-radius: 6px;
            }
            .search-bar .btn, .input-group .btn {
                font-size: 0.98rem;
                padding: 0.4rem 0.6rem;
                height: 36px;
                border-radius: 6px;
            }
        }

        /* --- SIDEBAR ENHANCEMENTS --- */
        .sidebar-backdrop {
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
                cursor: pointer;
            }
        }
        .sidebar-close-btn {
            display: none;
        }

        /* --- TABLE STANDARDIZATION --- */
        .table-standard thead th {
            background: #f8f9fa;
            font-weight: 700;
            font-size: 1rem;
            border-bottom: 2px solid #dee2e6;
        }
        .table-standard tbody tr {
            transition: box-shadow 0.2s;
        }
        .table-standard tbody tr:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            background: #f5f5f5;
        }
        .table-standard td, .table-standard th {
            vertical-align: middle;
            padding: 0.75rem 0.5rem;
        }

        /* Back to Top Button Styles */
        #backToTopBtn {
            display: none;
            position: fixed;
            bottom: 32px;
            right: 32px;
            z-index: 9999; /* Increased z-index to ensure visibility */
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

        /* Responsive table styles for mobile */
        @media (max-width: 768px) {
            .table-responsive {
                overflow-x: visible !important;
                border: 0;
                margin: 0;
                padding: 0;
                width: 100%;
            }
            .table {
                min-width: 0;
                width: 100%;
            }
            .table thead {
                display: none;
            }
            .table tbody tr {
                display: block;
                margin-bottom: 1rem;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: #fff;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                padding: 0.5rem 0.75rem;
            }
            .table tbody td {
                display: flex;
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-size: 0.97rem;
                width: 100%;
            }
            .table tbody td:last-child {
                border-bottom: none;
            }
            .table tbody td::before {
                content: attr(data-label);
                font-weight: 600;
                color: #495057;
                min-width: 110px;
                flex-shrink: 0;
                margin-right: 1rem;
            }
            .table tbody td.options-cell {
                justify-content: flex-end;
                padding: 0.5rem 0;
            }
            .products-column, .fruits-column {
                max-width: none;
                white-space: normal;
            }
            .products-column:hover, .fruits-column:hover {
                background: none;
                padding: 0;
            }
        }
        @media (max-width: 576px) {
            .table {
                min-width: 0;
            }
            .table tbody td {
                font-size: 0.92rem;
                padding: 0.4rem 0;
            }
            .table tbody tr {
                padding: 0.25rem 0.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- Sidebar Backdrop for mobile -->
        <div class="sidebar-backdrop" id="sidebarBackdrop"></div>

        <!-- Sidebar -->
        <nav id="sidebar" class="sidebar" aria-label="Main navigation">
            <button class="sidebar-close-btn" id="sidebarCloseBtn" aria-label="Close sidebar">&times;</button>
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
                <?php if ($user['role'] !== 'secretary'): ?>
                <li class="active"><a href="reports.php" aria-current="page"><i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i><span>Reports</span></a></li>
                <?php endif; ?>
                <li><a href="profile.php"><i class="bi bi-person me-2" aria-hidden="true"></i><span>Profile</span></a></li>
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
                        <div class="dropdown">
                            <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="filterDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                                <?php 
                                $dateRangeText = '';
                                if ($filter === 'Daily') {
                                    $dateRangeText = date('M d, Y');
                                } elseif ($filter === 'Weekly') {
                                    $startDate = date('M d, Y', strtotime('-7 days'));
                                    $endDate = date('M d, Y');
                                    $dateRangeText = "$startDate to $endDate";
                                } elseif ($filter === 'Monthly') {
                                    $startDate = date('M d, Y', strtotime('-1 month'));
                                    $endDate = date('M d, Y');
                                    $dateRangeText = "$startDate to $endDate";
                                } elseif ($filter === 'Custom') {
                                    if ($startDate && $endDate) {
                                        $startDate = date('M d, Y', strtotime($startDate));
                                        $endDate = date('M d, Y', strtotime($endDate));
                                        $dateRangeText = "$startDate to $endDate";
                                    } else {
                                        $dateRangeText = 'Custom';
                                    }
                                } else {
                                    $dateRangeText = $filter;
                                }
                                echo htmlspecialchars($filter === 'Custom' ? $dateRangeText : "$filter ($dateRangeText)");
                                ?>
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="filterDropdown">
                                <li><a class="dropdown-item" href="reports.php?filter=Daily&search=<?php echo urlencode($search); ?>">Daily (Today)</a></li>
                                <li><a class="dropdown-item" href="reports.php?filter=Weekly&search=<?php echo urlencode($search); ?>">Weekly (Last 7 days)</a></li>
                                <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#customRangeModal">Custom Range</a></li>
                            </ul>
                        </div>
                        <div class="dropdown ms-3">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-label="User menu">
                                <img src="<?php echo htmlspecialchars($user['profile_picture'] ?: 'assets/images/default-profile.png'); ?>" class="rounded-circle" width="32" height="32" alt="User profile picture">
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
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h2 class="mb-1 fw-bold">Reports</h2>
                        <p class="text-muted">View and export business insights, <?php echo htmlspecialchars($user['username']); ?>.</p>
                    </div>
                    <div class="col-md-6 text-md-end d-flex justify-content-md-end align-items-center flex-wrap gap-2">
                        <button class="btn btn-outline-secondary" id="refreshReports" aria-label="Refresh reports">
                            <i class="bi bi-arrow-clockwise me-1" aria-hidden="true"></i> Refresh
                        </button>
                    </div>
                </div>
                <div class="row g-4 mb-4" id="statCards">
                    <div class="col-md-6 col-lg-4">
                        <div class="card stat-card" role="region" aria-labelledby="totalRevenueLabel">
                            <div class="card-body">
                                <div class="stat-icon bg-primary">
                                    <i class="bi bi-cash-stack" aria-hidden="true"></i>
                                </div>
                                <div class="stat-card-content">
                                    <p class="text-muted mb-1 small" id="totalRevenueLabel">Total Revenue</p>
                                    <h3 class="mb-0" id="totalRevenue">₱0.00</h3>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-cash-stack" aria-hidden="true"></i> <?php echo htmlspecialchars($filter === 'Custom' ? 'Custom' : $filter); ?> revenue
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 col-lg-4">
                        <div class="card stat-card" role="region" aria-labelledby="transactionCountLabel">
                            <div class="card-body">
                                <div class="stat-icon bg-success">
                                    <i class="bi bi-cart-check" aria-hidden="true"></i>
                                </div>
                                <div class="stat-card-content">
                                    <p class="text-muted mb-1 small" id="transactionCountLabel">Transactions</p>
                                    <h3 class="mb-0" id="transactionCount">0</h3>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-receipt" aria-hidden="true"></i> Total count
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 col-lg-4">
                        <div class="card stat-card" role="region" aria-labelledby="totalBoxesSoldLabel">
                            <div class="card-body">
                                <div class="stat-icon bg-warning">
                                    <i class="bi bi-boxes" aria-hidden="true"></i>
                                </div>
                                <div class="stat-card-content">
                                    <p class="text-muted mb-1 small" id="totalBoxesSoldLabel">Total Boxes Sold</p>
                                    <h3 class="mb-0" id="totalBoxesSold">0</h3>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-boxes" aria-hidden="true"></i> <?php echo htmlspecialchars($filter === 'Custom' ? 'Custom' : $filter); ?> boxes
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Top Products</h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover align-middle" id="topFruitsTable" aria-label="Top selling fruits">
                                <thead class="table-light">
                                    <tr>
                                        <th scope="col">#</th>
                                        <th scope="col">Fruit</th>
                                        <th scope="col">Size</th>
                                        <th scope="col">Boxes Sold</th>
                                        <th scope="col">Revenue</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <ul class="nav nav-tabs mb-0" id="reportTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="sales-summary-tab" data-bs-toggle="tab" data-bs-target="#sales-summary" type="button" role="tab" aria-controls="sales-summary" aria-selected="true" data-export-type="fruit_summary">Sales Summary</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="recent-transactions-tab" data-bs-toggle="tab" data-bs-target="#recent-transactions" type="button" role="tab" aria-controls="recent-transactions" aria-selected="false" data-export-type="transactions">
                                    <span class="transactions-tab-text">Recent Transactions</span>
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="low-stock-tab" data-bs-toggle="tab" data-bs-target="#low-stock" type="button" role="tab" aria-controls="low-stock" aria-selected="false" data-export-type="low_stock">Low Stock Fruits</button>
                            </li>
                        </ul>
                        <?php if ($user['role'] === 'admin'): ?>
                            <div id="exportFormContainer">
                                <form method="POST" action="reports.php" class="d-inline" id="exportForm">
                                    <input type="hidden" name="action" value="export">
                                    <input type="hidden" name="report_type" value="fruit_summary">
                                    <button type="submit" class="btn btn-outline-primary btn-sm" aria-label="Export to CSV">
                                        <i class="bi bi-download me-1" aria-hidden="true"></i> Export Summary
                                    </button>
                                </form>
                            </div>
                        <?php endif; ?>
                    </div>
                    <div class="card-body p-0">
                        <div class="tab-content" id="reportTabsContent">
                            <div class="tab-pane fade show active" id="sales-summary" role="tabpanel" aria-labelledby="sales-summary-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover align-middle" id="fruitSummaryTable" aria-label="Sales summary by fruit">
                                        <thead class="table-light">
                                            <tr>
                                                <th scope="col">#</th>
                                                <th scope="col">Fruit</th>
                                                <th scope="col">Size</th>
                                                <th scope="col">Boxes Sold</th>
                                                <th scope="col">Price per Box</th>
                                                <th scope="col">Revenue</th>
                                            </tr>
                                        </thead>
                                        <tbody></tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="recent-transactions" role="tabpanel" aria-labelledby="recent-transactions-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover align-middle table-standard" id="transactionsTable" aria-label="Recent transactions">
                                        <thead class="table-light">
                                            <tr>
                                                <th scope="col" style="width: 10%;">Transaction #</th>
                                                <th scope="col" style="width: 15%;">Date & Time</th>
                                                <th scope="col" style="width: 20%;">Fruits</th>
                                                <th scope="col" style="width: 10%;">Size</th>
                                                <th scope="col" style="width: 8%;">Items</th>
                                                <th scope="col" style="width: 8%;">Boxes</th>
                                                <th scope="col" style="width: 12%;">Total</th>
                                                <th scope="col" style="width: 10%;">Status</th>
                                                <th scope="col" style="width: 7%;">Options</th>
                                            </tr>
                                        </thead>
                                        <tbody></tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="low-stock" role="tabpanel" aria-labelledby="low-stock-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover align-middle" id="lowStockTable" aria-label="Low stock fruits">
                                        <thead class="table-light">
                                            <tr>
                                                <th scope="col">#</th>
                                                <th scope="col">Fruit</th>
                                                <th scope="col">Size</th>
                                                <th scope="col">Stock (boxes)</th>
                                                <th scope="col">Price</th>
                                            </tr>
                                        </thead>
                                        <tbody></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Custom Range Modal -->
    <div class="modal fade" id="customRangeModal" tabindex="-1" aria-labelledby="customRangeModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="customRangeModalLabel">Select Custom Date Range</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="customRangeForm">
                        <div class="mb-3">
                            <label for="startDate" class="form-label">Start Date</label>
                            <input type="text" class="form-control flatpickr-input" id="startDate" required aria-describedby="startDateFeedback" value="<?php echo htmlspecialchars($startDate); ?>">
                            <div id="startDateFeedback" class="invalid-feedback"></div>
                        </div>
                        <div class="mb-3">
                            <label for="endDate" class="form-label">End Date</label>
                            <input type="text" class="form-control flatpickr-input" id="endDate" required aria-describedby="endDateFeedback" value="<?php echo htmlspecialchars($endDate); ?>">
                            <div id="endDateFeedback" class="invalid-feedback"></div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="applyCustomRange">Apply</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Transaction Details Modal -->
    <div class="modal fade" id="transactionDetailsModal" tabindex="-1" aria-labelledby="transactionDetailsModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="transactionDetailsModalLabel">Sale Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="transactionDetailsContent">
                        <div class="row mb-3">
                            <div class="col-12">
                                <table class="table table-bordered mb-3" style="max-width: 500px; margin: 0 auto;">
                                    <tbody>
                                        <tr><th>Transaction #:</th><td>#<span id="detailSaleId"></span></td></tr>
                                        <tr><th>OR #:</th><td><span id="detailOrNumber"></span></td></tr>
                                        <tr><th>Date:</th><td><span id="detailDateOnly"></span>, <span id="detailTimeOnly"></span></td></tr>
                                        <tr><th>Processed By:</th><td><span id="detailProcessedBy"></span></td></tr>
                                        <tr><th>Status:</th><td><span id="detailStatus"></span></td></tr>
                                        <tr><td colspan="2"><hr class="my-2" style="border-top: 2px dashed #bbb;"></td></tr>
                                        <tr>
                                            <td colspan="2" class="p-0">
                                                <table class="table mb-0" style="border: none;">
                                                    <thead>
                                                        <tr style="border-bottom: 2px solid #333;">
                                                            <th>Description</th>
                                                            <th class="text-end">Quantity</th>
                                                            <th class="text-end">Price (₱)</th>
                                                            <th class="text-end">Amount (₱)</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody id="detailItems"></tbody>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr><td colspan="2"><hr class="my-2" style="border-top: 2px dashed #bbb;"></td></tr>
                                        <tr><th>Sub Total:</th><td class="text-end"><span id="detailSubtotal"></span></td></tr>
                                        <tr><th>Plus 12% VAT:</th><td class="text-end"><span id="detailVAT"></span></td></tr>
                                        <tr style="font-weight: bold;"><th>TOTAL AMOUNT TO BE PAID:</th><td class="text-end"><span id="detailTotal"></span></td></tr>
                                        <tr><th>Cash (PHP) Tendered:</th><td class="text-end"><span id="detailAmountPaid"></span></td></tr>
                                        <tr><th>Change Cash:</th><td class="text-end"><span id="detailChange"></span></td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Void Confirmation Modal -->
    <div class="modal fade" id="voidConfirmationModal" tabindex="-1" aria-labelledby="voidConfirmationModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="voidConfirmationModalLabel">Confirm Void Sale</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="voidModalAlert" class="alert d-none mb-3" role="alert"></div>
                    <p>Are you sure you want to mark this sale as Voided? This action will restore the inventory stock.</p>
                    <input type="hidden" id="voidSaleId">
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" id="confirmVoidSale">Void Sale</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Complete Confirmation Modal -->
    <div class="modal fade" id="completeConfirmationModal" tabindex="-1" aria-labelledby="completeConfirmationModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="completeConfirmationModalLabel">Confirm Complete Sale</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="completeModalAlert" class="alert d-none mb-3" role="alert"></div>
                    <p>Are you sure you want to mark this sale as Completed? This action will deduct the inventory stock.</p>
                    <input type="hidden" id="completeSaleId">
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-success" id="confirmCompleteSale">Complete Sale</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Printable Receipt Area -->
    <div id="printArea" style="display: none;">
        <div class="receipt-container" style="max-width: 400px; margin: 0 auto; font-family: 'Courier New', Courier, monospace; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 24px;">
            <div class="receipt-header" style="text-align: center;">
                <img src="assets/logo.png" alt="Logo" style="max-width: 80px; margin-bottom: 8px;">
                <div class="company-name" style="font-weight: 700; font-size: 1.2rem; margin-bottom: 4px; letter-spacing: 0.5px;">FruitMaster Marketing</div>
                <div class="company-details" style="font-size: 0.95rem; line-height: 1.4; letter-spacing: 0.3px;">Mabini Street - Libertad, Bacolod City, Negros Occidental</div>
                <div class="company-details" style="font-size: 0.95rem; line-height: 1.4; letter-spacing: 0.3px;">TIN: </div>
                <div class="company-details" style="font-size: 0.95rem; line-height: 1.4; letter-spacing: 0.3px;">Tel: 434-7680, 213-5681, 213-5682</div>
            </div>
            <div class="receipt-title" style="text-align: center; font-weight: 700; font-size: 1.1rem; margin: 12px 0 8px 0; letter-spacing: 0.5px;">SALES RECEIPT</div>
            <div class="receipt-divider" style="border-top: 2px dashed #bbb; margin: 8px 0;"></div>
            <div id="receiptProcessedByRow" class="receipt-info" style="font-size: 0.98rem; margin-bottom: 4px; display: block; letter-spacing: 0.3px;">
                <span style="font-weight: 700;">Processed by: </span><span id="receiptProcessedBy" style="font-weight: 400;"></span>
            </div>
            <div class="receipt-info" style="font-size: 0.98rem; margin-bottom: 4px; letter-spacing: 0.3px;">
                <span style="font-weight: 700;">Transaction #: </span><span id="transactionNumber" style="font-weight: 400;"></span>
            </div>
            <div class="receipt-info" style="font-size: 0.98rem; margin-bottom: 4px; letter-spacing: 0.3px;">
                <span style="font-weight: 700;">OR #: </span><span id="orNumber" style="font-weight: 400;"></span>
            </div>
            <div class="receipt-info" style="font-size: 0.98rem; margin-bottom: 4px; letter-spacing: 0.3px;">
                <span style="font-weight: 700;">Date: </span><span id="receiptDate" style="font-weight: 400;"></span>
            </div>
            <table class="receipt-table" style="width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.95rem; letter-spacing: 0.3px;">
                <thead>
                    <tr>
                        <th style="text-align:left; border-bottom: 1px solid #ccc; padding: 4px 6px; font-weight: 700;">Description</th>
                        <th style="text-align:right; border-bottom: 1px solid #ccc; padding: 4px 6px; font-weight: 700;">Qty</th>
                        <th style="text-align:right; border-bottom: 1px solid #ccc; padding: 4px 6px; font-weight: 700;">Price</th>
                        <th style="text-align:right; border-bottom: 1px solid #ccc; padding: 4px 6px; font-weight: 700;">Amount</th>
                    </tr>
                </thead>
                <tbody id="receiptTableItems"></tbody>
            </table>
            <div class="receipt-divider" style="border-top: 2px dashed #bbb; margin: 12px 0;"></div>
            <div class="receipt-summary" style="font-size: 0.98rem; letter-spacing: 0.3px;">
                <div class="receipt-summary-row" style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 700;">Sub Total:</span>
                    <span id="receiptSubtotal" style="font-weight: 400;">0.00</span>
                </div>
                <div class="receipt-summary-row" style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 700;">Plus 12% VAT:</span>
                    <span id="receiptVAT" style="font-weight: 400;">0.00</span>
                </div>
                <div class="receipt-summary-row total" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-weight: 700;">
                    <span>TOTAL AMOUNT TO BE PAID:</span>
                    <span id="receiptTotalAmount">0.00</span>
                </div>
                <div class="receipt-summary-row" style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 700;">Cash (PHP) Tendered:</span>
                    <span id="receiptAmountPaid" style="font-weight: 400;">0.00</span>
                </div>
                <div class="receipt-summary-row" style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 700;">Change Cash:</span>
                    <span id="receiptChange" style="font-weight: 400;">0.00</span>
                </div>
            </div>
            <div class="receipt-divider" style="border-top: 2px dashed #bbb; margin: 12px 0;"></div>
            <div class="receipt-footer" style="text-align: center; font-size: 0.9rem; color: #666; line-height: 1.4; letter-spacing: 0.3px;">
                <p style="margin: 0 0 4px 0;">This serves as your Official Receipt.</p>
                <p style="margin: 0 0 4px 0;">SERVER SN: </p>
                <p style="margin: 0 0 4px 0;">POS SN: </p>
                <p style="margin: 0 0 4px 0;">BIR PERMIT NO. </p>
                <p style="margin: 0;">ACCREDITATION NO. </p>
            </div>
        </div>
    </div>

    <!-- Back to Top Button -->
    <button id="backToTopBtn" title="Back to top" aria-label="Back to top">
        <i class="bi bi-arrow-up"></i>
    </button>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script>
        const isAdmin = <?php echo json_encode($user['role'] === 'admin'); ?>;

        document.addEventListener('DOMContentLoaded', function() {
            // Sidebar toggle functionality
            const sidebar = document.getElementById('sidebar');
            const sidebarOverlay = document.getElementById('sidebarOverlay');
            const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
            const sidebarCloseBtn = document.createElement('button');
            sidebarCloseBtn.className = 'sidebar-close-btn';
            sidebarCloseBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
            sidebarCloseBtn.setAttribute('aria-label', 'Close sidebar');
            sidebar.appendChild(sidebarCloseBtn);

            function toggleSidebar() {
                sidebar.classList.toggle('active');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.toggle('active');
                }
                document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
            }

            // Toggle sidebar on button click
            if (sidebarCollapseBtn) {
                sidebarCollapseBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    toggleSidebar();
                });
            }

            // Close sidebar when clicking close button
            sidebarCloseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                toggleSidebar();
            });

            // Close sidebar when clicking overlay
            if (sidebarOverlay) {
                sidebarOverlay.addEventListener('click', function(e) {
                    e.preventDefault();
                    toggleSidebar();
                });
            }

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', function(e) {
                if (window.innerWidth <= 768 && 
                    sidebar.classList.contains('active') && 
                    !sidebar.contains(e.target) && 
                    e.target !== sidebarCollapseBtn) {
                    toggleSidebar();
                }
            });

            // Handle window resize
            window.addEventListener('resize', function() {
                if (window.innerWidth > 768) {
                    sidebar.classList.remove('active');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.remove('active');
                    }
                    document.body.style.overflow = '';
                }
            });

            // Initialize Flatpickr for date inputs
            flatpickr('#startDate', { dateFormat: 'Y-m-d', maxDate: 'today' });
            flatpickr('#endDate', { dateFormat: 'Y-m-d', maxDate: 'today' });

            // Utility function to show alerts
            function showAlert(type, message) {
                const alertContainer = document.getElementById('alertContainer');
                const alert = document.createElement('div');
                alert.className = `alert alert-${type} alert-dismissible fade show`;
                alert.setAttribute('role', 'alert');
                alert.innerHTML = `
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                alertContainer.appendChild(alert);
                setTimeout(() => alert.remove(), 5000);
            }

            // Utility function to format numbers as currency
            function formatCurrency(value) {
                return `₱${parseFloat(value).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')}`;
            }

            // Function to update summary stats dynamically
            function updateSummaryStats(salesSummary) {
                document.getElementById('totalRevenue').textContent = formatCurrency(salesSummary.total_revenue || 0);
                document.getElementById('transactionCount').textContent = salesSummary.transaction_count || 0;
                document.getElementById('avgOrderValue').textContent = formatCurrency(salesSummary.avg_order_value || 0);
                document.getElementById('totalBoxesSold').textContent = salesSummary.total_items_sold || 0;
            }

            // Dynamic export button functionality
            const exportForm = document.getElementById('exportForm');
            const exportTypeInput = exportForm?.querySelector('input[name="report_type"]');
            const exportButton = exportForm?.querySelector('button[type="submit"]');
            const exportFormContainer = document.getElementById('exportFormContainer');
            
            // Function to update export button based on active tab
            function updateExportButton() {
                if (!exportForm || !exportFormContainer) return;
                
                const activeTab = document.querySelector('.nav-link.active');
                if (!activeTab) return;
                
                const exportType = activeTab.dataset.exportType;
                
                // Hide export button for low stock tab
                if (exportType === 'low_stock') {
                    exportFormContainer.style.display = 'none';
                    return;
                }
                
                // Show export button for other tabs
                exportFormContainer.style.display = 'block';
                if (exportTypeInput) exportTypeInput.value = exportType;
                
                // Update button text based on active tab
                if (exportButton) {
                    let buttonText = 'Export CSV';
                    switch(exportType) {
                        case 'fruit_summary':
                            buttonText = 'Export Summary';
                            break;
                        case 'transactions':
                            buttonText = 'Export Transactions';
                            break;
                    }
                    exportButton.innerHTML = `<i class="bi bi-download me-1" aria-hidden="true"></i> ${buttonText}`;
                }
            }

            // Update export button when tab changes
            document.querySelectorAll('.nav-link[data-bs-toggle="tab"]').forEach(tab => {
                tab.addEventListener('shown.bs.tab', updateExportButton);
            });

            // Initial update
            updateExportButton();

            // Function to fetch reports data via AJAX
            function fetchReports() {
                const search = document.getElementById('globalSearch')?.value.trim() || '';
                const urlParams = new URLSearchParams(window.location.search);
                const filter = urlParams.get('filter') || 'Daily';
                const startDate = urlParams.get('start_date') || '';
                const endDate = urlParams.get('end_date') || '';

                // Update transactions tab text based on current filter
                updateTransactionsTabText();

                const refreshButton = document.getElementById('refreshReports');
                if (refreshButton) {
                    refreshButton.disabled = true;
                    refreshButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                }

                // Show loading state in transactions table
                const transactionsTable = document.querySelector('#transactionsTable tbody');
                if (transactionsTable) {
                    transactionsTable.innerHTML = `
                        <tr>
                            <td colspan="9" class="text-center">
                                <div class="d-flex justify-content-center align-items-center py-3">
                                    <div class="spinner-border text-primary me-2" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <span>Loading transactions...</span>
                                </div>
                            </td>
                        </tr>
                    `;
                }

                fetch(`reports.php?action=fetch_reports&filter=${encodeURIComponent(filter)}&search=${encodeURIComponent(search)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update Summary Stats
                        const totalRevenue = document.getElementById('totalRevenue');
                        const transactionCount = document.getElementById('transactionCount');
                        const avgOrderValue = document.getElementById('avgOrderValue');
                        const totalBoxesSold = document.getElementById('totalBoxesSold');

                        if (totalRevenue) totalRevenue.textContent = formatCurrency(data.data.sales_summary.total_revenue || 0);
                        if (transactionCount) transactionCount.textContent = data.data.sales_summary.transaction_count || 0;
                        if (avgOrderValue) avgOrderValue.textContent = formatCurrency(data.data.sales_summary.avg_order_value || 0);
                        if (totalBoxesSold) totalBoxesSold.textContent = data.data.sales_summary.total_items_sold || 0;

                        // Update Top Fruits Table
                        const topFruitsTable = document.querySelector('#topFruitsTable tbody');
                        if (topFruitsTable) {
                            topFruitsTable.innerHTML = '';
                            if (data.data.top_fruits.length === 0) {
                                topFruitsTable.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No fruits sold.</td></tr>`;
                            } else {
                                data.data.top_fruits.forEach(fruit => {
                                    const row = document.createElement('tr');
                                    row.innerHTML = `
                                        <td>#${fruit.product_id || 'N/A'}</td>
                                        <td>${fruit.name}</td>
                                        <td>${fruit.size || 'N/A'}</td>
                                        <td>${fruit.boxes_sold}</td>
                                        <td>${formatCurrency(fruit.revenue)}</td>
                                    `;
                                    topFruitsTable.appendChild(row);
                                });
                            }
                        }

                        // Update Transactions Table
                        const transactionsTable = document.querySelector('#transactionsTable tbody');
                        if (transactionsTable) {
                            transactionsTable.innerHTML = '';
                            if (!data.data.transactions || data.data.transactions.length === 0) {
                                let message = 'No transactions found.';
                                switch(filter) {
                                    case 'Daily':
                                        message = 'No transactions for today.';
                                        break;
                                    case 'Weekly':
                                        message = 'No transactions in the last 7 days.';
                                        break;
                                    case 'Monthly':
                                        message = 'No transactions in the last 30 days.';
                                        break;
                                    case 'Custom':
                                        message = 'No transactions in the selected date range.';
                                        break;
                                    case 'All Time':
                                        message = 'No transactions found in the system.';
                                        break;
                                }
                                transactionsTable.innerHTML = `<tr><td colspan="9" class="text-center text-muted">${message}</td></tr>`;
                            } else {
                                data.data.transactions.forEach(transaction => {
                                    const row = document.createElement('tr');
                                    row.dataset.id = transaction.sale_id;
                                    
                                    // Format the date
                                    const transactionDate = new Date(transaction.recorded_at);
                                    const formattedDate = transactionDate.toLocaleString('en-US', {
                                        year: 'numeric',
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    });

                                    // Prepare options menu
                                    let optionsHtml = `
                                        <li>
                                            <a class="dropdown-item view-details" href="#" data-id="${transaction.sale_id}">
                                                <i class="bi bi-eye" aria-hidden="true"></i> View Details
                                            </a>
                                        </li>
                                        <li>
                                            <a class="dropdown-item print-receipt" href="#" data-id="${transaction.sale_id}">
                                                <i class="bi bi-printer" aria-hidden="true"></i> Print Receipt
                                            </a>
                                        </li>
                                    `;
                                    if (isAdmin) {
                                        optionsHtml += `
                                            <li>
                                                <a class="dropdown-item void-sale" href="#" data-id="${transaction.sale_id}">
                                                    <i class="bi bi-x-circle" aria-hidden="true"></i> Void Sale
                                                </a>
                                            </li>
                                        `;
                                    }

                                    row.innerHTML = `
                                        <td data-label="Transaction #">#${transaction.sale_id}</td>
                                        <td data-label="Date & Time">${formattedDate}</td>
                                        <td class="products-column" data-label="Fruits">${transaction.fruits || 'N/A'}</td>
                                        <td data-label="Size">${transaction.sizes || 'N/A'}</td>
                                        <td data-label="Items">${transaction.fruit_count || 0}</td>
                                        <td class="boxes-column" data-label="Boxes">${transaction.total_boxes || 0}</td>
                                        <td data-label="Total">${formatCurrency(transaction.total)}</td>
                                        <td data-label="Status">
                                            <span class="badge ${transaction.status === 'Completed' ? 'bg-success' : 'bg-danger'}" role="status">
                                                ${transaction.status}
                                            </span>
                                        </td>
                                        <td class="options-cell" data-label="Options">
                                            <div class="options-dropdown">
                                                <button class="options-btn" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="More options">
                                                    <i class="bi bi-three-dots" aria-hidden="true"></i>
                                                </button>
                                                <ul class="dropdown-menu dropdown-menu-end">
                                                    ${optionsHtml}
                                                </ul>
                                            </div>
                                        </td>
                                    `;
                                    transactionsTable.appendChild(row);
                                });
                            }
                        }

                        // Update other tables
                        updateTableIfExists('fruitSummaryTable', data.data.fruit_summary);
                        updateTableIfExists('lowStockTable', data.data.low_stock);

                        // Reattach event listeners
                        attachEventListeners();
                    } else {
                        showAlert('danger', data.message || 'Failed to fetch reports.');
                        if (transactionsTable) {
                            transactionsTable.innerHTML = `
                                <tr>
                                    <td colspan="9" class="text-center text-danger">
                                        <i class="bi bi-exclamation-circle me-2"></i>
                                        Failed to load transactions. Please try again.
                                    </td>
                                </tr>
                            `;
                        }
                    }
                })
                .catch(error => {
                    console.error('Fetch Reports Error:', error);
                    showAlert('danger', 'Error fetching reports.');
                    if (transactionsTable) {
                        transactionsTable.innerHTML = `
                            <tr>
                                <td colspan="9" class="text-center text-danger">
                                    <i class="bi bi-exclamation-circle me-2"></i>
                                    Error loading transactions. Please try again.
                                </td>
                            </tr>
                        `;
                    }
                })
                .finally(() => {
                    if (refreshButton) {
                        refreshButton.disabled = false;
                        refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise me-1" aria-hidden="true"></i> Refresh';
                    }
                });
            }

            // Helper function to safely update tables
            function updateTableIfExists(tableId, data) {
                const table = document.getElementById(tableId);
                if (!table) return;

                const tbody = table.querySelector('tbody');
                if (!tbody) return;

                tbody.innerHTML = '';
                if (data.length === 0) {
                    const colSpan = table.querySelectorAll('thead th').length;
                    tbody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center text-muted">No data available.</td></tr>`;
                    return;
                }

                // Update table based on its ID
                switch(tableId) {
                    case 'topFruitsTable':
                        data.forEach(fruit => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>#${fruit.product_id || 'N/A'}</td>
                                <td>${fruit.name}</td>
                                <td>${fruit.size || 'N/A'}</td>
                                <td>${fruit.boxes_sold}</td>
                                <td>${formatCurrency(fruit.revenue)}</td>
                            `;
                            tbody.appendChild(row);
                        });
                        break;
                    case 'fruitSummaryTable':
                        data.forEach(fruit => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>#${fruit.product_id || 'N/A'}</td>
                                <td>${fruit.name}</td>
                                <td>${fruit.size || 'N/A'}</td>
                                <td>${fruit.boxes_sold}</td>
                                <td>${formatCurrency(fruit.price_per_box)}</td>
                                <td>${formatCurrency(fruit.revenue)}</td>
                            `;
                            tbody.appendChild(row);
                        });
                        break;
                    case 'transactionsTable':
                        data.forEach(transaction => {
                            const row = document.createElement('tr');
                            row.dataset.id = transaction.sale_id;
                            row.dataset.date = transaction.date;
                            row.dataset.status = transaction.status;
                            row.dataset.total = transaction.total;
                            row.dataset.items = JSON.stringify(transaction.items || []);
                            
                            const sizes = Array.from(new Set(transaction.items.map(item => item.size || 'N/A')));
                            
                            let optionsHtml = `
                                <li>
                                    <a class="dropdown-item view-details" href="#" data-id="${transaction.sale_id}">
                                        <i class="bi bi-eye" aria-hidden="true"></i> View Details
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item print-receipt" href="#" data-id="${transaction.sale_id}">
                                        <i class="bi bi-printer" aria-hidden="true"></i> Print Receipt
                                    </a>
                                </li>
                            `;
                            if (isAdmin) {
                                optionsHtml += `
                                    <li>
                                        <a class="dropdown-item void-sale" href="#" data-id="${transaction.sale_id}">
                                            <i class="bi bi-x-circle" aria-hidden="true"></i> Void Sale
                                        </a>
                                    </li>
                                `;
                            }
                            row.innerHTML = `
                                <td data-label="Transaction #">#${transaction.sale_id}</td>
                                <td data-label="Date & Time">${transaction.date}</td>
                                <td class="products-column" data-label="Fruits">${transaction.fruits || 'N/A'}</td>
                                <td data-label="Size">${sizes.join(', ')}</td>
                                <td data-label="Items">${transaction.fruit_count}</td>
                                <td class="boxes-column" data-label="Boxes">${transaction.total_boxes}</td>
                                <td data-label="Total">${formatCurrency(transaction.total)}</td>
                                <td data-label="Status">
                                    <span class="badge ${transaction.status === 'Completed' ? 'bg-success' : 'bg-danger'}" role="status">
                                        ${transaction.status}
                                    </span>
                                </td>
                                <td class="options-cell" data-label="Options">
                                    <div class="options-dropdown">
                                        <button class="options-btn" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="More options">
                                            <i class="bi bi-three-dots" aria-hidden="true"></i>
                                        </button>
                                        <ul class="dropdown-menu dropdown-menu-end">
                                            ${optionsHtml}
                                        </ul>
                                    </div>
                                </td>
                            `;
                            tbody.appendChild(row);
                        });
                        break;
                    case 'lowStockTable':
                        data.forEach(fruit => {
                            const row = document.createElement('tr');
                            const variant = fruit.variant ? ` (${fruit.variant})` : '';
                            row.innerHTML = `
                                <td>#${fruit.product_id || 'N/A'}</td>
                                <td>${fruit.name}${variant}</td>
                                <td>${fruit.size || 'N/A'}</td>
                                <td>${fruit.stock}</td>
                                <td>${formatCurrency(fruit.price)}</td>
                            `;
                            tbody.appendChild(row);
                        });
                        break;
                }
            }

            // Initial fetch
            fetchReports();

            // Refresh button
            const refreshReportsBtn = document.getElementById('refreshReports');
            if (refreshReportsBtn) {
                refreshReportsBtn.addEventListener('click', function() {
                    const btn = this;
                    btn.disabled = true;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                    
                    // Reload the entire page after a short delay to show the loading state
                    setTimeout(() => {
                        window.location.reload();
                    }, 800);
                });
            }

            // Search functionality
            const searchInput = document.getElementById('globalSearch');
            const searchButton = document.getElementById('searchBtn');
            const searchLoading = document.querySelector('.search-loading');
            let searchTimeout;

            function performSearch() {
                const searchValue = searchInput.value.trim();
                const currentUrl = new URL(window.location.href);
                
                if (searchValue) {
                    currentUrl.searchParams.set('search', searchValue);
                } else {
                    currentUrl.searchParams.delete('search');
                }
                
                window.location.href = currentUrl.toString();
            }

            // Search on button click
            if (searchButton) {
                searchButton.addEventListener('click', performSearch);
            }

            // Search on Enter key
            if (searchInput) {
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        performSearch();
                    }
                });
            }

            // Clear search
            const clearSearchBtn = document.getElementById('clearSearch');
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', function() {
                    searchInput.value = '';
                    const currentUrl = new URL(window.location.href);
                    currentUrl.searchParams.delete('search');
                    window.location.href = currentUrl.toString();
                });
            }

            // Custom range form submission with validation
            const applyCustomRangeBtn = document.getElementById('applyCustomRange');
            if (applyCustomRangeBtn) {
                applyCustomRangeBtn.addEventListener('click', () => {
                    const startDateInput = document.getElementById('startDate');
                    const endDateInput = document.getElementById('endDate');
                    const startDate = startDateInput.value;
                    const endDate = endDateInput.value;

                    if (!startDate) {
                        startDateInput.classList.add('is-invalid');
                        document.getElementById('startDateFeedback').textContent = 'Please select a start date.';
                        return;
                    }
                    if (!endDate) {
                        endDateInput.classList.add('is-invalid');
                        document.getElementById('endDateFeedback').textContent = 'Please select an end date.';
                        return;
                    }
                    startDateInput.classList.remove('is-invalid');
                    endDateInput.classList.remove('is-invalid');

                    const urlParams = new URLSearchParams(window.location.search);
                    urlParams.set('filter', 'Custom');
                    urlParams.set('start_date', startDate);
                    urlParams.set('end_date', endDate);
                    
                    // Update transactions tab text before redirecting
                    updateTransactionsTabText();
                    
                    window.location.search = urlParams.toString();
                });
            }

            // Function to populate transaction details
            function populateTransactionDetails(saleId, date, status, total, items, or_number, username) {
                // Helper function to safely set textContent
                const setTextContent = (elementId, value) => {
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.textContent = value || '';
                    } else {
                        console.warn(`Element with ID ${elementId} not found in the DOM.`);
                    }
                };

                // Set sale details with null checks
                setTextContent('detailSaleId', saleId);
                setTextContent('detailOrNumber', or_number || 'N/A');
                setTextContent('detailProcessedBy', username || 'N/A');
                setTextContent('detailStatus', status);

                // Format date and time
                let formattedDate = 'N/A';
                let formattedTime = 'N/A';
                if (date) {
                    try {
                        const dateObj = new Date(date);
                        if (!isNaN(dateObj.getTime())) {
                            formattedDate = dateObj.toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                            });
                            formattedTime = dateObj.toLocaleTimeString('en-US', {
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        } else {
                            console.warn('Invalid date format:', date);
                        }
                    } catch (error) {
                        console.warn('Error formatting date:', error);
                    }
                }
                setTextContent('detailDateOnly', formattedDate);
                setTextContent('detailTimeOnly', formattedTime);

                // Calculate totals
                const subtotal = items.reduce((sum, item) => sum + (parseFloat(item.subtotal) || 0), 0);
                const vat = subtotal * 0.12;
                const amountPaid = parseFloat(total) || 0;
                const change = amountPaid - total;

                // Set totals
                setTextContent('detailSubtotal', formatCurrency(subtotal));
                setTextContent('detailVAT', formatCurrency(vat));
                setTextContent('detailTotal', formatCurrency(total));
                setTextContent('detailAmountPaid', formatCurrency(amountPaid));
                setTextContent('detailChange', formatCurrency(change));

                // Populate items
                const detailItems = document.getElementById('detailItems');
                if (detailItems) {
                    detailItems.innerHTML = '';
                    items.forEach(item => {
                        const tr = document.createElement('tr');
                        const variant = item.variant ? ` (${item.variant})` : '';
                        const size = item.size ? ` (${item.size})` : '';
                        tr.innerHTML = `
                            <td>
                                <div><strong>#${item.product_id || ''} ${item.product_name || item.fruit_name || 'N/A'}</strong></div>
                                <div class="text-muted small">${variant}${size}</div>
                            </td>
                            <td class="text-end">${item.quantity || 0}</td>
                            <td class="text-end">₱${parseFloat(item.price || 0).toFixed(2)}</td>
                            <td class="text-end">₱${parseFloat(item.subtotal || 0).toFixed(2)}</td>
                        `;
                        detailItems.appendChild(tr);
                    });
                } else {
                    console.warn('Element with ID detailItems not found in the DOM.');
                }
            }

            // Attach event listeners for dynamic elements
            function attachEventListeners() {
                document.querySelectorAll('.view-details').forEach(button => {
                    button.addEventListener('click', function(e) {
                        e.preventDefault();
                        const saleId = this.dataset.id;
                        fetch(`reports.php?action=fetch_transaction_details&sale_id=${saleId}`, {
                            method: 'GET',
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                const { sale_id, date, status, total, items, or_number, username } = data.data;
                                populateTransactionDetails(sale_id, date, status, total, items, or_number, username);
                                const modal = new bootstrap.Modal(document.getElementById('transactionDetailsModal'));
                                modal.show();
                            } else {
                                showAlert('danger', data.message || 'Failed to fetch transaction details.');
                            }
                        })
                        .catch(error => {
                            console.error('Fetch Transaction Details Error:', error);
                            showAlert('danger', 'Error fetching transaction details.');
                        });
                    });
                });

                // Remove the old print receipt event listener since we're using the new implementation
            }

            // Ensure event listeners are attached after initial DOM load
            attachEventListeners();

            // Add event listeners for void/complete functionality
            document.addEventListener('click', function (e) {
                const voidSale = e.target.closest('.void-sale');
                if (voidSale) {
                    e.preventDefault();
                    const saleId = voidSale.dataset.id;
                    document.getElementById('voidSaleId').value = saleId;
                    const modal = new bootstrap.Modal(document.getElementById('voidConfirmationModal'));
                    modal.show();
                }

                const completeSale = e.target.closest('.complete-sale');
                if (completeSale) {
                    e.preventDefault();
                    const saleId = completeSale.dataset.id;
                    document.getElementById('completeSaleId').value = saleId;
                    const modal = new bootstrap.Modal(document.getElementById('completeConfirmationModal'));
                    modal.show();
                }
            });

            // Confirm void sale
            const confirmVoidSaleBtn = document.getElementById('confirmVoidSale');
            if (confirmVoidSaleBtn) {
                confirmVoidSaleBtn.addEventListener('click', function () {
                    const saleId = document.getElementById('voidSaleId').value;
                    const alertElement = document.getElementById('voidModalAlert');
                    const confirmButton = this;
                    
                    // Show loading state
                    confirmButton.disabled = true;
                    confirmButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                    
                    // Clear any existing alerts
                    alertElement.classList.add('d-none');
                    alertElement.classList.remove('alert-success', 'alert-danger');
                    
                    fetch('sales.php', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: `action=void_sale&sale_id=${encodeURIComponent(saleId)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Show success message in modal
                            alertElement.textContent = data.message;
                            alertElement.classList.remove('d-none', 'alert-danger');
                            alertElement.classList.add('alert-success');
                            
                            // Close modal after a short delay
                            setTimeout(() => {
                                const modal = bootstrap.Modal.getInstance(document.getElementById('voidConfirmationModal'));
                                modal.hide();
                                // Refresh the reports data
                                fetchReports();
                            }, 1500);
                        } else {
                            // Show error message in modal
                            alertElement.textContent = data.message || 'Failed to void sale.';
                            alertElement.classList.remove('d-none', 'alert-success');
                            alertElement.classList.add('alert-danger');
                            // Re-enable the button
                            confirmButton.disabled = false;
                            confirmButton.innerHTML = 'Void Sale';
                        }
                    })
                    .catch(error => {
                        console.error('Void sale error:', error);
                        // Show error message in modal
                        alertElement.textContent = 'An error occurred while voiding the sale.';
                        alertElement.classList.remove('d-none', 'alert-success');
                        alertElement.classList.add('alert-danger');
                        // Re-enable the button
                        confirmButton.disabled = false;
                        confirmButton.innerHTML = 'Void Sale';
                    });
                });
            }

            // Confirm complete sale
            const confirmCompleteSaleBtn = document.getElementById('confirmCompleteSale');
            if (confirmCompleteSaleBtn) {
                confirmCompleteSaleBtn.addEventListener('click', function () {
                    const saleId = document.getElementById('completeSaleId').value;
                    const alertElement = document.getElementById('completeModalAlert');
                    const confirmButton = this;
                    
                    // Show loading state
                    confirmButton.disabled = true;
                    confirmButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                    
                    // Clear any existing alerts
                    alertElement.classList.add('d-none');
                    alertElement.classList.remove('alert-success', 'alert-danger');
                    
                    fetch('reports.php', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: `action=complete_sale&sale_id=${encodeURIComponent(saleId)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Show success message in modal
                            alertElement.textContent = data.message;
                            alertElement.classList.remove('d-none', 'alert-danger');
                            alertElement.classList.add('alert-success');
                            
                            // Close modal after a short delay
                            setTimeout(() => {
                                const modal = bootstrap.Modal.getInstance(document.getElementById('completeConfirmationModal'));
                                modal.hide();
                                // Refresh the reports data
                                fetchReports();
                            }, 1500);
                        } else {
                            // Show error message in modal
                            alertElement.textContent = data.message || 'Failed to complete sale.';
                            alertElement.classList.remove('d-none', 'alert-success');
                            alertElement.classList.add('alert-danger');
                            // Re-enable the button
                            confirmButton.disabled = false;
                            confirmButton.innerHTML = 'Complete Sale';
                        }
                    })
                    .catch(error => {
                        console.error('Complete sale error:', error);
                        // Show error message in modal
                        alertElement.textContent = 'An error occurred while completing the sale.';
                        alertElement.classList.remove('d-none', 'alert-success');
                        alertElement.classList.add('alert-danger');
                        // Re-enable the button
                        confirmButton.disabled = false;
                        confirmButton.innerHTML = 'Complete Sale';
                    });
                });
            }

            // Helper function to safely set text content
            function setTextContent(elementId, value) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = value || '';
                } else {
                    console.warn(`Element with ID ${elementId} not found in the DOM.`);
                }
            }

            // Helper function to format currency
            function formatCurrency(value) {
                return `₱${parseFloat(value).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')}`;
            }

            // Print receipt functionality (matching sales page implementation)
            document.addEventListener('click', function (e) {
                const printReceipt = e.target.closest('.print-receipt');
                if (printReceipt) {
                    e.preventDefault();
                    e.stopPropagation(); // Stop event from bubbling up to dropdown
                    const saleId = printReceipt.dataset.id;

                    // Fetch full sale details via AJAX
                    fetch(`reports.php?action=fetch_transaction_details&sale_id=${saleId}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const { sale_id, date, status, total, items, or_number, username } = data.data;

                            // Set header info
                            setTextContent('transactionNumber', sale_id);
                            setTextContent('orNumber', or_number || '');
                            setTextContent('receiptDate', date);
                            setTextContent('receiptProcessedBy', username || '');
                            document.getElementById('receiptProcessedByRow').style.display = 'block';

                            // Populate items
                            const receiptTableItems = document.getElementById('receiptTableItems');
                            receiptTableItems.innerHTML = '';
                            let subtotal = 0;
                            items.forEach(item => {
                                let description = `#${item.product_id || ''} ${item.fruit_name || item.product_name || 'N/A'}`;
                                if (item.variant) description += ` (${item.variant})`;
                                if (item.size) description += ` (${item.size})`;
                                const price = parseFloat(item.price || 0);
                                const quantity = parseInt(item.quantity || 0);
                                const amount = price * quantity;
                                subtotal += amount;
                                const tr = document.createElement('tr');
                                tr.innerHTML = `
                                    <td>${description}</td>
                                    <td style="text-align:right">${quantity}</td>
                                    <td style="text-align:right">₱${price.toFixed(2)}</td>
                                    <td style="text-align:right">₱${amount.toFixed(2)}</td>
                                `;
                                receiptTableItems.appendChild(tr);
                            });

                            // Calculate VAT and totals
                            const vat = subtotal * 0.12;
                            const totalWithVAT = subtotal + vat;
                            setTextContent('receiptSubtotal', `₱${subtotal.toFixed(2)}`);
                            setTextContent('receiptVAT', `₱${vat.toFixed(2)}`);
                            setTextContent('receiptTotalAmount', `₱${totalWithVAT.toFixed(2)}`);
                            setTextContent('receiptAmountPaid', `₱${parseFloat(total).toFixed(2)}`);
                            setTextContent('receiptChange', `₱${(parseFloat(total) - totalWithVAT).toFixed(2)}`);

                            // Print
                            const printArea = document.getElementById('printArea');
                            const printWindow = window.open('', '_blank');
                            printWindow.document.write(`
                                <html>
                                    <head>
                                        <title>Receipt</title>
                                        <style>
                                            body { 
                                                font-family: 'Courier New', Courier, monospace; 
                                                padding: 20px; 
                                                background: #f8f9fa; 
                                            }
                                            .receipt-container { 
                                                max-width: 400px; 
                                                margin: 0 auto; 
                                                background: #fff; 
                                                border-radius: 10px; 
                                                box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
                                                padding: 24px; 
                                                font-family: 'Courier New', Courier, monospace;
                                            }
                                            .receipt-header { text-align: center; }
                                            .receipt-title { 
                                                text-align: center; 
                                                font-weight: 700; 
                                                font-size: 1.1rem; 
                                                margin: 12px 0 8px 0; 
                                                letter-spacing: 0.5px;
                                            }
                                            .receipt-divider { border-top: 2px dashed #bbb; margin: 8px 0; }
                                            .receipt-info { 
                                                font-size: 0.98rem; 
                                                margin-bottom: 4px; 
                                                letter-spacing: 0.3px;
                                            }
                                            .company-name { 
                                                font-weight: 700; 
                                                font-size: 1.2rem; 
                                                margin-bottom: 4px; 
                                                letter-spacing: 0.5px;
                                            }
                                            .company-details { 
                                                font-size: 0.95rem; 
                                                line-height: 1.4; 
                                                letter-spacing: 0.3px;
                                            }
                                            .receipt-table { 
                                                width: 100%; 
                                                border-collapse: collapse; 
                                                margin-top: 12px; 
                                                font-size: 0.95rem; 
                                                letter-spacing: 0.3px;
                                            }
                                            .receipt-table th, .receipt-table td { 
                                                padding: 4px 6px; 
                                            }
                                            .receipt-table th { 
                                                text-align: left; 
                                                border-bottom: 1px solid #ccc; 
                                                font-weight: 700;
                                            }
                                            .receipt-table td { 
                                                text-align: right; 
                                            }
                                            .receipt-table td:first-child { 
                                                text-align: left; 
                                            }
                                            .receipt-summary { 
                                                font-size: 0.98rem; 
                                                letter-spacing: 0.3px;
                                            }
                                            .receipt-summary-row { 
                                                display: flex; 
                                                justify-content: space-between; 
                                                margin-bottom: 4px;
                                            }
                                            .receipt-summary-row.total { 
                                                font-weight: 700; 
                                            }
                                            .receipt-footer { 
                                                text-align: center; 
                                                font-size: 0.9rem; 
                                                color: #666; 
                                                line-height: 1.4; 
                                                letter-spacing: 0.3px;
                                            }
                                        </style>
                                    </head>
                                    <body>
                                        ${printArea.innerHTML}
                                    </body>
                                </html>
                            `);
                            printWindow.document.close();
                            printWindow.focus();
                            printWindow.print();
                            printWindow.close();
                        } else {
                            showAlert('danger', data.message || 'Failed to fetch sale details for receipt.');
                        }
                    })
                    .catch(error => {
                        console.error('Print Receipt Error:', error);
                        showAlert('danger', 'Error fetching sale details for receipt.');
                    });
                }
            });

            // Add event listeners to clear alerts when modals are closed
            const voidConfirmationModal = document.getElementById('voidConfirmationModal');
            if (voidConfirmationModal) {
                voidConfirmationModal.addEventListener('hidden.bs.modal', function () {
                    const alertElement = document.getElementById('voidModalAlert');
                    alertElement.classList.add('d-none');
                    alertElement.classList.remove('alert-success', 'alert-danger');
                    const confirmButton = document.getElementById('confirmVoidSale');
                    confirmButton.disabled = false;
                    confirmButton.innerHTML = 'Void Sale';
                });
            }

            const completeConfirmationModal = document.getElementById('completeConfirmationModal');
            if (completeConfirmationModal) {
                completeConfirmationModal.addEventListener('hidden.bs.modal', function () {
                    const alertElement = document.getElementById('completeModalAlert');
                    alertElement.classList.add('d-none');
                    alertElement.classList.remove('alert-success', 'alert-danger');
                    const confirmButton = document.getElementById('confirmCompleteSale');
                    confirmButton.disabled = false;
                    confirmButton.innerHTML = 'Complete Sale';
                });
            }

            // Function to update transactions tab text based on filter
            function updateTransactionsTabText() {
                const urlParams = new URLSearchParams(window.location.search);
                const filter = urlParams.get('filter') || 'Daily';
                const transactionsTabText = document.querySelector('.transactions-tab-text');
                
                if (transactionsTabText) {
                    let tabText = 'Recent Transactions';
                    switch(filter) {
                        case 'Daily':
                            tabText = 'Today\'s Transactions';
                            break;
                        case 'Weekly':
                            tabText = 'Weekly Transactions';
                            break;
                        case 'Monthly':
                            tabText = 'Monthly Transactions';
                            break;
                        case 'Custom':
                            const startDate = urlParams.get('start_date');
                            const endDate = urlParams.get('end_date');
                            if (startDate && endDate) {
                                const start = new Date(startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                                const end = new Date(endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                                tabText = `Transactions (${start} - ${end})`;
                            } else {
                                tabText = 'Custom Range Transactions';
                            }
                            break;
                        case 'All Time':
                            tabText = 'All Transactions';
                            break;
                    }
                    transactionsTabText.textContent = tabText;
                }
            }

            // Update transactions tab text when filter changes
            const filterDropdown = document.getElementById('filterDropdown');
            if (filterDropdown) {
                filterDropdown.addEventListener('change', updateTransactionsTabText);
            }

            // Initial update of transactions tab text
            updateTransactionsTabText();
        });

        // Back to Top Button logic
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
    </script>
</body>
</html>