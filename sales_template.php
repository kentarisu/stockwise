<?php
// Prevent direct access to template
if (!isset($user)) {
    header("Location: login.php");
    exit;
}
// Map sales.php variables to template variables
$todaySales = $totalRevenue ?? 0;
$transactionCount = $totalSales ?? 0;
$totalItemsSold = $totalBoxes ?? 0;
$avgOrderValue = ($transactionCount > 0) ? $totalRevenue / $transactionCount : 0;
$filter = $filter ?? 'Daily';
$search = $search ?? '';
$startDate = $startDate ?? '';
$endDate = $endDate ?? '';
$products = $products ?? [];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Sales Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
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
            --radius: 0.75rem;
            --gap: 1.25rem;
            --mobile-breakpoint: 768px;
            --tablet-breakpoint: 992px;
        }

        html, body {
            font-size: 16px;
            scroll-behavior: smooth;
        }

        body {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            font-size: 1rem;
            line-height: 1.5;
            margin: 0;
            color: #212529;
            min-height: 100vh;
            -webkit-text-size-adjust: 100%;
            -moz-text-size-adjust: 100%;
            text-size-adjust: 100%;
            overflow-x: hidden;
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
            border-radius: 0 var(--radius) var(--radius) 0;
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
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
            font-weight: 500;
            font-size: 1rem;
            border-radius: var(--radius);
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
            padding: 1rem;
        }

        .sidebar-footer {
            padding: 1.25rem;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            gap: 0.75rem;
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
            .wrapper {
                display: block;
                width: 100vw;
                min-height: 100vh;
            }
            .sidebar {
                display: block !important;
                position: fixed;
                left: 0;
                top: 0;
                height: 100vh;
                width: min(var(--sidebar-width), 80vw);
                z-index: 2000;
                background: var(--dark);
                transform: translateX(-100%);
                transition: transform 0.3s cubic-bezier(.4,0,.2,1);
                box-shadow: 2px 0 10px rgba(0,0,0,0.2);
                border-radius: 0 var(--radius) var(--radius) 0;
            }
            .sidebar.active {
                transform: translateX(0);
            }
            #sidebarOverlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.3);
                z-index: 1999;
            }
            .sidebar.active ~ #sidebarOverlay {
                display: block;
            }
            #content {
                margin-left: 0 !important;
                width: 100vw !important;
                max-width: 100vw !important;
                padding: 0.5rem 0.5rem 1.5rem 0.5rem !important;
            }
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
            overflow: visible !important;
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

        .products-column {
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .products-column:hover {
            overflow: visible;
            white-space: normal;
            background-color: #f8f9fa;
            z-index: 10;
            position: relative;
            padding: 5px;
            border-radius: 5px;
        }

        .boxes-column {
            font-weight: 500;
            color: #343a40;
        }

        .item-row {
            margin-bottom: 1rem;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.3s ease;
        }

        .item-row:hover {
            background-color: #e9ecef;
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
            z-index: 1055 !important;
            position: absolute;
            min-width: 150px;
            right: 0;
            left: auto;
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

        :focus {
            outline: 3px solid var(--primary-light);
            outline-offset: 2px;
        }

        /* Responsive container adjustments */
        @media (max-width: 576px) {
            .container-fluid {
                padding-left: 10px;
                padding-right: 10px;
            }
            
            .navbar {
                padding: 10px;
            }

            .search-bar {
                max-width: 100%;
                margin-right: 0 !important;
            }

            .search-bar .input-group {
                flex-wrap: nowrap;
            }

            .search-bar .btn {
                padding: 0.375rem 0.75rem;
            }
        }

        /* Responsive table styles */
        .table-responsive {
            margin: 0 -10px;
            padding: 0 10px;
            width: calc(100% + 20px);
        }

        @media (max-width: 768px) {
            .table-responsive {
                border: 0;
            }

            .table {
                min-width: 100%;
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
            }

            .table tbody td {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.75rem;
                border: none;
                border-bottom: 1px solid #dee2e6;
            }

            .table tbody td:last-child {
                border-bottom: none;
            }

            .table tbody td::before {
                content: attr(data-label);
                font-weight: 600;
                margin-right: 1rem;
                color: #495057;
            }

            .table tbody td.options-cell {
                justify-content: flex-end;
                padding: 0.5rem;
            }

            .products-column {
                max-width: none;
                white-space: normal;
            }

            .products-column:hover {
                background: none;
                padding: 0;
            }

            /* Adjust stat cards for mobile */
            .stat-card {
                margin-bottom: 1rem;
            }

            .stat-card .card-body {
                padding: 1rem;
            }

            .stat-icon {
                width: 40px;
                height: 40px;
                font-size: 1.25rem;
            }

            /* Adjust modal for mobile */
            .modal-dialog {
                margin: 0.5rem;
            }

            .modal-content {
                border-radius: 8px;
            }

            .modal-body {
                padding: 1rem;
            }

            .modal-footer {
                padding: 0.75rem;
            }

            /* Adjust receipt for mobile */
            #printArea .receipt-container {
                padding: 15px;
                max-width: 100%;
            }

            .receipt-table {
                font-size: 0.9rem;
            }

            .receipt-info {
                font-size: 0.9rem;
            }
        }

        /* Responsive sidebar adjustments */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease-in-out;
            }

            .sidebar.active {
                transform: translateX(0);
            }

            #content {
                margin-left: 0;
                width: 100%;
            }

            .sidebar.active + #content {
                margin-left: 0;
            }

            .navbar .container-fluid {
                padding: 0.5rem;
            }
        }

        /* Responsive button and form adjustments */
        @media (max-width: 576px) {
            .btn {
                padding: 0.375rem 0.75rem;
                font-size: 0.875rem;
            }

            .form-control, .form-select {
                font-size: 0.875rem;
            }

            .dropdown-menu {
                font-size: 0.875rem;
            }

            .nav-tabs .nav-link {
                padding: 0.5rem 0.75rem;
                font-size: 0.875rem;
            }
        }

        /* Responsive modal adjustments */
        @media (max-width: 576px) {
            .modal-dialog {
                margin: 0.25rem;
            }

            .modal-header {
                padding: 0.75rem;
            }

            .modal-body {
                padding: 0.75rem;
            }

            .modal-footer {
                padding: 0.75rem;
            }

            .modal-title {
                font-size: 1.1rem;
            }
        }

        /* Responsive receipt adjustments */
        @media print {
            @page {
                size: auto;
                margin: 0;
            }

            body {
                margin: 0;
                padding: 0;
            }

            #printArea {
                display: block !important;
                width: 100%;
                max-width: none;
            }

            .receipt-container {
                box-shadow: none !important;
                border-radius: 0 !important;
                padding: 10px !important;
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
            }
        }
        .sidebar-close-btn {
            display: none;
        }
        @media (max-width: 768px) {
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
        }

        /* --- NAVBAR ENHANCEMENTS --- */
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
            #sidebarCollapseNavbar {
                margin-right: 0.5rem !important;
                margin-left: 0 !important;
                padding: 0.3rem 0.7rem !important;
                height: 32px;
            }
        }
        @media (max-width: 576px) {
            .navbar {
                padding: 8px 6px;
                border-radius: 0 0 12px 12px;
            }
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
        @media (max-width: 768px) {
            .table-standard thead {
                display: none;
            }
            .table-standard tbody tr {
                display: block;
                margin-bottom: 1rem;
                border-radius: 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.10);
                border: 1px solid #e0e0e0;
                background: #fff;
            }
            .table-standard td {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: none;
                border-bottom: 1px solid #f0f0f0;
                padding: 0.7rem 1rem;
                font-size: 0.97rem;
            }
            .table-standard td:last-child {
                border-bottom: none;
            }
            .table-standard td::before {
                content: attr(data-label);
                font-weight: 600;
                color: #495057;
                margin-right: 1rem;
                min-width: 110px;
                flex-shrink: 0;
            }
            .table-standard .options-cell {
                justify-content: flex-end;
            }
        }

        /* --- BUTTONS --- */
        .btn, .btn-sm, .btn-outline-secondary, .btn-primary {
            border-radius: 8px;
        }
        .btn:active, .btn:focus {
            box-shadow: 0 0 0 2px var(--primary-light);
        }

        /* --- Back to Top Button --- */
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

        .voided-days-badge {
            pointer-events: none;
            z-index: 10;
        }

        /* --- Improved Mobile Responsiveness --- */
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
            h5 {
                font-size: 1rem;
            }
            .text-muted {
                font-size: 0.9rem;
            }
            /* Table adjustments for mobile */
            .table-responsive {
                margin: 0 -0.5rem;
                padding: 0 0.5rem;
                width: calc(100% + 1rem);
            }
            .table {
                min-width: 100%;
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
            }
            .table tbody td {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.75rem;
                border: none;
                border-bottom: 1px solid #dee2e6;
            }
            .table tbody td:last-child {
                border-bottom: none;
            }
            .table tbody td::before {
                content: attr(data-label);
                font-weight: 600;
                margin-right: 1rem;
                color: #495057;
                min-width: 110px;
                flex-shrink: 0;
            }
            .table tbody td.options-cell {
                justify-content: flex-end;
                padding: 0.5rem;
            }
            .products-column {
                max-width: none;
                white-space: normal;
            }
            .products-column:hover {
                background: none;
                padding: 0;
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
            .table td, .table th {
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: break-word !important;
                max-width: 100% !important;
                min-width: 0 !important;
                flex-wrap: wrap !important;
                display: block !important;
                box-sizing: border-box;
            }
            .table tr {
                display: block !important;
                width: 100% !important;
                min-width: 0 !important;
                max-width: 100% !important;
                box-sizing: border-box;
            }
            .card, .card-body {
                max-width: 100% !important;
                min-width: 0 !important;
                overflow-x: auto !important;
                word-break: break-word !important;
                box-sizing: border-box;
            }
            .card-title, .card-text {
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: break-word !important;
                max-width: 100% !important;
                min-width: 0 !important;
            }
            /* Hide horizontal scrollbars if possible */
            .table-responsive, .card-body {
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch;
            }
        }

        /* --- Mobile Search Bar & Controls Stacking --- */
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

        /* --- Receipt Print Styles for Mobile --- */
        @media print {
            @page {
                size: auto;
                margin: 0;
            }
            body {
                margin: 0;
                padding: 0;
            }
            #printArea {
                display: block !important;
                width: 100%;
                max-width: none;
            }
            .receipt-container {
                box-shadow: none !important;
                border-radius: 0 !important;
                padding: 10px !important;
                max-width: none !important;
                width: 100% !important;
            }
            .receipt-table {
                font-size: 0.9rem;
            }
            .receipt-info {
                font-size: 0.9rem;
            }
        }

        /* --- Touch targets and accessibility --- */
        .btn, .form-control, .form-select, .dropdown-item, .nav-link {
            min-height: 2.75rem;
            font-size: 1rem;
            border-radius: 0.5rem;
            outline: none;
        }
        .btn:focus, .form-control:focus, .form-select:focus, .dropdown-item:focus, .nav-link:focus {
            box-shadow: 0 0 0 2px var(--primary-light);
            outline: 2px solid var(--primary);
        }

        /* Sidebar overlay for mobile (match dashboard_template.php) */
        #sidebarOverlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.35);
            z-index: 1029;
        }
        @media (max-width: 768px) {
            .wrapper {
                display: block;
                width: 100vw;
                min-height: 100vh;
            }
            .sidebar {
                position: fixed;
                left: 0;
                top: 0;
                width: var(--sidebar-width, 280px);
                min-width: 220px;
                max-width: 90vw;
                height: 100vh;
                background: var(--dark, #212529);
                z-index: 1031;
                transform: translateX(-100%);
                transition: transform 0.3s cubic-bezier(.4,0,.2,1);
                box-shadow: 2px 0 10px rgba(0,0,0,0.15);
            }
            .sidebar.active {
                display: block !important;
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
            #content {
                margin-left: 0 !important;
                width: 100vw !important;
                max-width: 100vw !important;
                padding: 0.5rem 0.5rem 1.5rem 0.5rem !important;
                transition: none !important;
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
                <li><a href="dashboard.php"><i class="bi bi-speedometer2 me-2" aria-hidden="true"></i><span>Dashboard</span></a></li>
                <li><a href="products_inventory.php"><i class="bi bi-basket me-2" aria-hidden="true"></i><span>Fruit Inventory</span></a></li>
                <li class="active"><a href="sales.php" aria-current="page"><i class="bi bi-cart me-2" aria-hidden="true"></i><span>Sales</span></a></li>
                <?php if ($user['role'] === 'admin'): ?>
                <li><a href="reports.php"><i class="bi bi-file-earmark-text me-2" aria-hidden="true"></i><span>Reports</span></a></li>
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
                    <button type="button" id="sidebarCollapseNavbar" class="btn btn-light me-2" aria-label="Toggle sidebar" title="Show/hide sidebar">
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
                                <?php if ($user['role'] === 'admin'): ?>
                                    <li><a class="dropdown-item" href="sales.php?filter=Daily&search=<?php echo urlencode($search); ?>">Daily (Today)</a></li>
                                    <li><a class="dropdown-item" href="sales.php?filter=Weekly&search=<?php echo urlencode($search); ?>">Weekly (Last 7 days)</a></li>
                                    <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#customRangeModal">Custom Range</a></li>
                                <?php else: ?>
                                    <li><a class="dropdown-item active" href="sales.php?filter=Daily&search=<?php echo urlencode($search); ?>">Daily (Today)</a></li>
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
                    <?php if ($success && $success === 'No sales yet'): ?>
                        <div class="alert alert-success alert-dismissible fade show">
                            <?php echo htmlspecialchars($success); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php elseif ($success): ?>
                        <div class="alert alert-success alert-dismissible fade show">
                            <?php echo htmlspecialchars($success); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                    <?php if ($error && $success !== 'No sales yet'): ?>
                        <div class="alert alert-danger alert-dismissible fade show">
                            <?php echo htmlspecialchars($error); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h2 class="mb-1 fw-bold">Sales Management</h2>
                        <p class="text-muted">Track and manage your sales transactions, <?php echo htmlspecialchars($user['username']); ?>.</p>
                    </div>
                    <div class="col-md-6 text-md-end d-flex justify-content-md-end align-items-center flex-wrap gap-2">
                        <button class="btn btn-outline-secondary" id="refreshSales" aria-label="Refresh sales data" title="Reload sales data">
                            <i class="bi bi-arrow-clockwise me-1" aria-hidden="true"></i> Refresh
                        </button>
                    </div>
                </div>
                <div class="row g-4 mb-4">
                    <div class="col-md-6 col-lg-4">
                        <div class="card stat-card" role="region" aria-labelledby="totalSalesLabel">
                            <div class="card-body">
                                <div class="stat-icon bg-primary">
                                    <i class="bi bi-cash-stack" aria-hidden="true"></i>
                                </div>
                                <div class="stat-card-content">
                                    <p class="text-muted mb-1 small" id="totalSalesLabel">Total Sales</p>
                                    <h3 class="mb-0" id="totalSales">₱<?php echo number_format($todaySales, 2); ?></h3>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-cash-stack" aria-hidden="true"></i> <?php echo htmlspecialchars($filter === 'Custom' ? 'Custom' : $filter); ?> sales
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
                                    <h3 class="mb-0" id="transactionCount"><?php echo $transactionCount; ?></h3>
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
                                    <h3 class="mb-0" id="totalBoxesSold"><?php echo $totalItemsSold; ?></h3>
                                    <p class="text-muted small mb-0">
                                        <i class="bi bi-boxes" aria-hidden="true"></i> <?php echo htmlspecialchars($filter === 'Custom' ? 'Custom' : $filter); ?> boxes
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <ul class="nav nav-tabs" id="salesTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="active-sales-tab" data-bs-toggle="tab" data-bs-target="#active-sales" type="button" role="tab" aria-controls="active-sales" aria-selected="true">Recent Transactions</button>
                            </li>
                            <?php if ($user['role'] === 'admin'): ?>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="voided-sales-tab" data-bs-toggle="tab" data-bs-target="#voided-sales" type="button" role="tab" aria-controls="voided-sales" aria-selected="false">Voided Transactions</button>
                            </li>
                            <?php endif; ?>
                        </ul>
                    </div>
                    <div class="card-body p-0">
                        <div class="tab-content" id="salesTabsContent">
                            <div class="tab-pane fade show active" id="active-sales" role="tabpanel" aria-labelledby="active-sales-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover align-middle table-standard" id="salesTable" aria-label="Recent sales transactions">
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
                                        <tbody>
                                            <?php
                                            $activeSales = array_filter($sales, function($sale) {
                                                return $sale['status'] !== 'Voided';
                                            });
                                            foreach ($activeSales as $sale):
                                                $items = json_decode($sale['items_json'] ?? '[]', true);
                                                $totalBoxes = array_reduce($items, function($sum, $item) {
                                                    return $sum + ($item['quantity'] ?? 0);
                                                }, 0);
                                            ?>
                                                <tr data-id="<?php echo $sale['sale_id']; ?>"
                                                    data-date="<?php echo htmlspecialchars($sale['recorded_at']); ?>"
                                                    data-status="<?php echo htmlspecialchars($sale['status']); ?>"
                                                    data-total="<?php echo htmlspecialchars($sale['total']); ?>"
                                                    data-items='<?php echo htmlspecialchars($sale['items_json']); ?>'>
                                                    <td data-label="Transaction #">#<?php echo $sale['sale_id']; ?></td>
                                                    <td data-label="Date & Time"><?php echo htmlspecialchars($sale['recorded_at']); ?></td>
                                                    <td class="products-column" data-label="Fruits">
                                                        <?php 
                                                        $productNames = array_map(function($item) {
                                                            $variant = !empty($item['variant']) ? " ({$item['variant']})" : '';
                                                            return htmlspecialchars($item['product_name'] . $variant);
                                                        }, $items);
                                                        echo implode(', ', $productNames);
                                                        ?>
                                                    </td>
                                                    <td data-label="Size">
                                                        <?php 
                                                        $sizes = array_unique(array_map(function($item) {
                                                            return $item['size'] ?? 'N/A';
                                                        }, $items));
                                                        echo implode(', ', $sizes);
                                                        ?>
                                                    </td>
                                                    <td data-label="Items"><?php echo count($items); ?></td>
                                                    <td class="boxes-column" data-label="Boxes"><?php echo $totalBoxes; ?></td>
                                                    <td data-label="Total">₱<?php echo number_format($sale['total'], 2); ?></td>
                                                    <td data-label="Status">
                                                        <span class="badge <?php echo $sale['status'] === 'Completed' ? 'bg-success' : 'bg-danger'; ?>" role="status">
                                                            <?php echo htmlspecialchars($sale['status']); ?>
                                                        </span>
                                                    </td>
                                                    <td class="options-cell" data-label="">
                                                        <div class="options-dropdown">
                                                            <button class="options-btn" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="More options">
                                                                <i class="bi bi-three-dots" aria-hidden="true"></i>
                                                            </button>
                                                            <ul class="dropdown-menu dropdown-menu-end">
                                                                <li>
                                                                    <a class="dropdown-item view-details" href="#" data-id="<?php echo $sale['sale_id']; ?>">
                                                                        <i class="bi bi-eye" aria-hidden="true"></i> View Details
                                                                    </a>
                                                                </li>
                                                                <li>
                                                                    <a class="dropdown-item print-receipt" href="#" data-id="<?php echo $sale['sale_id']; ?>">
                                                                        <i class="bi bi-printer" aria-hidden="true"></i> Print Receipt
                                                                    </a>
                                                                </li>
                                                                <?php if ($user['role'] === 'admin'): ?>
                                                                    <?php if ($sale['status'] === 'Completed'): ?>
                                                                        <li>
                                                                            <a class="dropdown-item void-sale" href="#" data-id="<?php echo $sale['sale_id']; ?>">
                                                                                <i class="bi bi-x-circle text-danger" aria-hidden="true"></i> Mark as Voided
                                                                            </a>
                                                                        </li>
                                                                    <?php endif; ?>
                                                                <?php endif; ?>
                                                            </ul>
                                                        </div>
                                                    </td>
                                                </tr>
                                            <?php endforeach; ?>
                                            <?php if (empty($activeSales)): ?>
                                                <tr>
                                                    <td colspan="8" class="text-center text-muted">No transactions found.</td>
                                                </tr>
                                            <?php endif; ?>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="voided-sales" role="tabpanel" aria-labelledby="voided-sales-tab">
                                <div class="table-responsive">
                                    <table class="table table-hover align-middle table-standard" id="voidedSalesTable" aria-label="Voided sales transactions">
                                        <thead class="table-light">
                                            <tr>
                                                <th scope="col" style="width: 10%;">Transaction #</th>
                                                <th scope="col" style="width: 15%;">Date & Time</th>
                                                <th scope="col" style="width: 25%;">Fruits</th>
                                                <th scope="col" style="width: 10%;">Size</th>
                                                <th scope="col" style="width: 10%;">Items</th>
                                                <th scope="col" style="width: 10%;">Boxes</th>
                                                <th scope="col" style="width: 15%;">Total</th>
                                                <th scope="col" style="width: 10%;">Status</th>
                                                <th scope="col" style="width: 10%;">Options</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <?php
                                            // Remove the filtering since we already have $voidedSales from sales.php
                                            foreach ($voidedSales as $sale):
                                                $items = json_decode($sale['items_json'] ?? '[]', true);
                                                $totalBoxes = array_reduce($items, function($sum, $item) {
                                                    return $sum + ($item['quantity'] ?? 0);
                                                }, 0);
                                            ?>
                                                <tr data-id="<?php echo $sale['sale_id']; ?>"
                                                    data-date="<?php echo htmlspecialchars($sale['recorded_at']); ?>"
                                                    data-status="<?php echo htmlspecialchars($sale['status']); ?>"
                                                    data-total="<?php echo htmlspecialchars($sale['total']); ?>"
                                                    data-items='<?php echo htmlspecialchars($sale['items_json']); ?>'>
                                                    <td data-label="Transaction #" style="position:relative;">
                                                        #<?php echo $sale['sale_id']; ?>
                                                        <?php if (isset($sale['days_until_deletion'])): ?>
                                                            <span class="voided-days-badge badge bg-warning text-dark"
                                                                  style="position:absolute;top:2px;right:2px;font-size:0.92rem;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
                                                                <?php echo ($sale['days_until_deletion'] > 0)
                                                                    ? ($sale['days_until_deletion'] . ' day' . ($sale['days_until_deletion'] == 1 ? '' : 's') . ' left')
                                                                    : 'Deleting soon'; ?>
                                                            </span>
                                                        <?php endif; ?>
                                                    </td>
                                                    <td data-label="Date & Time"><?php echo htmlspecialchars($sale['recorded_at']); ?></td>
                                                    <td class="products-column" data-label="Fruits"><?php echo htmlspecialchars($sale['products'] ?: 'N/A'); ?></td>
                                                    <td data-label="Size"><?php echo htmlspecialchars($sale['items'][0]['size'] ?? 'N/A'); ?></td>
                                                    <td data-label="Items"><?php echo $sale['product_count']; ?></td>
                                                    <td class="boxes-column" data-label="Boxes"><?php echo $sale['total_boxes']; ?></td>
                                                    <td data-label="Total">₱<?php echo number_format($sale['total'], 2); ?></td>
                                                    <td data-label="Status">
                                                        <span class="badge <?php echo $sale['status'] === 'Completed' ? 'bg-success' : 'bg-danger'; ?>" role="status">
                                                            <?php echo htmlspecialchars($sale['status']); ?>
                                                        </span>
                                                    </td>
                                                    <td class="options-cell" data-label="">
                                                        <div class="options-dropdown">
                                                            <button class="options-btn" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="More options">
                                                                <i class="bi bi-three-dots" aria-hidden="true"></i>
                                                            </button>
                                                            <ul class="dropdown-menu dropdown-menu-end">
                                                                <li>
                                                                    <a class="dropdown-item view-details" href="#" data-id="<?php echo $sale['sale_id']; ?>">
                                                                        <i class="bi bi-eye" aria-hidden="true"></i> View Details
                                                                    </a>
                                                                </li>
                                                                <li>
                                                                    <a class="dropdown-item print-receipt" href="#" data-id="<?php echo $sale['sale_id']; ?>">
                                                                        <i class="bi bi-printer" aria-hidden="true"></i> Print Receipt
                                                                    </a>
                                                                </li>
                                                                <?php if ($user['role'] === 'admin'): ?>
                                                                    <li>
                                                                        <a class="dropdown-item complete-sale" href="#" data-id="<?php echo $sale['sale_id']; ?>">
                                                                            <i class="bi bi-check-circle text-success" aria-hidden="true"></i> Mark as Completed
                                                                        </a>
                                                                    </li>
                                                                <?php endif; ?>
                                                            </ul>
                                                        </div>
                                                    </td>
                                                </tr>
                                            <?php endforeach; ?>
                                            <?php if (empty($voidedSales)): ?>
                                                <tr>
                                                    <td colspan="9" class="text-center text-muted">No voided transactions found.</td>
                                                </tr>
                                            <?php endif; ?>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Custom Date Range Modal -->
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

    <!-- Sale Details Modal -->
    <div class="modal fade" id="saleDetailsModal" tabindex="-1" aria-labelledby="saleDetailsModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="saleDetailsModalLabel">Sale Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="saleDetailsContent">
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

    <!-- Print Limit Modal -->
    <div class="modal fade" id="printLimitModal" tabindex="-1" aria-labelledby="printLimitModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="printLimitModalLabel">Print Limit Reached</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    You have reached the maximum number of prints (3) for this receipt. Please contact the <strong>Admin</strong> if you need additional copies.
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Okay</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script>
        // Add htmlspecialchars equivalent function
        function htmlspecialchars(str) {
            if (typeof str !== 'string') return '';
            return str
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        document.addEventListener('DOMContentLoaded', function () {
            // Initialize dropdowns explicitly
            function initializeDropdowns() {
                const dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]');
                dropdownElements.forEach(element => {
                    if (!bootstrap.Dropdown.getInstance(element)) {
                        new bootstrap.Dropdown(element);
                    }
                });
            }

            // Sidebar toggle for desktop and mobile (unified logic)
            const sidebar = document.getElementById('sidebar');
            const sidebarOverlay = document.getElementById('sidebarOverlay');
            const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
            const sidebarCollapse = document.getElementById('sidebarCollapse');
            const sidebarCollapseNavbar = document.getElementById('sidebarCollapseNavbar');

            function openSidebar() {
                sidebar.classList.add('active');
                if (sidebarOverlay) sidebarOverlay.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
            function closeSidebar() {
                sidebar.classList.remove('active');
                if (sidebarOverlay) sidebarOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
            if (sidebarCollapse) {
                sidebarCollapse.addEventListener('click', function(e) {
                    e.preventDefault();
                    openSidebar();
                });
            }
            if (sidebarCollapseNavbar) {
                sidebarCollapseNavbar.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (window.innerWidth <= 768) {
                        if (sidebar.classList.contains('active')) {
                            closeSidebar();
                        } else {
                            openSidebar();
                        }
                    } else {
                        sidebar.classList.toggle('collapsed');
                        if (!sidebar.classList.contains('collapsed')) {
                            sidebar.classList.add('active');
                        } else {
                            sidebar.classList.remove('active');
                        }
                    }
                });
            }
            if (sidebarOverlay) {
                sidebarOverlay.addEventListener('click', closeSidebar);
            }
            if (sidebarCloseBtn) {
                sidebarCloseBtn.addEventListener('click', closeSidebar);
            }

            // Always initialize dropdowns on load and after table updates
            initializeDropdowns();

            // Initialize Flatpickr for date inputs
            flatpickr('#startDate', { dateFormat: 'Y-m-d', maxDate: 'today' });
            flatpickr('#endDate', { dateFormat: 'Y-m-d', maxDate: 'today' });

            // Utility function to show alerts
            function showAlert(type, message) {
                if (!message) {
                    message = type;
                    type = 'info';
                }
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

            // Utility function to calculate total boxes from items array
            function calculateTotalBoxes(items) {
                return items.reduce((sum, item) => sum + (parseInt(item.quantity) || 0), 0);
            }

            // Function to update summary stats dynamically
            function updateSummaryStats(salesData) {
                const totalSales = salesData.reduce((sum, sale) => sum + (parseFloat(sale.total) || 0), 0);
                const transactionCount = salesData.length;
                const totalBoxesSold = salesData.reduce((sum, sale) => sum + calculateTotalBoxes(sale.items || []), 0);

                document.getElementById('totalSales').textContent = formatCurrency(totalSales);
                document.getElementById('transactionCount').textContent = transactionCount;
                document.getElementById('totalBoxesSold').textContent = totalBoxesSold;
            }

            // Function to fetch sales data (used for both active and voided sales)
            function fetchSalesData(status = 'Completed') {
                // Only fetch voided sales for admin users
                if (status === 'Voided' && !<?php echo json_encode($user['role'] === 'admin'); ?>) {
                    return Promise.resolve();
                }
                
                const search = document.getElementById('globalSearch').value.trim();
                const urlParams = new URLSearchParams(window.location.search);
                const filter = urlParams.get('filter') || 'Daily';
                const startDate = urlParams.get('start_date') || '';
                const endDate = urlParams.get('end_date') || '';
                const action = status === 'Completed' ? 'fetch_sales' : 'fetch_voided_sales';
                const timestamp = new Date().getTime(); // Add timestamp for cache busting

                return fetch(`sales.php?action=${encodeURIComponent(action)}&filter=${encodeURIComponent(filter)}&search=${encodeURIComponent(search)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&_=${timestamp}`, {
                    method: 'GET',
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const tableBody = status === 'Completed' ? 
                            document.querySelector('#salesTable tbody') : 
                            document.querySelector('#voidedSalesTable tbody');
                        tableBody.innerHTML = '';

                        if (data.data.length === 0) {
                            tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No ${status === 'Completed' ? 'transactions' : 'voided transactions'} found.</td></tr>`;
                            if (status === 'Completed') updateSummaryStats([]);
                            return;
                        }

                        data.data.forEach(sale => {
                            const items = sale.items || [];
                            const totalBoxes = calculateTotalBoxes(items);
                            const row = document.createElement('tr');
                            row.dataset.id = sale.sale_id;
                            row.dataset.date = sale.recorded_at;
                            row.dataset.status = sale.status;
                            row.dataset.total = sale.total;
                            row.dataset.items = JSON.stringify(items);
                            row.innerHTML = `
                                <td>#${sale.sale_id}</td>
                                <td>${htmlspecialchars(sale.recorded_at)}</td>
                                <td class="products-column">
                                    ${sale.items.map(item => htmlspecialchars(item.product_name + (item.variant ? ` (${item.variant})` : ''))).join(', ')}
                                </td>
                                <td>
                                    ${Array.from(new Set(sale.items.map(item => htmlspecialchars(item.size || 'N/A')))).join(', ')}
                                </td>
                                <td>${sale.items.length}</td>
                                <td class="boxes-column">${sale.items.reduce((sum, item) => sum + (parseInt(item.quantity) || 0), 0)}</td>
                                <td>${formatCurrency(sale.total)}</td>
                                <td>
                                    <span class="badge ${sale.status === 'Completed' ? 'bg-success' : 'bg-danger'}" role="status">
                                        ${htmlspecialchars(sale.status)}
                                    </span>
                                </td>
                                <td class="options-cell" data-label="">
                                    <div class="options-dropdown">
                                        <button class="options-btn" type="button" data-bs-toggle="dropdown" aria-expanded="false" aria-label="More options">
                                            <i class="bi bi-three-dots" aria-hidden="true"></i>
                                        </button>
                                        <ul class="dropdown-menu dropdown-menu-end">
                                            <li>
                                                <a class="dropdown-item view-details" href="#" data-id="${sale.sale_id}">
                                                    <i class="bi bi-eye" aria-hidden="true"></i> View Details
                                                </a>
                                            </li>
                                            <li>
                                                <a class="dropdown-item print-receipt" href="#" data-id="${sale.sale_id}">
                                                    <i class="bi bi-printer" aria-hidden="true"></i> Print Receipt
                                                </a>
                                            </li>
                                            <?php if ($user['role'] === 'admin'): ?>
                                                ${sale.status === 'Completed' ? `
                                                    <li>
                                                        <a class="dropdown-item void-sale" href="#" data-id="${sale.sale_id}">
                                                            <i class="bi bi-x-circle text-danger" aria-hidden="true"></i> Mark as Voided
                                                        </a>
                                                    </li>
                                                ` : `
                                                    <li>
                                                        <a class="dropdown-item complete-sale" href="#" data-id="${sale.sale_id}">
                                                            <i class="bi bi-check-circle text-success" aria-hidden="true"></i> Mark as Completed
                                                        </a>
                                                    </li>
                                                `}
                                            <?php endif; ?>
                                        </ul>
                                    </div>
                                </td>
                            `;
                            tableBody.appendChild(row);
                        });

                        // Re-initialize dropdowns for dynamically added content
                        initializeDropdowns();

                        if (status === 'Completed') updateSummaryStats(data.data);
                    } else {
                        showAlert('danger', data.message || 'Failed to fetch sales data.');
                    }
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                    showAlert('danger', 'An error occurred while fetching sales data.');
                });
            }

            // Search button handler
            document.getElementById('searchBtn').addEventListener('click', function () {
                const search = document.getElementById('globalSearch').value.trim();
                const urlParams = new URLSearchParams(window.location.search);
                const filter = urlParams.get('filter') || 'Daily';
                const startDate = urlParams.get('start_date') || '';
                const endDate = urlParams.get('end_date') || '';
                window.location.href = `sales.php?filter=${encodeURIComponent(filter)}&search=${encodeURIComponent(search)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;
            });

            // Enter key handler for search
            document.getElementById('globalSearch').addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    document.getElementById('searchBtn').click();
                }
            });

            // Refresh sales data
            document.getElementById('refreshSales').addEventListener('click', function() {
                const btn = this;
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                
                // Reload the entire page after a short delay to show the loading state
                setTimeout(() => {
                    window.location.reload();
                }, 800);
            });

            // Apply custom date range
            document.getElementById('applyCustomRange').addEventListener('click', function () {
                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;
                const search = document.getElementById('globalSearch').value.trim();

                if (!startDate || !endDate) {
                    showAlert('danger', 'Please select both start and end dates.');
                    return;
                }

                const start = new Date(startDate);
                const end = new Date(endDate);
                if (start > end) {
                    showAlert('danger', 'Start date cannot be after end date.');
                    return;
                }

                window.location.href = `sales.php?filter=Custom&search=${encodeURIComponent(search)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;
            });

            // View sale details
            document.addEventListener('click', function (e) {
                const viewDetails = e.target.closest('.view-details');
                if (viewDetails) {
                    e.preventDefault();
                    const saleId = viewDetails.dataset.id;
                    // Fetch full sale details via AJAX
                    fetch(`sales.php?action=get_sale_details&sale_id=${encodeURIComponent(saleId)}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Sale details response:', data);
                        if (data.success && data.data && typeof data.data === 'object' && Object.keys(data.data).length > 0) {
                            const sale = data.data;
                            const items = sale.items || [];

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
                            setTextContent('detailSaleId', sale.sale_id);
                            setTextContent('detailOrNumber', sale.or_number);
                            setTextContent('detailProcessedBy', sale.username);
                            setTextContent('detailStatus', sale.status);

                            // Calculate totals
                            const total = parseFloat(sale.total) || 0;
                            const subtotal = total / 1.12; // Calculate pre-VAT amount
                            const vat = total - subtotal; // Calculate VAT amount
                            const amountPaid = parseFloat(sale.amount_paid) || total;
                            const change = amountPaid - total;

                            // Set totals with proper formatting
                            setTextContent('detailSubtotal', `₱${subtotal.toFixed(2)}`);
                            setTextContent('detailVAT', `₱${vat.toFixed(2)}`);
                            setTextContent('detailTotal', `₱${total.toFixed(2)}`);
                            setTextContent('detailAmountPaid', `₱${amountPaid.toFixed(2)}`);
                            setTextContent('detailChange', `₱${change.toFixed(2)}`);

                            // Format date and time
                            let formattedDate = '';
                            let formattedTime = '';
                            if (sale.recorded_at) {
                                let dateObj = new Date(sale.recorded_at.replace(/-/g, '/'));
                                if (!isNaN(dateObj.getTime())) {
                                    formattedDate = dateObj.toLocaleDateString('en-US', {
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric'
                                    });
                                    let hours = dateObj.getHours();
                                    let minutes = dateObj.getMinutes();
                                    let ampm = hours >= 12 ? 'PM' : 'AM';
                                    hours = hours % 12;
                                    hours = hours ? hours : 12; // the hour '0' should be '12'
                                    minutes = minutes < 10 ? '0' + minutes : minutes;
                                    formattedTime = `${hours}:${minutes} ${ampm}`;
                                } else {
                                    console.warn('Invalid date format for recorded_at:', sale.recorded_at);
                                }
                            }
                            setTextContent('detailDateOnly', formattedDate);
                            setTextContent('detailTimeOnly', formattedTime);

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
                                            <div><strong>#${item.product_id || ''} ${item.product_name || 'N/A'}</strong></div>
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

                            // Show the modal
                            const modalElement = document.getElementById('saleDetailsModal');
                            if (modalElement) {
                                const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                            } else {
                                console.error('Sale details modal element not found.');
                                showAlert('danger', 'Unable to open sale details modal.');
                            }
                        } else {
                            showAlert('danger', data.message || 'No sale details found.');
                        }
                    })
                    .catch(error => {
                        console.error('Fetch sale details error:', error);
                        showAlert('danger', error.message || 'An error occurred while fetching sale details.');
                    });
                }
            });

            // Helper function to safely set text content
            function setTextContent(elementId, value) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = value || '';
                } else {
                    console.warn(`Element with ID ${elementId} not found in the DOM.`);
                }
            }

            // Print receipt
            document.addEventListener('click', function (e) {
                const printReceipt = e.target.closest('.print-receipt');
                if (printReceipt) {
                    e.preventDefault();
                    e.stopPropagation(); // Stop event from bubbling up to dropdown
                    const saleId = printReceipt.dataset.id;

                    // First check if user can print
                    fetch(`sales.php?action=check_print_limit&sale_id=${saleId}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            if (!data.data.can_print) {
                                const printLimitModal = new bootstrap.Modal(document.getElementById('printLimitModal'));
                                printLimitModal.show();
                                return;
                            }

                            // If can print, proceed with fetching sale details
                            fetch(`sales.php?action=get_sale_details&sale_id=${saleId}`, {
                                method: 'GET',
                                headers: { 'X-Requested-With': 'XMLHttpRequest' }
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    const sale = data.data;
                                    const items = sale.items || [];
                                    let subtotal = 0;

                                    // Set header info
                                    setTextContent('transactionNumber', sale.sale_id);
                                    setTextContent('orNumber', sale.or_number || '');
                                    setTextContent('receiptDate', sale.recorded_at);
                                    setTextContent('receiptProcessedBy', sale.username || '');
                                    document.getElementById('receiptProcessedByRow').style.display = 'block';

                                    // Populate items
                                    const receiptTableItems = document.getElementById('receiptTableItems');
                                    receiptTableItems.innerHTML = '';
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
                                    const amountPaid = parseFloat(sale.amount_paid || sale.total || 0);
                                    const change = parseFloat(sale.change_given || (amountPaid - totalWithVAT));

                                    // Set totals
                                    setTextContent('receiptSubtotal', `₱${subtotal.toFixed(2)}`);
                                    setTextContent('receiptVAT', `₱${vat.toFixed(2)}`);
                                    setTextContent('receiptTotalAmount', `₱${totalWithVAT.toFixed(2)}`);
                                    setTextContent('receiptAmountPaid', `₱${amountPaid.toFixed(2)}`);
                                    setTextContent('receiptChange', `₱${change.toFixed(2)}`);

                                    // Print
                                    const printArea = document.getElementById('printArea');
                                    const printWindow = window.open('', '_blank');
                                    printWindow.document.write(`
                                        <html>
                                            <head>
                                                <title>Receipt</title>
                                                <style>
                                                    /* ... existing receipt styles ... */
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

                                    // Record the print after successful printing
                                    fetch(`sales.php?action=record_print&sale_id=${saleId}`, {
                                        method: 'GET',
                                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                                    })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (!data.success) {
                                            console.error('Failed to record print:', data.message);
                                        }
                                    })
                                    .catch(error => {
                                        console.error('Error recording print:', error);
                                    });
                                } else {
                                    showAlert('danger', data.message || 'Failed to fetch sale details for receipt.');
                                }
                            })
                            .catch(error => {
                                console.error('Print Receipt Error:', error);
                                showAlert('danger', 'Error fetching sale details for receipt.');
                            });
                        } else {
                            showAlert('danger', data.message || 'Failed to check print limit.');
                        }
                    })
                    .catch(error => {
                        console.error('Check Print Limit Error:', error);
                        showAlert('danger', 'Error checking print limit.');
                    });
                }
            });

            // Void sale
            document.addEventListener('click', function (e) {
                const voidSale = e.target.closest('.void-sale');
                if (voidSale) {
                    e.preventDefault();
                    const saleId = voidSale.dataset.id;
                    document.getElementById('voidSaleId').value = saleId;
                    const modal = new bootstrap.Modal(document.getElementById('voidConfirmationModal'));
                    modal.show();
                }
            });

            // Confirm void sale
            document.getElementById('confirmVoidSale').addEventListener('click', function () {
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
                            // Refresh the sales data
                        fetchSalesData('Completed').then(() => fetchSalesData('Voided'));
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

            // Complete sale
            document.addEventListener('click', function (e) {
                const completeSale = e.target.closest('.complete-sale');
                if (completeSale) {
                    e.preventDefault();
                    const saleId = completeSale.dataset.id;
                    document.getElementById('completeSaleId').value = saleId;
                    const modal = new bootstrap.Modal(document.getElementById('completeConfirmationModal'));
                    modal.show();
                }
            });

            // Confirm complete sale
            document.getElementById('confirmCompleteSale').addEventListener('click', function () {
                const saleId = document.getElementById('completeSaleId').value;
                const alertElement = document.getElementById('completeModalAlert');
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
                            // Refresh the sales data
                        fetchSalesData('Completed').then(() => fetchSalesData('Voided'));
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

            // Initialize dropdowns on page load
            initializeDropdowns();

            // Fetch initial sales data
            fetchSalesData('Completed');
            <?php if ($user['role'] === 'admin'): ?>
            fetchSalesData('Voided');
            <?php endif; ?>

            // Auto-refresh sales data every 30 seconds
            setInterval(() => {
                fetchSalesData('Completed');
                <?php if ($user['role'] === 'admin'): ?>
                fetchSalesData('Voided');
                <?php endif; ?>
            }, 30000);

            // Add event listeners to clear alerts when modals are closed
            document.getElementById('voidConfirmationModal').addEventListener('hidden.bs.modal', function () {
                const alertElement = document.getElementById('voidModalAlert');
                alertElement.classList.add('d-none');
                alertElement.classList.remove('alert-success', 'alert-danger');
                const confirmButton = document.getElementById('confirmVoidSale');
                confirmButton.disabled = false;
                confirmButton.innerHTML = 'Void Sale';
            });

            document.getElementById('completeConfirmationModal').addEventListener('hidden.bs.modal', function () {
                const alertElement = document.getElementById('completeModalAlert');
                alertElement.classList.add('d-none');
                alertElement.classList.remove('alert-success', 'alert-danger');
                const confirmButton = document.getElementById('confirmCompleteSale');
                confirmButton.disabled = false;
                confirmButton.innerHTML = 'Complete Sale';
            });

            // Add touch event handling for mobile
            document.addEventListener('DOMContentLoaded', function() {
                // Handle touch events for dropdowns on mobile
                const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
                dropdownToggles.forEach(toggle => {
                    toggle.addEventListener('touchstart', function(e) {
                        e.preventDefault();
                        const dropdown = bootstrap.Dropdown.getInstance(this);
                        if (dropdown) {
                            dropdown.toggle();
                        }
                    });
                });

                // Adjust table column visibility based on screen size
                function adjustTableColumns() {
                    const tables = document.querySelectorAll('.table-responsive');
                    tables.forEach(table => {
                        const isMobile = window.innerWidth <= 768;
                        const cells = table.querySelectorAll('td, th');
                        cells.forEach(cell => {
                            if (isMobile) {
                                cell.style.display = cell.classList.contains('options-cell') ? 'flex' : 'block';
                            } else {
                                cell.style.display = '';
                            }
                        });
                    });
                }

                // Call on load and resize
                adjustTableColumns();
                window.addEventListener('resize', adjustTableColumns);

                // Handle modal positioning on mobile
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modal => {
                    modal.addEventListener('show.bs.modal', function() {
                        if (window.innerWidth <= 576) {
                            this.style.paddingLeft = '0';
                            this.style.paddingRight = '0';
                        }
                    });
                });
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
        });

        // Initialize flatpickr for date inputs
        flatpickr(".flatpickr-input", {
            dateFormat: "Y-m-d",
            maxDate: "today",
            allowInput: true
        });

        // Update transactions tab text based on filter
        function updateTransactionsTabText() {
            const urlParams = new URLSearchParams(window.location.search);
            const filter = urlParams.get('filter') || 'Daily';
            const transactionsTabText = document.querySelector('.card-title');
            
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

        // Apply custom date range
        document.getElementById('applyCustomRange').addEventListener('click', function() {
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

        // Initial update of transactions tab text
        updateTransactionsTabText();

        // Sidebar toggle logic
        function updateSidebarState() {
            const $sidebar = $('.sidebar');
            const $content = $('#content');
            const isMobile = window.innerWidth <= 768;

            if (isMobile) {
                // Mobile view
                if ($sidebar.hasClass('active')) {
                    $sidebar.css('transform', 'translateX(0)');
                    $content.css('margin-left', '0');
                } else {
                    $sidebar.css('transform', 'translateX(-100%)');
                    $content.css('margin-left', '0');
                }
            } else {
                // Desktop view
                if ($sidebar.hasClass('collapsed')) {
                    $sidebar.css('transform', 'none');
                    $content.css('margin-left', 'var(--sidebar-collapsed-width)');
                } else {
                    $sidebar.css('transform', 'none');
                    $content.css('margin-left', 'var(--sidebar-width)');
                }
            }
        }

        // Toggle sidebar on button click
        $('#sidebarCollapseSidebar, #sidebarCollapseNavbar').on('click', function() {
            const $sidebar = $('.sidebar');
            const isMobile = window.innerWidth <= 768;

            if (isMobile) {
                $sidebar.toggleClass('active');
                if ($sidebar.hasClass('active')) {
                    $('#sidebarOverlay').show();
                } else {
                    $('#sidebarOverlay').hide();
                }
            } else {
                $sidebar.toggleClass('collapsed');
            }

            updateSidebarState();
        });

        // Update sidebar state on window resize
        $(window).on('resize', updateSidebarState);

        // Initial sidebar state
        $(document).ready(function() {
            updateSidebarState();
        });
    </script>
</body>
</html>