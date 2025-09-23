<?php
require_once 'config/headers.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Fruit Inventory</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <!-- Bootstrap Datepicker CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-datepicker@1.10.0/dist/css/bootstrap-datepicker.min.css">
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <!-- Bootstrap JS and dependencies -->
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.min.js"></script>
    <!-- Bootstrap Datepicker JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap-datepicker@1.10.0/dist/js/bootstrap-datepicker.min.js"></script>
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
            padding-top: 0;
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

        @media (max-width: 900px) {
            #content {
                padding: 0.75rem;
            }
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
                top: 0 left: 0 right: 0 bottom: 0;
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

        @media (max-width: 600px) {
            html, body {
                font-size: 0.88rem !important;
            }
            h2 {
                font-size: 1.05rem !important;
                margin-bottom: 0.35rem;
            }
            h5 {
                font-size: 0.98rem !important;
                margin-bottom: 0.3rem;
            }
            .navbar, .navbar .container-fluid {
                min-height: 36px !important;
                padding: 0.2rem 0.3rem !important;
                gap: 0;
            }
            .navbar .input-group.search-bar {
                margin: 0.2rem 0 0.2rem 0;
            }
            .navbar .input-group .form-control {
                font-size: 0.9rem;
                padding: 0.2rem 0.4rem;
                height: 32px;
                border-radius: 0.35rem 0 0 0.35rem;
            }
            .navbar .input-group .btn {
                font-size: 0.9rem;
                padding: 0.2rem 0.5rem;
                height: 32px;
                border-radius: 0 0.35rem 0.35rem 0;
            }
            .form-select, select.form-select {
                font-size: 0.9rem;
                padding: 0.2rem 0.4rem;
                height: 32px;
                border-radius: 0.35rem;
                min-width: 100%;
                max-width: 100%;
            }
            .dropdown-menu {
                min-width: 90vw !important;
                font-size: 0.9rem;
                border-radius: 0.35rem;
            }
            .dropdown-item {
                min-height: 32px;
                font-size: 0.9rem;
                padding: 0.4rem 0.6rem;
            }
            .modal-dialog {
                max-width: 98vw !important;
                margin: 0.2rem auto !important;
            }
            .modal-content {
                border-radius: 0.35rem;
                padding: 0.2rem 0.2rem 0.5rem 0.2rem;
                max-height: 90vh;
                overflow-y: auto;
            }
            .modal-header, .modal-body, .modal-footer {
                padding-left: 0.2rem !important;
                padding-right: 0.2rem !important;
            }
            .modal .form-select, .modal .form-control {
                font-size: 0.9rem;
                padding: 0.2rem 0.4rem;
                height: 32px;
                border-radius: 0.35rem;
                min-width: 100%;
                max-width: 100%;
                margin-bottom: 0.2rem;
            }
            .modal .btn {
                font-size: 0.9rem;
                min-height: 32px;
                width: 100%;
                margin-bottom: 0.2rem;
                border-radius: 0.35rem;
            }
            #inventoryTable, .table {
                display: block;
                width: 100%;
                border: none;
                background: none;
            }
            #inventoryTable thead, #inventoryTable tfoot, .table thead, .table tfoot {
                display: none;
            }
            #inventoryTable tbody, .table tbody {
                display: flex;
                flex-direction: column;
                gap: 0.3rem;
            }
            #inventoryTable tr, .table tr {
                display: table-row;
                flex-direction: unset;
                background: #fff;
                border-radius: 0.35rem;
                box-shadow: 0 1px 2px rgba(0,0,0,0.02);
                padding: 0.35rem 0.4rem;
                margin-bottom: 0.2rem;
                border: 1px solid #f0f0f0;
                width: 100%;
                min-width: 0;
            }
            #inventoryTable td, .table td {
                display: flex;
                align-items: center;
                font-size: 0.9rem;
                padding: 0.08rem 0;
                border: none;
                width: 100%;
                word-break: break-word;
            }
            #inventoryTable td:first-child, .table td:first-child {
                font-weight: 600;
                color: var(--primary);
                font-size: 0.98rem;
            }
            .stock-value {
                font-size: 0.9rem;
                font-weight: 500;
                margin-left: 0.2rem;
            }
            .badge {
                font-size: 0.88rem;
                padding: 0.2em 0.4em;
                border-radius: 0.35rem;
            }
            .btn, .form-control, .form-select, .dropdown-item, .nav-link {
                min-height: 32px;
                font-size: 0.9rem;
                border-radius: 0.35rem;
            }
            .card-body, .card {
                padding: 0.4rem !important;
                border-radius: 0.35rem;
            }
            .text-muted {
                font-size: 0.88rem;
            }
        }
        /* Touch targets and accessibility */
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
        img {
            max-width: 100%;
            height: auto;
            border-radius: 0.5rem;
        }
        .table-responsive {
            -webkit-overflow-scrolling: touch;
        }
        .table th, .table td {
            padding: 0.75rem;
            font-size: 1rem;
            word-break: break-word;
        }
        @media (max-width: 600px) {
            .table th, .table td {
                padding: 0.5rem;
                font-size: 0.95rem;
            }
            .table td {
                max-width: 10rem;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
        }
        .card {
            border-radius: var(--radius);
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: var(--gap);
        }
        .card-title {
            font-size: clamp(1.1rem, 2vw, 1.3rem);
            font-weight: 600;
        }
        .card-text {
            font-size: 1rem;
        }
        .badge {
            font-size: 0.95rem;
            padding: 0.4em 0.8em;
            border-radius: 0.5rem;
        }
        /* Accessibility: high contrast for important elements */
        .badge.bg-success, .badge.bg-danger {
            color: #fff !important;
        }
        /* Responsive modal centering */
        @media (max-width: 600px) {
            .modal-dialog {
                max-width: 98vw !important;
                margin: 0.5rem auto !important;
            }
        }
        /* Remove outline for mouse users, keep for keyboard */
        :focus:not(:focus-visible) {
            outline: none;
            box-shadow: none;
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

        @media (max-width: 768px) {
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
        }

        @media (max-width: 576px) {
            .navbar {
                padding: 8px 6px;
                border-radius: 0 0 12px 12px;
            }
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
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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

        .product-card {
            border: none;
            border-radius: 12px;
            background: #fff;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
            display: flex;
            flex-direction: column;
        }

        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }

        .product-card .product-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 12px 12px 0 0;
        }

        .product-card .card-body {
            padding: 20px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }

        .product-card .card-title {
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 1rem;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .product-card .card-text {
            margin-bottom: 0.75rem;
            font-size: 1rem;
            color: #495057;
        }

        .product-card .card-text.text-muted {
            font-size: 0.875rem;
            color: #6c757d;
        }

        .product-card .badge {
            font-size: 0.875rem;
            padding: 0.5em 1em;
        }

        .modal-content {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            max-height: 100vh;
            overflow-y: auto;
            width: 110%;
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
            font-weight: 500;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            background: #b71c1c;
            transform: translateY(-1px);
        }

        .btn-outline-secondary {
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .btn-danger {
            background: var(--danger);
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .btn-danger:hover {
            background: #a31515;
            transform: translateY(-1px);
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

        .nav-tabs {
            border: none;
            background: #fff;
            border-radius: 12px;
            padding: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .nav-tabs .nav-link {
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            color: #495057;
            font-weight: 500;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .nav-tabs .nav-link.active {
            background: var(--primary);
            color: #fff;
        }

        .nav-tabs .nav-link:hover {
            background: var(--primary-light);
            color: var(--primary);
        }

        .form-control, .form-select {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .form-control:focus, .form-select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .flatpickr-input {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            padding: 0.75rem;
            font-size: 1rem;
            width: 100%;
            max-width: 200px;
        }

        .flatpickr-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
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

        .sortable {
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .sortable:hover {
            background: #e9ecef;
        }

        .sort-icon {
            margin-left: 5px;
        }

        .sort-asc .sort-icon::before {
            content: '\f144';
            font-family: 'bootstrap-icons';
        }

        .sort-desc .sort-icon::before {
            content: '\f140';
            font-family: 'bootstrap-icons';
        }

        .search-loading, .sort-loading {
            display: none;
            margin-left: 10px;
        }

        .search-loading.active, .sort-loading.active {
            display: inline-block;
        }

        .dropdown-menu {
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            font-size: 1rem;
        }

        .dropdown-item {
            padding: 0.5rem 1rem;
            font-size: 1rem;
        }

        .dropdown-item:hover {
            background: var(--primary-light);
            color: var(--primary);
        }

        h5 {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .text-muted {
            font-size: 0.875rem;
        }

        .fruit-name {
            text-transform: capitalize;
        }

        @media (max-width: 768px) {
            .search-bar {
                max-width: 100%;
            }
            .product-card .card-body {
                padding: 15px;
            }
            .product-card .product-image {
                height: 180px;
            }
        }

        @media (max-width: 576px) {
            .product-card .product-image {
                height: 160px;
            }
            h2 {
                font-size: 1.75rem;
            }
        }
    </style>
    <style>
        .receipt-container {
            font-family: 'Courier New', Courier, monospace;
            max-width: 380px;
            margin: 20px auto;
            background: #fff;
            border: 1px solid #ccc;
            padding: 18px 18px 8px 18px;
            line-height: 1.4;
        }

        .receipt-header {
            text-align: center;
            margin-bottom: 12px;
        }

        .receipt-header img {
            margin-bottom: 4px;
            max-width: 80px;
            height: auto;
        }

        .receipt-header .company-name {
            font-weight: bold;
            font-size: 1.1em;
            margin: 4px 0;
        }

        .receipt-header .company-details {
            font-size: 0.95em;
            margin: 2px 0;
        }

        .receipt-title {
            text-align: center;
            font-weight: bold;
            margin: 8px 0 4px 0;
            font-size: 1.1em;
            letter-spacing: 1px;
        }

        .receipt-divider {
            margin: 6px 0;
            border-top: 1px dashed #000;
        }

        .receipt-info {
            font-size: 0.95em;
            margin-bottom: 2px;
            display: flex;
            justify-content: space-between;
        }

        .receipt-info-label {
            font-weight: bold;
            margin-right: 8px;
        }

        .receipt-table {
            width: 100%;
            font-size: 0.95em;
            border-collapse: collapse;
            margin: 6px 0;
        }

        .receipt-table th {
            text-align: left;
            padding: 2px 0;
            border-bottom: 1px solid #000;
        }

        .receipt-table td {
            padding: 2px 0;
        }

        .receipt-table .align-right {
            text-align: right;
        }

        .receipt-summary {
            font-size: 0.95em;
            margin: 6px 0;
        }

        .receipt-summary-row {
            display: flex;
            justify-content: space-between;
            margin: 2px 0;
        }

        .receipt-summary-row.total {
            font-weight: bold;
            margin-top: 4px;
        }

        .receipt-footer {
            font-size: 0.85em;
            text-align: center;
            margin-top: 8px;
        }

        .receipt-footer p {
            margin: 2px 0;
        }

        .receipt-cashier {
            margin: 8px 0;
            padding-top: 8px;
            border-top: 1px dashed #000;
            font-size: 0.95em;
            text-align: center;
        }

        .receipt-cashier .cashier-name {
            font-weight: bold;
            margin-top: 4px;
        }
    </style>
    <style>
      .wide-select { 
        min-width: 100%; 
        max-width: 100%;
      }
      @media (min-width: 768px) {
        .wide-select {
          min-width: 400px;
          max-width: 100%;
        }
      }
    </style>
    <style>
        /* Update the step indicator styles for better visibility */
        .sale-steps {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 1rem auto 1.5rem auto;
            position: relative;
            padding: 0 1rem;
            max-width: 350px;
            width: 100%;
        }

        .sale-step {
            position: relative;
            z-index: 2;
            background: #fff;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #e9ecef;
            color: #6c757d;
            font-weight: 600;
            font-size: 1.1rem;
            margin: 0 0.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.07);
            transition: all 0.3s ease;
        }

        .sale-step i {
            font-size: 1.1rem;
        }

        .sale-step-label {
            position: absolute;
            top: calc(100% + 0.25rem);
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.85rem;
            color: #6c757d;
            white-space: nowrap;
            font-weight: 500;
            min-width: 70px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .sale-step.active {
            background: var(--primary);
            border-color: var(--primary);
            color: #fff;
            transform: scale(1.08);
            box-shadow: 0 2px 6px rgba(211, 47, 47, 0.13);
        }

        .sale-step.completed {
            background: var(--success);
            border-color: var(--success);
            color: #fff;
            box-shadow: 0 1px 2px rgba(46, 125, 50, 0.13);
        }

        .sale-step.active .sale-step-label {
            color: var(--primary);
            font-weight: 600;
            transform: translateX(-50%) scale(1.05);
        }

        .sale-step.completed .sale-step-label {
            color: var(--success);
        }

        .sale-progress {
            position: absolute;
            top: 50%;
            left: 2.5rem;
            height: 3px;
            background: var(--primary);
            transform: translateY(-50%);
            z-index: 1;
            transition: width 0.3s ease;
            max-width: calc(100% - 5rem);
            box-shadow: 0 1px 2px rgba(211, 47, 47, 0.2);
        }

        /* Add a pulsing effect to the active step */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(211, 47, 47, 0); }
            100% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
        }

        .sale-step.active {
            animation: pulse 2s infinite;
        }

        /* Update modal header to accommodate the new step indicator */
        #buyModal .modal-header {
            flex-direction: column;
            align-items: stretch;
            padding: 1.5rem;
            background: linear-gradient(135deg, var(--primary-light), #fff);
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }

        #buyModal .modal-header .modal-title {
            margin-bottom: 0.5rem;
            color: var(--primary);
            font-weight: 600;
        }

        #buyModal .modal-header .btn-close {
            position: absolute;
            right: 1.5rem;
            top: 1.5rem;
            background-color: rgba(255,255,255,0.8);
            border-radius: 50%;
            padding: 0.5rem;
        }

        /* Add a visual indicator for the current step content */
        #saleStep1, #saleStep2, #saleStep3 {
            position: relative;
            padding: 1.5rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        #saleStep1.active, #saleStep2.active, #saleStep3.active {
            background: rgba(211, 47, 47, 0.05);
            border: 1px solid rgba(211, 47, 47, 0.1);
        }
    </style>
    <style>
        /* Add these styles for the payment step table */
        .payment-summary-table {
            width: 100%;
            max-width: 600px;
            margin: 1.5rem auto 2rem;
            border-radius: 8px;
            background: #ffffff;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            border: 1px solid #e8e8e8;
        }

        .payment-summary-table table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            table-layout: auto;
        }

        .payment-summary-table th,
        .payment-summary-table td {
            padding: 0.75rem 0.75rem;
            font-size: 0.95rem;
            line-height: 1.5;
            border-bottom: 1px solid #edf2f7;
            background: #ffffff;
            color: #2d3748;
            word-break: break-word;
            white-space: normal;
        }

        /* Ensure Description column wraps and doesn't force table to overflow */
        .payment-summary-table th:first-child,
        .payment-summary-table td:first-child {
            max-width: 220px;
            min-width: 120px;
            word-break: break-word;
            white-space: normal;
        }

        .payment-summary-table th {
            background: #f8fafc;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
            color: #4a5568;
            border-bottom: 2px solid #e2e8f0;
        }

        .payment-summary-table tr:last-child td {
            border-bottom: none;
        }

        .payment-summary-table tr:nth-child(even) td {
            background: #f8fafc;
        }

        /* Special styling for amount fields */
        .payment-summary-table td.amount {
            font-weight: 600;
            color: #2d3748;
            font-family: 'Segoe UI', system-ui, -apple-system, monospace;
        }

        /* Highlight important rows */
        .payment-summary-table tr.total-row td {
            background: #f1f5f9;
            font-weight: 600;
            color: #1a202c;
            border-top: 2px solid #e2e8f0;
        }

        /* Amount tendered field specific styling */
        .payment-summary-table tr.amount-tendered td {
            background: #edf2f7;
            font-weight: 600;
            color: #2b6cb0;
        }

        .payment-summary-table tr.amount-tendered input {
            background: #ffffff;
            border: 2px solid #e2e8f0;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            font-size: 1rem;
            font-weight: 600;
            color: #2b6cb0;
            width: 100%;
            max-width: 200px;
            transition: all 0.2s ease;
        }

        .payment-summary-table tr.amount-tendered input::placeholder {
            color: #a0aec0;
            font-weight: normal;
            font-style: normal !important;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
        }

        .payment-summary-table tr.amount-tendered input:focus {
            border-color: #4299e1;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
            outline: none;
        }

        .payment-summary-table tr.amount-tendered input:focus::placeholder {
            color: #cbd5e0;
        }
    </style>
    <style>
    /* Add these styles for the disabled button */
    #nextToStep2:disabled {
        cursor: not-allowed;
        opacity: 0.7;
    }

    #nextToStep2:disabled:hover {
        background-color: var(--bs-secondary);
        border-color: var(--bs-secondary);
    }

    /* Add a tooltip style for the button */
    #nextToStep2[title] {
        position: relative;
    }

    #nextToStep2[title]:hover::after {
        content: attr(title);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        padding: 5px 10px;
        background-color: rgba(0, 0, 0, 0.8);
        color: white;
        border-radius: 4px;
        font-size: 0.875rem;
        white-space: nowrap;
        z-index: 1000;
        margin-bottom: 5px;
    }
    </style>
    <style>
    /* Add these styles for the sale modal */
    .payment-summary-table {
        width: 100%;
        max-width: 500px;
        margin: 0 auto 2rem;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        background: #fff;
    }

    .payment-summary-table tr {
        transition: background-color 0.2s ease;
    }

    .payment-summary-table tr:hover {
        background-color: rgba(211, 47, 47, 0.02);
    }

    .payment-summary-table th {
        /* Remove red background and color */
        background: #f8f9fa;
        color: #212529;
        font-weight: 600;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid rgba(211, 47, 47, 0.1);
        width: 40%;
    }

    .payment-summary-table td {
        padding: 1rem;
        border-bottom: 1px solid rgba(0,0,0,0.05);
        font-weight: 500;
    }

    .payment-summary-table tr:last-child td {
        border-bottom: none;
    }

    .payment-summary-table .total-row {
        background: #f8f9fa;
    }

    .payment-summary-table .total-row td {
        font-weight: 600;
        color: #212529;
    }

    .payment-summary-table .amount-input {
        width: 180px;
        margin-left: auto;
        display: block;
        text-align: right; /* Align right instead of center */
        font-weight: 500;
        border: 2px solid rgba(211, 47, 47, 0.1);
        border-radius: 8px;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }

    .payment-summary-table .amount-input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px var(--primary-light);
    }

    .payment-summary-table .change-row td {
        font-weight: 600;
        color: var(--success);
    }

    .payment-summary-table .amount {
        font-family: 'Courier New', monospace;
        font-weight: 600;
    }

    .item-row {
        background: #fff;
        border-radius: 8px;
        transition: all 0.3s ease;
    }

    .item-row:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    #buyModal .modal-header {
        background: linear-gradient(135deg, var(--primary-light), #fff);
        border-bottom: 1px solid rgba(0,0,0,0.1);
    }

    #buyModal .modal-footer {
        border-top: 1px solid rgba(0,0,0,0.1);
        padding: 1rem;
    }

    #buyModal .btn {
        min-width: 120px;
    }

    #buyModal .step-indicator {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1.5rem auto;
        position: relative;
        padding: 0 2rem;
        max-width: 500px;
    }

    #buyModal .step {
        position: relative;
        z-index: 2;
        background: #fff;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #e9ecef;
        color: #6c757d;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    #buyModal .step.active {
        background: var(--primary);
        border-color: var(--primary);
        color: #fff;
    }

    #buyModal .step.completed {
        background: var(--success);
        border-color: var(--success);
        color: #fff;
    }

    #buyModal .step-label {
        position: absolute;
        top: calc(100% + 0.5rem);
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.875rem;
        color: #6c757d;
        white-space: nowrap;
    }

    #buyModal .step.active .step-label {
        color: var(--primary);
        font-weight: 600;
    }

    #buyModal .step.completed .step-label {
        color: var(--success);
    }

    #buyModal .step-progress {
        position: absolute;
        top: 50%;
        left: 2.5rem;
        right: 2.5rem;
        height: 2px;
        background: #e9ecef;
        transform: translateY(-50%);
        z-index: 1;
    }

    #buyModal .step-progress-bar {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: var(--primary);
        transition: width 0.3s ease;
    }
    </style>
    <style>
    /* Payment summary table UI updates */
    .payment-summary-table th,
    .payment-summary-table td,
    .payment-summary-table .amount,
    .payment-summary-table .total-row td,
    .payment-summary-table .change-row td {
        color: #212529 !important;
    }
    .payment-summary-table .amount-input {
        text-align: right;
        margin-left: auto;
        display: block;
    }
    </style>
    <style>
    .receipt-table th.align-right, .receipt-table td.align-right {
        padding-left: 16px !important;
        padding-right: 16px !important;
        min-width: 60px;
        text-align: right;
    }
    </style>
    <style>
        /* --- Improved Mobile Responsiveness --- */
        @media (max-width: 768px) {
            .wrapper {
                display: block;
                width: 100vw;
                min-height: 100vh;
            }
            .sidebar {
                display: none !important;
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
        }
    </style>
    <style>
    /* --- Mobile Modal & Dropdown Fixes --- */
    @media (max-width: 600px) {
      .modal-dialog {
        max-width: 98vw !important;
        margin: 0.5rem auto !important;
      }
      .modal-content {
        border-radius: 10px;
        padding: 0.5rem 0.5rem 1rem 0.5rem;
      }
      .modal-header, .modal-body, .modal-footer {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
      }
      select.form-select, .form-control, .input-group, .search-bar {
        font-size: 1rem !important;
        min-width: 0;
        width: 100% !important;
        box-sizing: border-box;
      }
      .form-label, label {
        font-size: 0.98rem;
      }
      .dropdown-menu {
        font-size: 1rem;
        min-width: 90vw;
        left: 0 !important;
        right: 0 !important;
      }
      .modal .btn, .modal .form-control, .modal .form-select {
        font-size: 1rem;
        min-height: 40px;
      }
    }

    /* --- Search Bar & Controls Stacking --- */
    @media (max-width: 600px) {
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

    /* --- Remove notification styling for 'At least one item is required.' --- */
    #alertContainer .alert-warning:has(:contains('At least one item is required.')) {
      display: none !important;
    }
    </style>
    <style>
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

    /* --- Sidebar as Overlay/Drawer on Mobile --- */
    @media (max-width: 768px) {
      .sidebar {
        display: block !important;
        position: fixed;
        left: 0;
        top: 0;
        height: 100vh;
        width: var(--sidebar-width);
        max-width: 80vw;
        z-index: 2000;
        background: var(--dark);
        transform: translateX(-100%);
        transition: transform 0.3s cubic-bezier(.4,0,.2,1);
        box-shadow: 2px 0 10px rgba(0,0,0,0.2);
      }
      .sidebar.active {
        transform: translateX(0);
      }
      #sidebarOverlay {
        display: none;
        position: fixed;
        top: 0 left: 0 right: 0 bottom: 0;
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

    /* --- Compact Select Dropdown in Modal --- */
    @media (max-width: 600px) {
      .modal-content {
        padding: 0.5rem 0.5rem 1rem 0.5rem;
      }
      .modal .form-select, select.form-select {
        font-size: 0.98rem;
        padding: 0.4rem 0.6rem;
        height: 38px;
        border-radius: 6px;
        max-width: 100%;
      }
      .modal .dropdown-menu, .modal select.form-select {
        font-size: 0.98rem;
        max-width: 95vw;
      }
    }
    </style>
    <style>
    /* --- Mobile-First Redesign (except sidebar) --- */
    @media (max-width: 600px) {
      /* Header (navbar) */
      .navbar {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 0;
        box-shadow: none;
        background: #fff;
        gap: 0;
        min-height: 56px;
      }
      .navbar .container-fluid {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 0;
        padding: 0;
        width: 100%;
      }
      .navbar .input-group.search-bar {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0.5rem 0 0.5rem 0;
        flex-direction: row;
        gap: 0;
      }
      .navbar .input-group .form-control {
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        height: 44px;
        border-radius: 0.5rem 0 0 0.5rem;
      }
      .navbar .input-group .btn {
        font-size: 1rem;
        padding: 0.5rem 1rem;
        height: 44px;
        border-radius: 0 0.5rem 0.5rem 0;
      }
      .navbar .dropdown,
      .navbar .dropdown-menu {
        width: 100% !important;
        max-width: 100% !important;
        margin-bottom: 0.5rem;
      }
      .navbar img.rounded-circle {
        width: 2rem;
        height: 2rem;
      }
      /* Dropdowns: native select, large tap targets */
      .form-select, select.form-select {
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        height: 44px;
        border-radius: 0.5rem;
        min-width: 100%;
        max-width: 100%;
        background-size: 1.2rem 1.2rem;
      }
      .dropdown-menu {
        min-width: 90vw !important;
        font-size: 1rem;
        border-radius: 0.5rem;
      }
      .dropdown-item {
        min-height: 44px;
        font-size: 1rem;
        padding: 0.75rem 1rem;
      }
      /* Modals: edge-to-edge, minimal padding, scrollable */
      .modal-dialog {
        max-width: 95vw !important;
        margin: 0.5rem auto !important;
      }
      .modal-content {
        border-radius: 0.75rem;
        padding: 0.5rem 0.5rem 1rem 0.5rem;
        max-height: 95vh;
        overflow-y: auto;
      }
      .modal-header, .modal-body, .modal-footer {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
      }
      .modal .form-select, .modal .form-control {
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        height: 44px;
        border-radius: 0.5rem;
        min-width: 100%;
        max-width: 100%;
        margin-bottom: 0.5rem;
      }
      .modal .btn {
        font-size: 1rem;
        min-height: 44px;
        width: 100%;
        margin-bottom: 0.5rem;
      }
      /* Inventory List: card/list view */
      #inventoryTable, .table {
        display: block;
        width: 100%;
        border: none;
        background: none;
      }
      #inventoryTable thead, #inventoryTable tfoot, .table thead, .table tfoot {
        display: none;
      }
      #inventoryTable tbody, .table tbody {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }
      #inventoryTable tr, .table tr {
        display: table-row;
        flex-direction: unset;
        background: #fff;
        border-radius: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #f0f0f0;
        width: 100%;
        min-width: 0;
      }
      #inventoryTable td, .table td {
        display: flex;
        align-items: center;
        font-size: 1rem;
        padding: 0.25rem 0;
        border: none;
        width: 100%;
        word-break: break-word;
      }
      #inventoryTable td:first-child, .table td:first-child {
        font-weight: 600;
        color: var(--primary);
        font-size: 1.1rem;
      }
      .stock-value {
        font-size: 1rem;
        font-weight: 500;
        margin-left: 0.5rem;
      }
      .badge {
        font-size: 0.95rem;
        padding: 0.4em 0.8em;
        border-radius: 0.5rem;
      }
      /* General touch targets and spacing */
      .btn, .form-control, .form-select, .dropdown-item, .nav-link {
        min-height: 44px;
        font-size: 1rem;
        border-radius: 0.5rem;
      }
      .card-body, .card {
        padding: 1rem !important;
        border-radius: 0.75rem;
      }
      h2 {
        font-size: 1.2rem;
      }
      h5 {
        font-size: 1.1rem;
      }
      .text-muted {
        font-size: 0.95rem;
      }
    }
    </style>
    <style>
    .navbar .dropdown .nav-link img.rounded-circle {
        width: 40px !important;
        height: 40px !important;
        aspect-ratio: 1/1;
        object-fit: cover;
        border-radius: 50%;
        border: 2px solid #dee2e6;
        background: #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    </style>
    <style>
    .payment-summary-table table {
        table-layout: auto !important;
        width: 100%;
    }
    .payment-summary-table th,
    .payment-summary-table td {
        white-space: nowrap;
        vertical-align: middle;
        text-align: left;
    }
    .payment-summary-table th.text-end,
    .payment-summary-table td.text-end {
        text-align: right;
    }
    .payment-summary-table td.amount,
    .payment-summary-table th.amount {
        text-align: right;
        font-family: 'Roboto Mono', monospace;
    }
    .payment-summary-table td {
        word-break: break-word;
    }
    </style>
    <style>
    /* Make Quantity column compact and centered */
    .payment-summary-table th.quantity-col,
    .payment-summary-table td.quantity-col {
        width: 80px;
        min-width: 60px;
        max-width: 100px;
        text-align: center !important;
        font-size: 0.95em;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    /* Apply the class to all Quantity cells */
    .payment-summary-table td.quantity-col {
        vertical-align: middle;
    }
    /* Make Price column compact and centered */
    .payment-summary-table th.price-col,
    .payment-summary-table td.price-col {
        width: 110px;
        min-width: 80px;
        max-width: 130px;
        text-align: center !important;
        font-size: 0.95em;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    .payment-summary-table td.price-col {
        vertical-align: middle;
    }
    </style>
    <style>
        /* ...existing styles... */
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
    </style>
    <style>
    /* Status Modal Styles */
    #statusConfirmModal .modal-content {
        border: none;
        border-radius: 15px;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }

    #statusConfirmModal .modal-header {
        background-color: #f8f9fa;
        border-radius: 15px 15px 0 0;
        padding: 1.5rem 1.5rem 0.5rem;
    }

    #statusConfirmModal .modal-body {
        padding: 1.5rem;
    }

    #statusConfirmModal .modal-footer {
        background-color: #f8f9fa;
        border-radius: 0 0 15px 15px;
        padding: 1rem 1.5rem 1.5rem;
    }

    #statusConfirmModal .status-icon {
        margin: 1rem auto;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #fff3cd;
    }

    #statusConfirmModal .status-icon i {
        font-size: 3rem;
        color: #ffc107;
    }

    #statusConfirmModal .status-details {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.25rem;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }

    #statusConfirmModal .status-details p {
        margin-bottom: 0.75rem;
        font-size: 0.95rem;
    }

    #statusConfirmModal .status-details p:last-child {
        margin-bottom: 0;
    }

    #statusConfirmModal .btn {
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        border-radius: 8px;
        transition: all 0.2s;
        min-width: 140px;
    }

    #statusConfirmModal .btn-light {
        background-color: #e9ecef;
        border-color: #e9ecef;
    }

    #statusConfirmModal .btn-light:hover {
        background-color: #dee2e6;
        border-color: #dee2e6;
    }

    #statusConfirmModal .alert {
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border: none;
    }

    #statusConfirmModal .alert-success {
        background-color: #d1e7dd;
        color: #0f5132;
    }

    #statusConfirmModal .alert-danger {
        background-color: #f8d7da;
        color: #842029;
    }

    #statusConfirmModal .alert i {
        font-size: 1.25rem;
        margin-right: 0.75rem;
    }

    #statusConfirmModal .alert .d-flex {
        align-items: flex-start;
    }

    #statusConfirmModal .alert strong {
        display: block;
        margin-bottom: 0.25rem;
    }
    </style>

    <style>
        .modal-dialog {
            margin: 0.5rem;
            max-width: 100%;
            width: auto;
        }

        @media (min-width: 576px) {
            .modal-dialog {
                margin: 1.75rem auto;
                max-width: 500px;
            }
            .modal-dialog.modal-lg {
                max-width: 800px;
            }
            .modal-dialog.modal-xl {
                max-width: 1140px;
            }
        }

        /* Ensure modals don't overflow on mobile */
        .modal {
            padding-right: 0 !important;
        }

        .modal-content {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            max-height: calc(100vh - 2rem);
            overflow-y: auto;
            width: 100%;
            margin: 0 auto;
        }

        /* Modal header and footer spacing */
        .modal-header {
            padding: 1rem;
            border-bottom: 1px solid rgba(0,0,0,0.1);
            background: linear-gradient(135deg, var(--primary-light), #fff);
            position: sticky;
            top: 0;
            z-index: 1;
        }

        .modal-footer {
            padding: 1rem;
            border-top: 1px solid rgba(0,0,0,0.1);
            background: #fff;
            position: sticky;
            bottom: 0;
            z-index: 1;
        }

        .modal-body {
            padding: 1rem;
            overflow-y: auto;
        }

        /* Specific modal adjustments */
        #productModal .modal-body,
        #buyModal .modal-body,
        #addStockModal .modal-body,
        #stockDetailsModal .modal-body {
            padding: 1rem;
        }

        /* Form elements in modals */
        .modal .form-control,
        .modal .form-select {
            font-size: 1rem;
            padding: 0.5rem 0.75rem;
        }

        .modal .btn {
            padding: 0.5rem 1rem;
            font-size: 1rem;
        }

        /* Table responsiveness in modals */
        .modal .table-responsive {
            margin: 0 -1rem;
            padding: 0 1rem;
            width: calc(100% + 2rem);
        }

        /* Status confirmation modal specific styles */
        #statusConfirmModal .modal-dialog {
            max-width: 400px;
        }

        #statusConfirmModal .status-details {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #e9ecef;
        }

        /* Stock details modal specific styles */
        #stockDetailsModal .modal-dialog {
            max-width: 800px;
        }

        #stockDetailsModal .table {
            margin-bottom: 0;
        }

        /* Buy modal specific styles */
        #buyModal .sale-steps {
            margin: 0 -1rem 1rem;
            padding: 1rem;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }

        /* Add stock modal specific styles */
        #addStockModal .stock-items-container {
            max-height: 60vh;
            overflow-y: auto;
        }

        /* Ensure dropdowns in modals don't get cut off */
        .modal .dropdown-menu {
            max-width: 100%;
            width: max-content;
            min-width: 200px;
        }

        /* Ensure alerts in modals are properly styled */
        .modal .alert {
            margin: 0 0 1rem;
            border-radius: 8px;
        }

        /* Ensure buttons in modal footer are properly spaced */
        .modal-footer .btn {
            margin-left: 0.5rem;
        }

        .modal-footer .btn:first-child {
            margin-left: 0;
        }

        /* Ensure modals with forms have proper spacing */
        .modal form {
            margin-bottom: 0;
        }

        .modal .form-group {
            margin-bottom: 1rem;
        }

        /* Ensure modals with tables have proper scrolling */
        .modal .table-responsive {
            max-height: 60vh;
            overflow-y: auto;
        }

        /* Ensure modals with images have proper sizing */
        .modal img {
            max-width: 100%;
            height: auto;
        }

        /* Ensure modals with long content don't break layout */
        .modal .long-content {
            word-break: break-word;
            overflow-wrap: break-word;
        }

        /* Ensure modals with multiple buttons are properly aligned */
        .modal .btn-group {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        /* Ensure modals with icons have proper alignment */
        .modal .bi {
            vertical-align: -0.125em;
        }

        /* Ensure modals with badges have proper spacing */
        .modal .badge {
            margin: 0 0.25rem;
        }

        /* Ensure modals with tooltips don't get cut off */
        .modal .tooltip {
            z-index: 1070;
        }

        /* Ensure modals with popovers don't get cut off */
        .modal .popover {
            z-index: 1070;
        }

        /* Ensure modals with datepickers don't get cut off */
        .modal .datepicker {
            z-index: 1070;
        }

        /* Ensure modals with select2 dropdowns don't get cut off */
        .modal .select2-container {
            z-index: 1070;
        }

        /* Ensure modals with autocomplete dropdowns don't get cut off */
        .modal .autocomplete-container {
            z-index: 1070;
        }

        /* Ensure modals with file inputs have proper styling */
        .modal .custom-file {
            margin-bottom: 1rem;
        }

        /* Ensure modals with checkboxes and radios have proper spacing */
        .modal .form-check {
            margin-bottom: 0.5rem;
        }

        /* Ensure modals with input groups have proper alignment */
        .modal .input-group {
            flex-wrap: nowrap;
        }

        /* Ensure modals with validation feedback have proper positioning */
        .modal .invalid-feedback {
            position: static;
            margin-top: 0.25rem;
        }

        /* Ensure modals with loading spinners have proper centering */
        .modal .spinner-border {
            vertical-align: middle;
        }

        /* Ensure modals with progress bars have proper spacing */
        .modal .progress {
            margin-bottom: 1rem;
        }

        /* Ensure modals with tabs have proper styling */
        .modal .nav-tabs {
            margin-bottom: 1rem;
        }

        /* Ensure modals with accordions have proper spacing */
        .modal .accordion {
            margin-bottom: 1rem;
        }

        /* Ensure modals with cards have proper spacing */
        .modal .card {
            margin-bottom: 1rem;
        }

        /* Ensure modals with lists have proper spacing */
        .modal .list-group {
            margin-bottom: 1rem;
        }

        /* Ensure modals with pagination have proper alignment */
        .modal .pagination {
            justify-content: center;
            margin-bottom: 0;
        }

        /* Ensure modals with breadcrumbs have proper spacing */
        .modal .breadcrumb {
            margin-bottom: 1rem;
        }

        /* Ensure modals with alerts have proper stacking */
        .modal .alert + .alert {
            margin-top: 1rem;
        }

        /* Ensure modals with buttons have proper stacking on mobile */
        @media (max-width: 575.98px) {
            .modal-footer {
                flex-direction: column;
                gap: 0.5rem;
            }
            .modal-footer .btn {
                width: 100%;
                margin: 0;
            }
            .modal .btn-group {
                width: 100%;
            }
            .modal .btn-group .btn {
                flex: 1;
            }
        }
    </style>

    <style>
        @media (max-width: 600px) {
            /* Dropdowns in modals */
            .modal .dropdown-menu {
                left: 0 !important;
                right: 0 !important;
                min-width: 100vw !important;
                max-width: 100vw !important;
                width: 100vw !important;
                border-radius: 0 0 10px 10px;
                margin-left: -16px !important;
            }
            /* Select fields */
            .modal .form-select,
            .modal select.form-select {
                width: 100% !important;
                min-width: 0 !important;
                max-width: 100% !important;
            }
            /* Date fields in modals */
            .modal input[type="text"],
            .modal input[type="date"],
            .modal input[type="datetime-local"] {
                width: 100% !important;
                min-width: 0 !important;
                max-width: 100% !important;
                font-size: 1rem;
                box-sizing: border-box;
            }
            /* Receipt container in modal */
            .modal .receipt-container {
                width: 100% !important;
                max-width: 100% !important;
                overflow-x: auto;
                padding: 0.5rem !important;
            }
            .modal .receipt-table {
                width: 100% !important;
                min-width: 0 !important;
                font-size: 0.95rem !important;
                word-break: break-word;
            }
            .modal .receipt-table th,
            .modal .receipt-table td {
                white-space: normal !important;
                word-break: break-word !important;
                padding-left: 2px !important;
                padding-right: 2px !important;
            }
        }
    </style>
    <style>
    @media (min-width: 601px) {
      /* Center the step indicator and keep it compact */
      .sale-steps, #buyModal .sale-steps {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        max-width: 400px;
        margin: 0 auto 1.5rem auto;
        width: auto;
        padding: 0;
        box-sizing: border-box;
        background: none !important;
        border: none !important;
      }
      .sale-step, #buyModal .sale-step {
        min-width: 48px;
        max-width: 64px;
        height: 48px;
        flex: none;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 0;
      }
      .sale-step i, #buyModal .sale-step i {
        font-size: 1.5rem;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.25rem auto;
      }
      /* Date fields in modals: compact width for desktop */
      .modal input#purchaseDate,
      .modal input#stockDateDisplay {
        max-width: 180px;
        width: 180px;
        display: inline-block;
      }
    }

    @media (max-width: 600px) {
      /* Remove all backgrounds, borders, and box-shadows from step indicator and parents */
      .sale-steps, #buyModal .sale-steps,
      .sale-steps *, #buyModal .sale-steps *,
      .sale-steps > *, #buyModal .sale-steps > *,
      .sale-steps:before, .sale-steps:after,
      #buyModal .sale-steps:before, #buyModal .sale-steps:after {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
      }
      .sale-steps, #buyModal .sale-steps {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 1.2rem !important;
        max-width: 95vw !important;
        margin: 0 auto 1.2rem auto !important;
        width: auto !important;
        padding: 0 !important;
        box-sizing: border-box !important;
      }
      .sale-step, #buyModal .sale-step {
        min-width: 48px !important;
        max-width: 64px !important;
        height: 48px !important;
        flex: none !important;
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
      }
      .sale-step i, #buyModal .sale-step i {
        font-size: 1.5rem !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto 0.25rem auto !important;
      }
    }
    </style>
    <style>
    /* Restore red background for active step indicator on mobile */
    @media (max-width: 600px) {
      /* Restore red background for active step indicator on mobile */
      .sale-step.active, #buyModal .sale-step.active {
        background: var(--primary) !important;
        color: #fff !important;
        border: 2px solid var(--primary) !important;
      }
    }
    </style>
    <style>
    /* --- Mobile Table & Card Overflow Fixes --- */
    @media (max-width: 600px) {
      /* Inventory table cells: allow wrapping, prevent overflow */
      #inventoryTable td, .table td {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        min-width: 0 !important;
        flex-wrap: wrap !important;
        display: block !important;
        box-sizing: border-box;
      }
      #inventoryTable tr, .table tr {
        display: block !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box;
      }
      /* Product cards: allow content to wrap, prevent overflow */
      .product-card, .product-card .card-body {
        max-width: 100% !important;
        min-width: 0 !important;
        overflow-x: auto !important;
        word-break: break-word !important;
        box-sizing: border-box;
      }
      .product-card .card-title, .product-card .card-text {
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        min-width: 0 !important;
      }
      /* Hide horizontal scrollbars if possible */
      .table-responsive, .card-body, .product-card {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
      }
    }
    @media (max-width: 768px) {
      /* Also apply to slightly larger screens */
      #inventoryTable td, .table td, .product-card, .product-card .card-body {
        max-width: 100% !important;
        min-width: 0 !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        white-space: normal !important;
        box-sizing: border-box;
      }
    }
    </style>
    <style>
    /* --- Improved Mobile Table & Card Layout and Card Options Button --- */
    @media (max-width: 600px) {
      #inventoryTable td, .table td {
        padding: 0.25rem 0.25rem !important;
        margin: 0 !important;
        text-align: left !important;
      }
      #inventoryTable tr, .table tr {
        margin-bottom: 0.5rem !important;
        padding: 0 !important;
      }
      .product-card, .product-card .card-body {
        padding: 0.5rem !important;
        margin: 0 !important;
        border-radius: 0.5rem !important;
      }
      .product-card .card-title, .product-card .card-text {
        margin-bottom: 0.3rem !important;
        padding: 0 !important;
        text-align: left !important;
      }
      .product-card .badge {
        margin-bottom: 0.2rem !important;
      }
    }
    /* --- Three-dots dropdown in product card: upper right corner --- */
    .product-card .card-body {
      position: relative;
    }
    .product-card .card-title .dropdown {
      position: absolute;
      top: 0.25rem;
      right: 0.25rem;
      z-index: 2;
    }
    .product-card .card-title {
      padding-right: 2.2rem !important; /* space for the dropdown */
      display: block !important;
    }
    @media (max-width: 600px) {
      .product-card .card-title .dropdown {
        top: 0.15rem;
        right: 0.15rem;
      }
      .product-card .card-title {
        padding-right: 2.2rem !important;
      }
    }
    </style>
    <style>
    /* --- Three-dots dropdown icon button style for product card --- */
    .product-card .card-title .dropdown .btn-link {
      color: #212529 !important; /* neutral dark, matches Bootstrap text */
      text-decoration: none !important;
      font-size: 1.3rem;
      padding: 0.1rem 0.3rem;
      border: none;
      background: none;
      box-shadow: none;
      line-height: 1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .product-card .card-title .dropdown .btn-link:focus {
      outline: none;
      box-shadow: 0 0 0 2px var(--primary-light);
    }
    </style>
    <style>
    .product-card .product-options-dropdown {
      position: absolute;
      top: 0.5rem;
      left: 0.5rem;
      z-index: 3;
    }
    .product-card .card-title {
      padding-left: 0 !important;
      padding-right: 0 !important;
    }
    </style>
    <style>
    .product-card .card-body {
      position: relative;
    }
    .product-card .product-options-dropdown {
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
      z-index: 3;
    }
    .product-card .card-title {
      margin-top: 1.2rem;
    }
    </style>
    <style>
    #statusConfirmModal .modal-dialog {
      max-width: 500px;
      width: 90vw;
    }
    @media (max-width: 600px) {
      #statusConfirmModal .modal-dialog {
        max-width: 95vw;
        width: 95vw;
      }
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
                <button type="button" id="sidebarCollapseSidebar" class="btn btn-sm d-md-none" title="Toggle sidebar menu" aria-label="Toggle sidebar menu">
                    <i class="bi bi-list text-white" aria-hidden="true"></i>
                </button>
            </div>
            <ul class="list-unstyled components">
                <li><a href="dashboard.php"><i class="bi bi-speedometer2 me-2" aria-hidden="true"></i><span>Dashboard</span></a></li>
                <li class="active"><a href="products_inventory.php" aria-current="page"><i class="bi bi-basket me-2" aria-hidden="true"></i><span>Fruit Inventory</span></a></li>
                <li><a href="sales.php"><i class="bi bi-cart me-2" aria-hidden="true"></i><span>Sales</span></a></li>
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
                            <label for="globalSearch" class="sr-only">Search products</label>
                            <span class="input-group-text bg-transparent border-0"><i class="bi bi-search" aria-hidden="true"></i></span>
                            <input type="text" class="form-control border-0" id="globalSearch" placeholder="Search..." value="<?php echo htmlspecialchars($search ?? ''); ?>" aria-describedby="searchFeedback" title="Search...">
                            <button type="button" class="btn btn-primary" id="searchBtn" aria-label="Search" title="Perform search"><i class="bi bi-search" aria-hidden="true"></i> Search</button>
                        </div>
                        <div class="dropdown me-3">
                            <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="filterDropdown" data-bs-toggle="dropdown" aria-expanded="false" aria-controls="filterDropdownMenu" title="Filter inventory by status">
                                <?php echo htmlspecialchars($filter ?? 'All Fruits'); ?>
                            </button>
                            <ul class="dropdown-menu" id="filterDropdownMenu" aria-labelledby="filterDropdown">
                                <li><a class="dropdown-item" href="products_inventory.php?filter=All Products&search=<?php echo urlencode($search ?? ''); ?>&tab=<?php echo $tab ?? 'inventory'; ?>">All Fruits</a></li>
                                <li><a class="dropdown-item" href="products_inventory.php?filter=Active&search=<?php echo urlencode($search ?? ''); ?>&tab=<?php echo $tab ?? 'inventory'; ?>">Active</a></li>
                                <li><a class="dropdown-item" href="products_inventory.php?filter=Discontinued&search=<?php echo urlencode($search ?? ''); ?>&tab=<?php echo $tab ?? 'inventory'; ?>">Discontinued</a></li>
                            </ul>
                        </div>
                        <div class="dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-label="User menu" aria-expanded="false" title="User options">
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
                    <?php if (isset($success) && $success): ?>
                        <div class="alert alert-success alert-dismissible fade show">
                            <?php echo htmlspecialchars($success); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                    <?php if (isset($error) && $error): ?>
                        <div class="alert alert-danger alert-dismissible fade show">
                            <?php echo htmlspecialchars($error); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    <?php endif; ?>
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h2 class="mb-1 fw-bold">Fruit Inventory Management</h2>
                        <p class="text-muted">Manage your fruit inventory, <?php echo htmlspecialchars($user['username'] ?? 'User'); ?>.</p>
                    </div>
                    <div class="col-md-6 text-md-end d-flex justify-content-md-end align-items-center flex-wrap gap-2">
                        <button class="btn btn-outline-secondary" id="refreshInventory" aria-label="Refresh inventory" title="Reload inventory data">
                            <i class="bi bi-arrow-clockwise me-1" aria-hidden="true"></i> Refresh
                        </button>
                    </div>
                </div>
                <!-- Statistics Section -->
                <h5>Overview</h5>
                <div class="row g-4 mb-4">
                    <div class="col-lg-3 col-md-6">
                        <div class="card stat-card" role="region" aria-labelledby="totalFruitsLabel">
                            <div class="card-body d-flex align-items-center">
                                <div class="stat-icon me-3 bg-primary">
                                    <i class="bi bi-basket" aria-hidden="true"></i>
                                </div>
                                <div>
                                    <p class="text-muted mb-1" id="totalFruitsLabel">Total Fruits</p>
                                    <h4 class="mb-0" id="totalFruitsValue"><?php echo $totalProducts ?? 0; ?></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-3 col-md-6">
                        <div class="card stat-card" role="region" aria-labelledby="activeFruitsLabel">
                            <div class="card-body d-flex align-items-center">
                                <div class="stat-icon me-3 bg-success">
                                    <i class="bi bi-check-lg" aria-hidden="true"></i>
                                </div>
                                <div>
                                    <p class="text-muted mb-1" id="activeFruitsLabel">Active Fruits</p>
                                    <h4 class="mb-0" id="activeFruitsValue"><?php echo $activeProducts ?? 0; ?></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-3 col-md-6">
                        <div class="card stat-card" role="region" aria-labelledby="totalStockLabel">
                            <div class="card-body d-flex align-items-center">
                                <div class="stat-icon me-3 bg-warning">
                                    <i class="bi bi-box-seam" aria-hidden="true"></i>
                                </div>
                                <div>
                                    <p class="text-muted mb-1" id="totalStockLabel">Total Stock</p>
                                    <h4 class="mb-0" id="totalStockValue"><?php echo $totalStock ?? 0; ?></h4>
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
                                    <h4 class="mb-0" id="restockAlertsValue"><?php echo $restockAlerts ?? 0; ?></h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- Actions Section -->
                <h5>Actions</h5>
                <div class="row mb-4 align-items-center">
                    <div class="col-md-12 d-flex flex-wrap gap-2 justify-content-md-end">
                        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#productModal" data-action="add" aria-label="Add new fruit" title="Add a new fruit to inventory">
                            <i class="bi bi-plus-lg me-1" aria-hidden="true"></i>Add Fruit
                        </button>
                        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#buyModal" aria-label="Record sale" title="Record a fruit sale">
                            <i class="bi bi-cart me-1" aria-hidden="true"></i>Record Sale
                        </button>
                        <button class="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#addStockModal" aria-label="Add stock" title="Add stock to a fruit">
                            <i class="bi bi-box-seam me-1" aria-hidden="true"></i>Add Stock
                        </button>
                    </div>
                </div>
                <ul class="nav nav-tabs mb-4" role="tablist">
                    <li class="nav-item" role="presentation">
                        <a class="nav-link <?php echo ($tab ?? 'inventory') === 'inventory' ? 'active' : ''; ?>" id="inventory-tab" data-bs-toggle="tab" href="#inventory" role="tab" aria-controls="inventory" aria-selected="<?php echo ($tab ?? 'inventory') === 'inventory' ? 'true' : 'false'; ?>" title="View inventory list">Inventory</a>
                    </li>
                    <li class="nav-item" role="presentation">
                        <a class="nav-link <?php echo ($tab ?? 'inventory') === 'products' ? 'active' : ''; ?>" id="products-tab" data-bs-toggle="tab" href="#products" role="tab" aria-controls="products" aria-selected="<?php echo ($tab ?? 'inventory') === 'products' ? 'true' : 'false'; ?>" title="View fruit details">Fruits</a>
                    </li>
                </ul>
                <div class="tab-content">
                    <!-- Inventory Tab -->
                    <div class="tab-pane fade <?php echo ($tab ?? 'inventory') === 'inventory' ? 'show active' : ''; ?>" id="inventory" role="tabpanel" aria-labelledby="inventory-tab">
                        <div class="card stat-card" role="region" aria-labelledby="inventoryListLabel">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <div>
                                    <h5 class="card-title mb-0" id="inventoryListLabel">Inventory List</h5>
                                    <p class="text-muted small" id="inventoryCount"><?php echo count($products ?? []) ?> fruits</p>
                                </div>
                            </div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover align-middle" id="inventoryTable" aria-label="Fruit inventory list">
                                        <caption class="sr-only">List of fruits with their number, name, size, price, stock, and status</caption>
                                        <thead class="table-light">
                                            <tr>
                                                <th scope="col">#</th>
                                                <th scope="col">Fruit</th>
                                                <th scope="col">Size</th>
                                                <th scope="col">Price</th>
                                                <th scope="col" class="sortable" data-sort="stock" aria-sort="none" title="Sort by stock level">Stock <i class="bi sort-icon"></i><span class="sort-loading"><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span></span></th>
                                                <th scope="col">Status</th>
                                                <th scope="col">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <?php foreach ($products ?? [] as $product): ?>
                                                <?php
                                                $stock = $product['stock'] ?? 0;
                                                $stockIcon = '';
                                                $stockClass = '';
                                                if ($stock < 10) {
                                                    $stockIcon = '<i class="bi bi-exclamation-triangle-fill text-danger" title="Low Stock"></i>';
                                                    $stockClass = 'text-danger';
                                                } else if ($stock <= 30) {
                                                    $stockIcon = '<i class="bi bi-exclamation-circle-fill text-warning" title="Medium Stock"></i>';
                                                    $stockClass = 'text-warning';
                                                } else {
                                                    $stockIcon = '<i class="bi bi-check-circle-fill text-success" title="High Stock"></i>';
                                                    $stockClass = 'text-success';
                                                }
                                                ?>
                                                <tr data-id="<?php echo $product['product_id']; ?>">
                                                    <td><?php echo $product['product_id']; ?></td>
                                                    <td class="fruit-name">
                                                        <?php echo htmlspecialchars($product['name']); ?>
                                                    </td>
                                                    <td><?php echo !empty($product['size']) ? htmlspecialchars($product['size']) : 'N/A'; ?></td>
                                                    <td>₱<?php echo number_format($product['price'] ?? 0, 2); ?></td>
                                                    <td class="stock-value <?php echo $stockClass; ?>">
                                                        <?php echo $stockIcon; ?> <?php echo ($stock === null ? 0 : $stock); ?>
                                                        <small class="d-block text-muted">
                                                            <?php echo $stock < 10 ? 'Low Stock' : ($stock <= 30 ? 'Medium Stock' : 'High Stock'); ?>
                                                        </small>
                                                        <button type="button" class="btn btn-link p-0 stock-details-icon" data-product-id="<?php echo $product['product_id']; ?>" style="cursor: pointer; margin-left: 5px;" title="View stock batches (FIFO)">
                                                            <i class="bi bi-info-circle" aria-hidden="true"></i>
                                                            <span class="visually-hidden">View stock details for <?php echo htmlspecialchars($product['name']); ?></span>
                                                        </button>
                                                    </td>
                                                    <td>
                                                        <span class="badge <?php echo $product['status'] === 'Active' ? 'bg-success' : 'bg-danger'; ?>" role="status">
                                                            <?php echo htmlspecialchars($product['status']); ?>
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <div class="dropdown">
                                                            <button class="btn btn-sm btn-icon" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="More options">
                                                                <i class="bi bi-three-dots-vertical"></i>
                                                                <span class="visually-hidden">More options for <?php echo htmlspecialchars($product['name']); ?></span>
                                                            </button>
                                                            <ul class="dropdown-menu dropdown-menu-end">
                                                                <li>
                                                                    <button class="dropdown-item add-stock-btn" data-id="<?php echo $product['product_id']; ?>" data-bs-toggle="modal" data-bs-target="#addStockModal" title="Add stock to this fruit">
                                                                        <i class="bi bi-plus-lg me-2" aria-hidden="true"></i> Add Stock
                                                                    </button>
                                                                </li>
                                                                <li>
                                                                    <button class="dropdown-item edit-btn" data-id="<?php echo $product['product_id']; ?>" data-bs-toggle="modal" data-bs-target="#productModal" title="Edit this fruit">
                                                                        <i class="bi bi-pencil me-2" aria-hidden="true"></i> Edit
                                                                    </button>
                                                                </li>
                                                                <li>
                                                                    <?php
                                                                    $isDiscontinued = ($product['status'] === 'Discontinued');
                                                                    $statusBtnLabel = $isDiscontinued ? 'Recontinue' : 'Discontinue';
                                                                    $statusBtnIcon = $isDiscontinued ? 'arrow-counterclockwise' : 'trash';
                                                                    $statusBtnNext = $isDiscontinued ? 'Active' : 'Discontinued';
                                                                    ?>
                                                                    <button class="dropdown-item status-btn" data-id="<?php echo $product['product_id']; ?>" data-status="<?php echo $statusBtnNext; ?>">
                                                                        <i class="bi bi-<?php echo $statusBtnIcon; ?> me-2" aria-hidden="true"></i> <?php echo $statusBtnLabel; ?>
                                                                    </button>
                                                                </li>
                                                            </ul>
                                                        </div>
                                                    </td>
                                                </tr>
                                            <?php endforeach; ?>
                                        </tbody>
                                    </table>
                                </div>
                                <div class="mb-3">
                                    <small class="text-muted">
                                        <strong>Stock Status Legend:</strong><br>
                                        <i class="bi bi-exclamation-triangle-fill text-danger"></i> Low Stock (less than 10)<br>
                                        <i class="bi bi-exclamation-circle-fill text-warning"></i> Medium Stock (10-30)<br>
                                        <i class="bi bi-check-circle-fill text-success"></i> High Stock (more than 30)
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                    <!-- Products Tab -->
                    <div class="tab-pane fade <?php echo ($tab ?? 'inventory') === 'products' ? 'show active' : ''; ?>" id="products" role="tabpanel" aria-labelledby="products-tab">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="card-title mb-0">Fruits List</h5>
                            <div class="dropdown">
                                <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="sortDropdown" data-bs-toggle="dropdown" aria-expanded="false" aria-controls="sortDropdownMenu" title="Sort fruit list">
                                    Sort by: Name
                                </button>
                                <ul class="dropdown-menu" id="sortDropdownMenu" aria-labelledby="sortDropdown">
                                    <li><button class="dropdown-item sort-option" data-sort="name" data-order="asc">Name</button></li>
                                    <li><button class="dropdown-item sort-option" data-sort="date_added" data-order="desc">Date Added (Newest First)</button></li>
                                    <li><button class="dropdown-item sort-option" data-sort="date_added" data-order="asc">Date Added (Oldest First)</button></li>
                                </ul>
                            </div>
                        </div>
                        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4" id="productsGrid">
                            <?php foreach ($products ?? [] as $product): ?>
                                <?php
                                $date = new DateTime($product['date_added'] ?? 'now');
                                $formattedDate = $date->format('F j, Y');
                                $imageSrc = $product['image'] ? htmlspecialchars($product['image']) : 'assets/no-image.png';
                                $imageAlt = $product['image'] ? htmlspecialchars($product['name']) : 'No image for ' . htmlspecialchars($product['name']);
                                ?>
                                <div class="col">
                                    <div class="card product-card h-100" role="region" aria-labelledby="product-<?php echo $product['product_id']; ?>">
                                        <img src="<?php echo $imageSrc; ?>" class="product-image" alt="<?php echo $imageAlt; ?>">
                                        <div class="card-body">
                                            <div class="d-flex justify-content-between align-items-start mb-2">
                                                <h5 class="card-title mb-0" id="product-<?php echo $product['product_id']; ?>">
                                                    #<?php echo $product['product_id']; ?>: 
                                                    <span class="fruit-name">
                                                        <?php echo htmlspecialchars($product['name']); ?>
                                                    </span>
                                                </h5>
                                                <div class="dropdown">
                                                    <button type="button" class="btn btn-link p-0" data-bs-toggle="dropdown" aria-expanded="false" title="More options">
                                                        <span class="visually-hidden">More options</span>
                                                        <i class="bi bi-three-dots-vertical"></i>
                                                    </button>
                                                    <ul class="dropdown-menu">
                                                        <li>
                                                            <button class="dropdown-item edit-btn" data-id="<?php echo $product['product_id']; ?>" data-bs-toggle="modal" data-bs-target="#productModal" title="Edit this fruit">
                                                                <i class="bi bi-pencil me-2" aria-hidden="true"></i> Edit
                                                            </button>
                                                        </li>
                                                        <li>
                                                            <?php
                                                            $isDiscontinued = ($product['status'] === 'Discontinued');
                                                            $statusBtnLabel = $isDiscontinued ? 'Recontinue' : 'Discontinue';
                                                            $statusBtnIcon = $isDiscontinued ? 'arrow-counterclockwise' : 'trash';
                                                            $statusBtnNext = $isDiscontinued ? 'Active' : 'Discontinued';
                                                            ?>
                                                            <button class="dropdown-item status-btn" data-id="<?php echo $product['product_id']; ?>" data-status="<?php echo $statusBtnNext; ?>">
                                                                <i class="bi bi-<?php echo $statusBtnIcon; ?> me-2" aria-hidden="true"></i> <?php echo $statusBtnLabel; ?>
                                                            </button>
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>
                                            <p class="card-text"><strong>Size:</strong> <?php echo !empty($product['size']) ? htmlspecialchars($product['size']) : 'N/A'; ?></p>
                                            <p class="card-text"><strong>Price:</strong> ₱<?php echo number_format($product['price'] ?? 0, 2); ?></p>
                                            <p class="card-text"><strong>Cost:</strong> ₱<?php echo number_format($product['cost'] ?? 0, 2); ?></p>
                                            <p class="card-text"><strong>Stock:</strong> <?php echo ($product['stock'] === null ? 0 : $product['stock']); ?> boxes</p>
                                            <p class="card-text"><strong>Status:</strong> 
                                                <span class="badge <?php echo $product['status'] === 'Active' ? 'bg-success' : 'bg-danger'; ?>">
                                                    <?php echo htmlspecialchars($product['status']); ?>
                                                </span>
                                            </p>
                                            <p class="card-text text-muted">Added on: <?php echo $formattedDate; ?></p>
                                        </div>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Product Modal -->
            <div class="modal fade" id="productModal" tabindex="-1" aria-labelledby="productModalLabel" role="dialog">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="productModalLabel">Add New Fruit</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Add this above the <form id="productForm" ... > in the Add Fruit modal: -->
                            <div id="productFormAlert"></div>

                            <form id="productForm" enctype="multipart/form-data" novalidate>
                                <input type="hidden" id="formAction" name="action" value="add">
                                <input type="hidden" id="productId" name="productId">
                                <div class="row g-3 mb-3">
                                    <div class="col-md-6">
                                        <label for="productName" class="form-label">Fruit Name</label>
                                        <input type="text" class="form-control fruit-name" id="productName" name="productName" required aria-describedby="productNameFeedback" title="Enter the fruit's name" placeholder="Enter fruit name">
                                        <div id="productNameFeedback" class="invalid-feedback">Please enter a fruit name.</div>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="variant" class="form-label">Variant (Optional)</label>
                                        <input type="text" class="form-control" id="variant" name="variant" placeholder="e.g., Navel for Oranges" aria-describedby="variantFeedback" title="Specify a variant if applicable">
                                        <div id="variantFeedback" class="invalid-feedback">Please enter a valid variant name.</div>
                                    </div>
                                </div>
                                <div class="row g-3 mb-3">
                                    <div class="col-md-6">
                                        <label for="size" class="form-label">Size</label>
                                        <input type="text" class="form-control" id="size" name="size" placeholder="e.g., Medium" aria-describedby="sizeFeedback" title="Enter the fruit's size">
                                        <div id="sizeFeedback" class="invalid-feedback">Please enter a valid size.</div>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="cost" class="form-label">Cost (₱)</label>
                                        <input type="number" class="form-control" id="cost" name="cost" step="0.01" min="0" required aria-describedby="costFeedback" title="Enter the cost per unit" placeholder="0.00">
                                        <div id="costFeedback" class="invalid-feedback">Please enter a valid cost (0 or greater).</div>
                                    </div>
                                </div>
                                <div class="row g-3 mb-3">
                                    <div class="col-md-6">
                                        <label for="price" class="form-label">Price (₱)</label>
                                        <input type="number" class="form-control" id="price" name="price" step="0.01" min="0" required aria-describedby="priceFeedback priceVATNote" title="Enter the price (before VAT)" placeholder="0.00">
                                        <div class="mt-2">
                                            <small class="text-muted" id="priceVATNote">VAT Inclusive Price: ₱<span id="priceWithVAT">0.00</span> (automatically includes 12% VAT)</small>
                                        </div>
                                        <div id="priceFeedback" class="invalid-feedback">Please enter a valid price (0 or greater).</div>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="initialStock" class="form-label">Initial Stock</label>
                                        <input type="number" class="form-control" id="initialStock" name="initialStock" min="0" required aria-describedby="initialStockFeedback" title="Enter the initial stock quantity" placeholder="0">
                                        <div id="initialStockFeedback" class="invalid-feedback">Please enter a valid stock quantity (0 or greater).</div>
                                    </div>
                                </div>
                                <div class="row g-3 mb-3">
                                    <div class="col-md-6">
                                        <label for="status" class="form-label">Status</label>
                                        <select class="form-select" id="status" name="status" required aria-describedby="statusFeedback statusHelp" title="Select the fruit's status">
                                            <!-- Options will be dynamically populated based on current status -->
                                        </select>
                                        <div id="statusFeedback" class="invalid-feedback">Please select a status.</div>
                                        <small id="statusHelp" class="form-text text-muted"></small>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="dateAddedDisplay" class="form-label">Date Added</label>
                                        <input type="text" class="form-control" id="dateAddedDisplay" readonly>
                                        <input type="hidden" id="dateAdded" name="dateAdded">
                                        <small class="form-text text-muted" id="dateAddedHelp">This is set to the current date for new fruits, or the original date for existing fruits.</small>
                                        <div id="dateAddedFeedback" class="invalid-feedback">Please select a valid date.</div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="productImage" class="form-label">Fruit Image (Optional)</label>
                                    <input type="file" class="form-control w-auto" style="max-width: 400px;" id="productImage" name="productImage" accept="image/jpeg,image/png" aria-describedby="productImageFeedback" title="Upload an image (JPG/PNG, max 2MB)">
                                    <div id="productImageFeedback" class="invalid-feedback">Please upload a valid image (JPG/PNG, max 2MB).</div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal" title="Close without saving">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveProductBtn" title="Save the fruit details">Add Fruit</button>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Buy Modal -->
            <div class="modal fade" id="buyModal" tabindex="-1" aria-labelledby="buyModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="buyModalLabel">Record Sale</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Alert area for messages -->
                            <div id="buyFormAlert"></div>

                            <!-- Add this above the step content in the Record Sale modal -->
                            <div class="sale-steps" id="saleStepsIndicator">
                                <div class="sale-step" id="stepIndicator1">
                                    <i class="bi bi-basket"></i>
                                    <div class="sale-step-label">Select Items</div>
                                </div>
                                <div class="sale-step" id="stepIndicator2">
                                    <i class="bi bi-credit-card"></i>
                                    <div class="sale-step-label">Payment</div>
                                </div>
                                <div class="sale-step" id="stepIndicator3">
                                    <i class="bi bi-receipt"></i>
                                    <div class="sale-step-label">Receipt</div>
                                </div>
                            </div>
                            <!-- Step 1: Fruit Selection -->
                            <div id="saleStep1">
                                <form id="buyForm" novalidate>
                                    
                                    <div id="itemsContainer">
                                        <div class="item-row mb-3 p-3 border rounded">
                                            <div class="row">
                                                <div class="col-md-5">
                                                    <label class="form-label">Fruit</label>
                                                    <select class="form-select product-select stock-product-select" id="productSelect0" required>
                                                        <option value="">Select a fruit</option>
                                                    </select>
                                                    <div class="stock-info text-muted small mt-1"></div>
                                                </div>
                                                <div class="col-md-4">
                                                    <label class="form-label">Quantity</label>
                                                    <input type="number" class="form-control quantity-input stock-quantity" id="quantityInput0" min="1" required>
                                                </div>
                                                <div class="col-md-3">
                                                    <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">&nbsp;</label>
                                                    <!-- No remove button for the first row -->
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Add Item button -->
                                    <button type="button" class="btn btn-outline-primary btn-sm mt-2" id="addItemBtn">
                                        <i class="bi bi-plus-circle"></i> Add Another Item
                                    </button>

                                    <div class="mt-3">
                                        <strong>
                                            Total Price (VAT Inclusive): ₱<span id="liveSaleTotalWithVATText">0.00</span>
                                        </strong>
                                    </div>

                                    <div class="mt-3 d-flex align-items-center gap-2">
                                        <label class="form-label mb-0">Date Recorded:</label>
                                        <input type="text" class="form-control form-control-sm w-auto" id="purchaseDate" readonly>
                                        <input type="hidden" name="purchase_date" value="<?php echo date('F j, Y'); ?>" readonly>
                                    </div>
                                    <small class="form-text text-muted">Set to today and cannot be changed.</small>
                                </form>
                            </div>

                            <!-- Step 2: Payment -->
                            <div id="saleStep2" style="display:none;">
                                <div class="payment-summary-table mb-4">
                                    <table class="table table-bordered mb-0">
                                        <thead>
                                            <tr>
                                                <th id="descHeader">Description</th>
                                                <th class="quantity-col text-center">Quantity</th>
                                                <th class="price-col text-center">Price</th>
                                                <th class="amount text-end">Amount</th>
                                            </tr>
                                        </thead>
                                        <tbody id="paymentTableItems">
                                        </tbody>
                                    </table>
                                </div>
                                <div class="payment-summary-table">
                                    <table class="table table-bordered mb-0">
                                        <tbody>
                                            <tr>
                                                <th>Subtotal</th>
                                                <td class="amount">₱<span id="paymentSubtotal">0.00</span></td>
                                            </tr>
                                            <tr>
                                                <th>VAT (12%)</th>
                                                <td class="amount">₱<span id="paymentVAT">0.00</span></td>
                                            </tr>
                                            <tr class="total-row">
                                                <th>Total Amount with VAT</th>
                                                <td class="amount">₱<span id="paymentTotalWithVAT">0.00</span></td>
                                            </tr>
                                            <tr class="amount-tendered">
                                                <th>Amount Tendered</th>
                                                <td class="text-end">
                                                    <input type="number" class="form-control amount-input" id="paymentTendered" min="0" step="0.01" required placeholder="Amount received">
                                                </td>
                                            </tr>
                                            <tr class="change-row">
                                                <th>Change</th>
                                                <td class="amount">₱<span id="paymentChange">0.00</span></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Step 3: Receipt -->
                            <div id="saleStep3" style="display:none;">
                                <!-- Success message area -->
                                <div id="saleSuccessMessage" class="alert alert-success w-100 mb-3" style="display: none;">
                                    <i class="bi bi-check-circle-fill text-success me-2"></i>Sale recorded successfully!
                                </div>
                                <div class="receipt-container">
                                    <div class="receipt-header">
                                        <img src="assets/logo.png" alt="Logo">
                                        <div class="company-name">FruitMaster Marketing</div>
                                        <div class="company-details">Mabini Street - Libertad, Bacolod City, Negros Occidental</div>
                                        <div class="company-details">TIN: </div>
                                        <div class="company-details">Tel: 434-7680, 213-5681, 213-5682</div>
                                    </div>
                                    <div class="receipt-title">SALES RECEIPT</div>
                                    <div class="receipt-divider"></div>
                                    <div id="receiptProcessedByRow" class="receipt-info" style="display: none;">
                                        <span>Processed by: <span id="receiptProcessedBy"></span></span>
                                    </div>
                                    <div class="receipt-info">
                                        <span>Transaction #: <span id="transactionNumber"></span></span>
                                    </div>
                                    <div class="receipt-info">
                                        <span>OR #: <span id="orNumber"></span></span>
                                    </div>
                                    <div class="receipt-info">
                                        <span>Date: <span id="receiptDate"></span></span>
                                    </div>
                                    <table class="receipt-table">
                                        <thead>
                                            <tr>
                                                <th>Description</th>
                                                <th class="align-right">Qty</th>
                                                <th class="align-right">Price</th>
                                                <th class="align-right">Amount</th>
                                            </tr>
                                        </thead>
                                        <tbody id="receiptTableItems"></tbody>
                                    </table>
                                    <div class="receipt-divider"></div>
                                    <div class="receipt-summary">
                                        <div class="receipt-summary-row">
                                            <span>Sub Total:</span>
                                            <span id="receiptSubtotal">0.00</span>
                                        </div>
                                        <div class="receipt-summary-row">
                                            <span>Plus 12% VAT:</span>
                                            <span id="receiptVAT">0.00</span>
                                        </div>
                                        <div class="receipt-summary-row total">
                                            <span>TOTAL AMOUNT TO BE PAID:</span>
                                            <span id="receiptTotalAmount">0.00</span>
                                        </div>
                                        <div class="receipt-summary-row">
                                            <span>Cash (PHP) Tendered:</span>
                                            <span id="receiptAmountPaid">0.00</span>
                                        </div>
                                        <div class="receipt-summary-row">
                                            <span>Change Cash:</span>
                                            <span id="receiptChange">0.00</span>
                                        </div>
                                    </div>
                                    <div class="receipt-divider"></div>
                                    <div class="receipt-footer">
                                        <p>This serves as your Official Receipt.</p>
                                        <p>SERVER SN: </p>
                                        <p>POS SN: </p>
                                        <p>BIR PERMIT NO. </p>
                                        <p>ACCREDITATION NO. </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <!-- Success message area -->
                            <div id="saleSuccessMessage" class="alert alert-success w-100 mb-3" style="display: none;">
                                <i class="bi bi-check-circle-fill text-success me-2"></i>Sale recorded successfully!
                            </div>
                            <!-- Step 1 buttons -->
                            <div id="step1Buttons">
                                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" id="nextToStep2">Proceed to Payment</button>
                            </div>
                            <!-- Step 2 buttons -->
                            <div id="step2Buttons" style="display:none;">
                                <button type="button" class="btn btn-outline-secondary" id="backToStep1">Back</button>
                                <button type="button" class="btn btn-success" id="confirmPaymentStep" disabled>Confirm Payment</button>
                            </div>
                            <!-- Step 3 buttons -->
                            <div id="step3Buttons" style="display:none;">
                                <button type="button" class="btn btn-outline-secondary" id="backToStep2">Back</button>
                                <button type="button" class="btn btn-outline-success" id="printReceiptBtn">Record Sale</button>
                                <button type="button" class="btn btn-primary" id="printReceiptAfterBtn" style="display:none;">
                                    <i class="bi bi-printer"></i> Print Receipt
                                </button>
                                <button type="button" class="btn btn-success" id="doneBtn" style="display:none;" data-bs-dismiss="modal">Done</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Add Stock Modal -->
            <div class="modal fade" id="addStockModal" tabindex="-1" aria-labelledby="addStockModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="addStockModalLabel">Add Stock</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Alert area for messages -->
                            <div id="addStockFormAlert"></div>
                            <!-- Stock items container -->
                            <div id="stockItemsContainer">
                                <div class="stock-item mb-3 p-3 border rounded">
                                    <div class="row">
                                        <div class="col-md-5">
                                            <label class="form-label">Fruit</label>
                                            <select class="form-select stock-product-select" required>
                                                <option value="">Select a fruit</option>
                                            </select>
                                            <div class="stock-indicator text-muted small mt-1"></div>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Quantity to Add</label>
                                            <input type="number" class="form-control stock-quantity" min="1" required>
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label">&nbsp;</label>
                                            <!-- No delete button for the first row -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- Add Item button -->
                            <button type="button" class="btn btn-outline-primary btn-sm mt-2" id="addStockItemBtn">
                                <i class="bi bi-plus-circle"></i> Add Another Item
                            </button>
                            <!-- Date Added field -->
                            <div class="mt-3 d-flex align-items-center gap-2">
                                <label class="form-label mb-0">Date Added:</label>
                                <input type="text" class="form-control form-control-sm w-auto" id="stockDateDisplay" readonly>
                                <input type="hidden" id="stockDate" value="<?php echo date('Y-m-d'); ?>">
                            </div>
                            <small class="form-text text-muted ms-2">Set to today and cannot be changed.</small>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveStockBtn" disabled>Add Stock</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Add status change handler -->
    <script>
    // Bootstrap alert helper for user feedback
    function showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        $('#alertContainer').html(alertHtml);
    }

    // Make fetchActiveProducts globally available
    async function fetchActiveProducts() {
        try {
            const response = await fetch('products_inventory.php?action=get_active_products', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!response.ok) throw new Error('Network error');
            const data = await response.json();
            if (data.success) {
                const products = data.data;
                // Update product selects in all modals
                $('.product-select, .stock-product-select').each(function() {
                    const $select = $(this);
                    const currentValue = $select.val();
                    $select.html('<option value="">Select a fruit</option>');
                    products.forEach(product => {
                        const variant = product.variant ? `(${product.variant})` : '';
                        const size = product.size ? `(${product.size})` : '';
                        const price = product.price ? `(₱${parseFloat(product.price).toFixed(2)})` : '';
                        const stock = product.stock !== undefined ? `(Current Stock: ${product.stock})` : '';
                        const optionText = `#${product.product_id} ${product.name} ${variant} ${size} ${price} ${stock}`.replace(/  +/g, ' ').trim();
                        const displayText = `${product.name} ${variant} ${size}`.replace(/  +/g, ' ').trim();
                        const option = $('<option>', {
                            value: product.product_id,
                            text: optionText,
                            'data-stock': product.stock,
                            'data-price': product.price,
                            'data-name': product.name,
                            'data-variant': product.variant || '',
                            'data-size': product.size || '',
                            'data-display': displayText,
                            'data-fulltext': optionText
                        });
                        $select.append(option);
                    });
                    $select.val(currentValue);
                });
                // Update product price map
                if (typeof productPriceMap !== 'undefined') {
                    productPriceMap = {};
                    products.forEach(product => {
                        productPriceMap[product.product_id] = product.price;
                    });
                }
            }
        } catch (error) {
            console.error('Fetch active products error:', error);
            if (typeof showAlert === 'function') showAlert('Failed to load products. Please try again.', 'danger');
        }
    }

    // Add this function before the document.ready block
    async function populateProductSelect($select) {
        try {
            const response = await fetch('products_inventory.php?action=get_active_products', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!response.ok) throw new Error('Network error');
            const data = await response.json();
            if (data.success) {
                const products = data.data;
                const currentValue = $select.val();
                $select.html('<option value="">Select a fruit</option>');
                products.forEach(product => {
                    const variant = product.variant ? `(${product.variant})` : '';
                    const size = product.size ? `(${product.size})` : '';
                    const price = product.price ? `(₱${parseFloat(product.price).toFixed(2)})` : '';
                    const stock = product.stock !== undefined ? `(Current Stock: ${product.stock})` : '';
                    const optionText = `#${product.product_id} ${product.name} ${variant} ${size} ${price} ${stock}`.replace(/  +/g, ' ').trim();
                    const displayText = `${product.name} ${variant} ${size}`.replace(/  +/g, ' ').trim();
                    const option = $('<option>', {
                        value: product.product_id,
                        text: optionText,
                        'data-stock': product.stock,
                        'data-price': product.price,
                        'data-name': product.name,
                        'data-variant': product.variant || '',
                        'data-size': product.size || '',
                        'data-display': displayText,
                        'data-fulltext': optionText
                    });
                    $select.append(option);
                });
                $select.val(currentValue);
            }
        } catch (error) {
            console.error('Populate product select error:', error);
            showAlert('Failed to load products. Please try again.', 'danger');
        }
    }

    $(document).ready(function() {
        // Initialize product fetching when page loads
        fetchActiveProducts();

        // Initialize all modals to fetch products when shown
        $('#buyModal, #addStockModal, #productModal').on('show.bs.modal', function () {
            fetchActiveProducts();
        });

        // Save handler for Add Stock
        $('#saveStockBtn').on('click', async function() {
            // Remove previous alerts in the modal
            $('#addStockFormAlert').html('');
            const productId = $('#stockProductSelect').val();
            const quantity = $('#stockQuantity').val();
            const dateAdded = $('#stockDate').val() || new Date().toISOString().slice(0, 10);
            
            if (!productId || !quantity) {
                showAlert('Please select a fruit and enter a quantity.', 'danger');
                return;
            }

            try {
                const formData = new FormData();
                formData.append('action', 'add_stock');
                formData.append('product_id', productId);
                formData.append('quantity', quantity);
                formData.append('date_added', dateAdded);

                const response = await fetch('products_inventory.php', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                const data = await response.json();
                if (data.success) {
                    // Show success message in modal
                    $('#addStockFormAlert').html('<div class="alert alert-success alert-dismissible fade show" role="alert"><i class="bi bi-check-circle-fill text-success me-2"></i>Stock added successfully!<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
                    setTimeout(() => {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('addStockModal'));
                        if (modal) modal.hide();
                        window.location.reload();
                    }, 1200);
                } else {
                    $('#addStockFormAlert').html('<div class="alert alert-danger alert-dismissible fade show" role="alert"><i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>' + (data.message || 'Failed to add stock.') + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
                }
            } catch (error) {
                $('#addStockFormAlert').html('<div class="alert alert-danger alert-dismissible fade show" role="alert"><i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>Failed to add stock. Please try again.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
            }
        });

        // Record Sale handlers
        let currentStep = 1;
        const totalSteps = 3;

        // Next button handler for Step 1
        $('#nextToStep2').on('click', function() {
            const form = $('#buyForm')[0];
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            // Calculate totals and generate items list
            const items = [];
            let totalWithVATCalculated = 0;
            $('.item-row').each(function() {
                const $select = $(this).find('.product-select option:selected');
                const $quantity = $(this).find('.quantity-input');
                if ($select.val() && $quantity.val()) {
                    const priceWithVAT = parseFloat($select.data('price'));
                    const quantity = parseInt($quantity.val());
                    const amountWithVAT = quantity * priceWithVAT;
                    totalWithVATCalculated += amountWithVAT;
                    items.push({
                        product_id: $select.val(),
                        name: $select.data('name') || $select.text().split(' — ')[0].trim(),
                        variant: $select.data('variant'),
                        size: $select.data('size'),
                        quantity: quantity,
                        price: priceWithVAT,
                        amount: amountWithVAT
                    });
                }
            });

            // Calculate pre-VAT subtotal and VAT
            const subtotal = totalWithVATCalculated / 1.12;
            const vat = totalWithVATCalculated - subtotal;

            // Update payment step values
            $('#paymentSubtotal').text(subtotal.toFixed(2));
            $('#paymentVAT').text(vat.toFixed(2));
            $('#paymentTotalWithVAT').text(totalWithVATCalculated.toFixed(2));

            // Generate payment items table
            let paymentHtml = '';
            items.forEach(item => {
                let description = `#${item.product_id} ${item.name}`;
                if (item.variant) description += ` (${item.variant})`;
                if (item.size) description += ` (${item.size})`;
                paymentHtml += `
                    <tr>
                        <td>${description}</td>
                        <td class="text-end">${item.quantity}</td>
                        <td class="text-end">₱${Number(item.price).toFixed(2)}</td>
                        <td class="amount text-end">₱${Number(item.amount).toFixed(2)}</td>
                    </tr>
                `;
            });
            $('#paymentTableItems').html(paymentHtml);

            // Show step 2 and correct buttons
            $('#saleStep1').hide();
            $('#saleStep2').show();
            $('#step1Buttons').hide();
            $('#step2Buttons').show();
            $('#step3Buttons').hide();
            currentStep = 2;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            updateSaleStepIndicator(currentStep);
        });

        // Back button handler for Step 2
        $('#backToStep1').on('click', function() {
            $('#saleStep2').hide();
            $('#saleStep1').show();
            $('#step2Buttons').hide();
            $('#step1Buttons').show();
            $('#step3Buttons').hide();
            currentStep = 1;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            updateSaleStepIndicator(currentStep);
        });

        // Payment amount handler
        $('#paymentTendered').on('input', function() {
            const tendered = parseFloat($(this).val()) || 0;
            const total = parseFloat($('#paymentTotalWithVAT').text()) || 0;
            const change = tendered - total;
            $('#paymentChange').text(change >= 0 ? change.toFixed(2) : '0.00');
        });

        // Confirm payment button handler (Step 2 to Step 3)
        $('#confirmPaymentStep').on('click', function() {
            const tendered = parseFloat($('#paymentTendered').val()) || 0;
            const totalWithVATFromStep2 = parseFloat($('#paymentTotalWithVAT').text()) || 0;
            if (tendered < totalWithVATFromStep2) {
                showAlert('Amount tendered must be greater than or equal to the total amount.', 'danger');
                return;
            }
            // Generate receipt data
            const items = [];
            let totalWithVATCalculated = 0;
            $('.item-row').each(function() {
                const $select = $(this).find('.product-select option:selected');
                const $quantity = $(this).find('.quantity-input');
                if ($select.val() && $quantity.val()) {
                    const priceWithVAT = parseFloat($select.data('price'));
                    const quantity = parseInt($quantity.val());
                    const amountWithVAT = quantity * priceWithVAT;
                    totalWithVATCalculated += amountWithVAT;
                    items.push({
                        product_id: $select.val(),
                        name: $select.data('name') || $select.text().split(' — ')[0].trim(),
                        variant: $select.data('variant'),
                        size: $select.data('size'),
                        quantity: quantity,
                        price: priceWithVAT,
                        amount: amountWithVAT
                    });
                }
            });
            // Calculate pre-VAT subtotal and VAT
            const subtotal = totalWithVATCalculated / 1.12;
            const vat = totalWithVATCalculated - subtotal;
            // Update receipt
            const now = new Date();
            $('#transactionNumber').text('');
            $('#orNumber').text('');
            $('#receiptDate').text(now.toLocaleString());
            let receiptHtml = '';
            items.forEach(item => {
                let description = `#${item.product_id} ${item.name}`;
                if (item.variant && !description.includes(item.variant)) description += ` (${item.variant})`;
                if (item.size && !description.includes(item.size)) description += ` (${item.size})`;
                const price = Number(item.price);
                const quantity = Number(item.quantity);
                const amount = price * quantity;
                receiptHtml += `
                    <tr>
                        <td>${description}</td>
                        <td style="text-align:right">${quantity}</td>
                        <td style="text-align:right">₱${price.toFixed(2)}</td>
                        <td style="text-align:right">₱${amount.toFixed(2)}</td>
                    </tr>
                `;
            });
            $('#receiptTableItems').html(receiptHtml);
            $('#receiptSubtotal').text('₱' + subtotal.toFixed(2));
            $('#receiptVAT').text('₱' + vat.toFixed(2));
            $('#receiptTotalAmount').text('₱' + totalWithVATCalculated.toFixed(2));
            $('#receiptAmountPaid').text('₱' + tendered.toFixed(2));
            $('#receiptChange').text('₱' + (tendered - totalWithVATCalculated).toFixed(2));
            // Show Step 3
            $('#saleStep2').hide();
            $('#saleStep3').show();
            $('#step2Buttons').hide();
            $('#step3Buttons').show();
            $('#step1Buttons').hide();
            currentStep = 3;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            updateSaleStepIndicator(currentStep);
        });

        // Back button handler for Step 3
        $('#backToStep2').on('click', function() {
            $('#saleStep3').hide();
            $('#saleStep2').show();
            $('#step3Buttons').hide();
            $('#step2Buttons').show();
            $('#step1Buttons').hide();
            currentStep = 2;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            updateSaleStepIndicator(currentStep);
        });

        // Record sale button handler
        $('#printReceiptBtn').on('click', async function() {
            try {
                const items = [];
                $('.item-row').each(function() {
                    const $select = $(this).find('.product-select');
                    const $selected = $select.find('option:selected');
                    const $quantity = $(this).find('.quantity-input');
                    if ($selected.val() && $quantity.val()) {
                        let name = $selected.data('name');
                        let variant = $selected.data('variant');
                        let size = $selected.data('size');
                        if (!name) {
                            let text = $selected.text();
                            text = text.replace(/^(#|\(\#\))/, '').replace(/^(\d+)\s*/, '');
                            text = text.split('(')[0].trim();
                            name = text.split('\n')[0].trim();
                        }
                        items.push({
                            product_id: $selected.val(),
                            quantity: parseInt($quantity.val()),
                            price: parseFloat($selected.data('price')),
                            name: name,
                            variant: variant,
                            size: size,
                            amount: parseInt($quantity.val()) * parseFloat($selected.data('price'))
                        });
                    }
                });

                const formData = new FormData();
                formData.append('action', 'buy');  // Changed from 'record_sale' to 'buy'
                formData.append('items', JSON.stringify(items));
                formData.append('purchase_date', $('#purchaseDate').val());
                formData.append('amount_paid', parseFloat($('#receiptAmountPaid').text().replace(/[^0-9.-]+/g, '')));

                // Show loading state
                $('#printReceiptBtn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Recording...');

                const response = await fetch('products_inventory.php', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                const data = await response.json();
                if (data.success && data.sale_id) {
                    // Fetch actual sale details from backend
                    const saleDetailsResp = await fetch(`products_inventory.php?action=get_sale_details&sale_id=${data.sale_id}`, {
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    });
                    const saleDetails = await saleDetailsResp.json();
                    
                    if (saleDetails.success) {
                        const sale = saleDetails.sale;
                        const items = saleDetails.items;
                        
                        // Update receipt with actual values
                        $('#transactionNumber').text(sale.sale_id);
                        $('#orNumber').text(sale.or_number);
                        $('#receiptDate').text(new Date(sale.recorded_at).toLocaleString());
                        $('#receiptProcessedBy').text(sale.username);
                        $('#receiptProcessedByRow').show();

                        // Build receipt table
                        let receiptHtml = '';
                        items.forEach(item => {
                            let description = `#${item.product_id} ${item.name}`;
                            if (item.variant && !description.includes(item.variant)) description += ` (${item.variant})`;
                            if (item.size && !description.includes(item.size)) description += ` (${item.size})`;
                            const price = Number(item.price);
                            const quantity = Number(item.quantity);
                            const amount = price * quantity;
                            receiptHtml += `
                                <tr>
                                    <td>${description}</td>
                                    <td style="text-align:right">${quantity}</td>
                                    <td style="text-align:right">₱${price.toFixed(2)}</td>
                                    <td style="text-align:right">₱${amount.toFixed(2)}</td>
                                </tr>
                            `;
                        });
                        $('#receiptTableItems').html(receiptHtml);

                        // Update receipt totals
                        const formatCurrency = (amount) => `₱${parseFloat(amount).toFixed(2)}`;
                        $('#receiptSubtotal').text(formatCurrency(data.total / 1.12));
                        $('#receiptVAT').text(formatCurrency(data.total - (data.total / 1.12)));
                        $('#receiptTotalAmount').text(formatCurrency(data.total));
                        $('#receiptAmountPaid').text(formatCurrency(data.amount_paid));
                        $('#receiptChange').text(formatCurrency(data.change));

                        // Show success message
                        showAlert('Sale recorded successfully!', 'success');
                        
                        // Show success message above receipt
                        $('#saleSuccessMessage').show();
                        
                        // Change buttons
                        $('#printReceiptBtn').hide();
                        $('#printReceiptAfterBtn').show();
                        $('#doneBtn').show();
                        
                        // Remove external notification
                        $('.alert').not('#saleSuccessMessage').remove();
                    } else {
                        throw new Error(saleDetails.message || 'Failed to fetch sale details');
                    }
                } else {
                    throw new Error(data.message || 'Failed to record sale');
                }
            } catch (error) {
                console.error('Record sale error:', error);
                showAlert(error.message || 'Failed to record sale. Please try again.', 'danger');
                
                // Show error message above receipt
                $('#saleSuccessMessage').removeClass('alert-success').addClass('alert-danger')
                    .text(error.message || 'Failed to record sale. Please try again.')
                    .show();
            } finally {
                // Reset button state if there was an error
                if (!$('#doneBtn').is(':visible')) {
                    $('#printReceiptBtn').prop('disabled', false).text('Record Sale');
                }
            }
        });

        // When moving to Step 3 (receipt), do NOT set transaction/OR numbers
        $('#confirmPaymentStep').on('click', function() {
            // ... existing validation code ...

            // Set temporary values for receipt
            const now = new Date();
            $('#receiptDate').text(now.toLocaleString());
            $('#receiptProcessedByRow').hide(); // Hide until sale is recorded
            
            // ... rest of existing code ...
        });

        // Add item button handler
        $('#addItemBtn').on('click', function() {
            const itemCount = $('.item-row').length;
            const newRow = `
                <div class="item-row mb-3 p-3 border rounded">
                    <div class="row">
                        <div class="col-md-5">
                            <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">Fruit</label>
                            <select class="form-select product-select stock-product-select" id="productSelect${itemCount}" required>
                                <option value="">Select a fruit</option>
                            </select>
                            <div class="stock-info text-muted small mt-1"></div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">Quantity</label>
                            <input type="number" class="form-control quantity-input stock-quantity" id="quantityInput${itemCount}" min="1" required>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">&nbsp;</label>
                            <button type="button" class="btn btn-danger btn-sm d-block w-100 remove-item">
                                <i class="bi bi-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                </div>
            `;
            $('#itemsContainer').append(newRow);
            fetchActiveProducts(); // Refresh product options
            validateAllItems();
        });

        // Remove item button handler
        $(document).on('click', '.remove-item', function() {
            if ($('.item-row').length > 1) {
                $(this).closest('.item-row').remove();
                updateTotal();
            } else {
                // showAlert('At least one item is required.', 'warning'); // REMOVE THIS LINE
            }
        });

        // Update total when quantity changes
        $(document).on('input', '.quantity-input', updateTotal);
        $(document).on('change', '.product-select', updateTotal);


        // Reset modal when closed
        $('#buyModal').on('hidden.bs.modal', function() {
            $('#buyForm')[0].reset();
            $('#itemsContainer').html(`
                <div class="item-row mb-3 p-3 border rounded">
                    <div class="row">
                        <div class="col-md-5">
                            <label class="form-label">Fruit</label>
                            <select class="form-select product-select stock-product-select" id="productSelect0" required>
                                <option value="">Select a fruit</option>
                            </select>
                            <div class="stock-info text-muted small mt-1"></div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Quantity</label>
                            <input type="number" class="form-control quantity-input stock-quantity" id="quantityInput0" min="1" required>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">&nbsp;</label>
                            <!-- No remove button for the first row -->
                        </div>
                    </div>
                </div>
            `);
            $('#saleStep1').show();
            $('#saleStep2, #saleStep3').hide();
            currentStep = 1;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            fetchActiveProducts();
            validateAllItems();
        });

        // Reset Add Stock modal when closed
        $('#addStockModal').on('hidden.bs.modal', function() {
            if ($('#addStockForm').length) {
                $('#addStockForm')[0].reset();
            }
        });

        // Update stock info when product is selected
        $(document).on('change', '.product-select', function() {
            const $select = $(this);
            const $row = $select.closest('.item-row');
            const $stockInfo = $row.find('.stock-info');
            const $quantityInput = $row.find('.quantity-input');
            const selectedOption = $select.find('option:selected');
            
            if (selectedOption.val()) {
                const stock = parseInt(selectedOption.data('stock')) || 0;
                const priceWithVAT = parseFloat(selectedOption.data('price')) || 0;
                $stockInfo.html(`
                    <div class="text-${stock < 10 ? 'danger' : (stock <= 30 ? 'warning' : 'success')}">
                        <i class="bi bi-${stock < 10 ? 'exclamation-triangle-fill' : (stock <= 30 ? 'exclamation-circle-fill' : 'check-circle-fill')}"></i>
                        Current Stock: ${stock} boxes
                    </div>
                    <div class="text-muted small">Price: ₱${priceWithVAT.toFixed(2)} (VAT inclusive)</div>
                `);
                $quantityInput.attr('max', stock);
                $quantityInput.removeClass('is-invalid is-valid');
                $quantityInput.next('.invalid-feedback').remove();
                if (parseInt($quantityInput.val()) > stock) {
                    $quantityInput.val('');
                    showAlert(`Quantity cannot exceed current stock of ${stock} boxes.`, 'warning');
                }
            } else {
                $stockInfo.html('');
                $quantityInput.removeAttr('max');
                $quantityInput.val('');
            }
            
            updateTotal();
        });

        // Validate quantity input
        $(document).on('input', '.quantity-input', function() {
            const $input = $(this);
            const $row = $input.closest('.item-row');
            const $select = $row.find('.product-select');
            const selectedOption = $select.find('option:selected');
            const quantity = parseInt($input.val()) || 0;
            const stock = parseInt(selectedOption.data('stock')) || 0;
            
            // Remove previous validation
            $input.removeClass('is-invalid is-valid');
            $input.next('.invalid-feedback').remove();
            
            if (!selectedOption.val()) {
                $input.addClass('is-invalid');
                $input.after('<div class="invalid-feedback">Please select a fruit first.</div>');
                return;
            }
            
            if (quantity <= 0) {
                $input.addClass('is-invalid');
                $input.after('<div class="invalid-feedback">Quantity must be greater than 0.</div>');
            } else if (quantity > stock) {
                $input.addClass('is-invalid');
                $input.after(`<div class="invalid-feedback">Quantity cannot exceed current stock of ${stock} boxes.</div>`);
            } else {
                $input.addClass('is-valid');
            }
            
            updateTotal();
        });

        // Update total calculation to only include valid items
        function updateTotal() {
            let total = 0;
            let hasInvalidItems = false;
            
            $('.item-row').each(function() {
                const $row = $(this);
                const $select = $row.find('.product-select');
                const $quantity = $row.find('.quantity-input');
                
                // Check if both product and quantity are valid
                if ($select.val() && $quantity.val() && !$quantity.hasClass('is-invalid')) {
                    const quantity = parseInt($quantity.val()) || 0;
                    const price = parseFloat($select.find('option:selected').data('price')) || 0;
                    total += quantity * price;
                } else {
                    hasInvalidItems = true;
                }
            });
            
            // NO VAT calculation here!
            $('#liveSaleTotalWithVATText').text(total.toFixed(2));
            
            // Update total display style based on validation
            const $totalDisplay = $('#liveSaleTotalWithVATText').closest('strong');
            if (hasInvalidItems) {
                $totalDisplay.addClass('text-muted');
                $totalDisplay.attr('title', 'Some items have invalid quantities');
            } else {
                $totalDisplay.removeClass('text-muted');
                $totalDisplay.attr('title', '');
            }
        }

        // Update next button handler to validate all fields
        $('#nextToStep2').on('click', function() {
            const form = $('#buyForm')[0];
            let isValid = true;
            
            // Check each item row
            $('.item-row').each(function() {
                const $row = $(this);
                const $select = $row.find('.product-select');
                const $quantity = $row.find('.quantity-input');
                
                // Trigger validation
                if (!$select.val()) {
                    $select.addClass('is-invalid');
                    isValid = false;
                } else {
                    $select.removeClass('is-invalid');
                }
                
                if (!$quantity.val() || $quantity.hasClass('is-invalid')) {
                    $quantity.addClass('is-invalid');
                    isValid = false;
                }
            });
            

            
            // Calculate totals
            let subtotal = 0;
            $('.item-row').each(function() {
                const quantity = parseInt($(this).find('.quantity-input').val()) || 0;
                const price = parseFloat($(this).find('.product-select option:selected').data('price')) || 0;
                subtotal += quantity * price;
            });

            const vat = subtotal * 0.12;
            const totalWithVAT = subtotal + vat;

            // Update payment step values
            $('#paymentSubtotal').text(subtotal.toFixed(2));
            $('#paymentVAT').text(vat.toFixed(2));
            $('#paymentTotalWithVAT').text(totalWithVAT.toFixed(2));

            // Show step 2
            $('#saleStep1').hide();
            $('#saleStep2').show();
            currentStep = 2;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            updateSaleStepIndicator(currentStep);
        });

        // Function to check if all items are valid
        function validateAllItems() {
            let isValid = true;
            let hasItems = false;

            $('.item-row').each(function() {
                const $row = $(this);
                const $select = $row.find('.product-select');
                const $quantity = $row.find('.quantity-input');
                
                // Skip empty rows
                if (!$select.val() && !$quantity.val()) {
                    return true; // continue to next iteration
                }
                
                hasItems = true;
                
                // Check product selection
                if (!$select.val()) {
                    $select.addClass('is-invalid');
                    isValid = false;
                } else {
                    $select.removeClass('is-invalid');
                }
                
                // Check quantity
                if (!$quantity.val() || $quantity.hasClass('is-invalid')) {
                    $quantity.addClass('is-invalid');
                    isValid = false;
                }
            });

            // Update proceed button state
            const $proceedBtn = $('#nextToStep2');
            $proceedBtn.prop('disabled', !(isValid && hasItems));
        }

        // Update validation on any change
        $(document).on('change input', '.product-select, .quantity-input', function() {
            validateAllItems();
        });

        // Update validation when adding/removing items
        $('#addItemBtn').on('click', function() {
            // ... existing add item code ...
            validateAllItems();
        });

        $(document).on('click', '.remove-item', function() {
            if ($('.item-row').length > 1) {
                $(this).closest('.item-row').remove();
                updateTotal();
                validateAllItems();
            } else {
                // showAlert('At least one item is required.', 'warning'); // REMOVE THIS LINE
            }
        });

        // Update the next button handler to use the validation function
        $('#nextToStep2').on('click', function() {
            if (!validateAllItems()) {
                return;
            }

            // Calculate totals
            let subtotal = 0;
            $('.item-row').each(function() {
                const quantity = parseInt($(this).find('.quantity-input').val()) || 0;
                const price = parseFloat($(this).find('.product-select option:selected').data('price')) || 0;
                subtotal += quantity * price;
            });

            const vat = subtotal * 0.12;
            const totalWithVAT = subtotal + vat;

            // Update payment step values
            $('#paymentSubtotal').text(subtotal.toFixed(2));
            $('#paymentVAT').text(vat.toFixed(2));
            $('#paymentTotalWithVAT').text(totalWithVAT.toFixed(2));

            // Show step 2
            $('#saleStep1').hide();
            $('#saleStep2').show();
            currentStep = 2;
            $('#saleStepIndicatorText').text(`Step ${currentStep}/${totalSteps}`);
            updateSaleStepIndicator(currentStep);
        });

        // Reset validation when modal is closed
        $('#buyModal').on('hidden.bs.modal', function() {
            // ... existing reset code ...
            validateAllItems(); // Reset button state
        });

        // Initial validation
        validateAllItems();

        // Add price calculation handler
        $('#price').on('input', function() {
            const basePrice = parseFloat($(this).val()) || 0;
            const vatAmount = basePrice * 0.12;
            const priceWithVAT = basePrice + vatAmount;
            $('#priceWithVAT').text(priceWithVAT.toFixed(2));
        });

        // Reset price calculation when modal is closed
        $('#productModal').on('hidden.bs.modal', function() {
            $('#price').val('');
            $('#priceWithVAT').text('0.00');
        });

        // Helper to populate status dropdown
        function populateStatusDropdown(selectedStatus = 'Active', isDiscontinued = false) {
            const $status = $('#status');
            if (isDiscontinued) {
                $status.html(`
                    <option value="Recontinue"${selectedStatus === 'Recontinue' ? ' selected' : ''}>Recontinue</option>
                    <option value="Discontinued"${selectedStatus === 'Discontinued' ? ' selected' : ''}>Discontinued</option>
                `);
            } else {
                $status.html(`
                    <option value="Active"${selectedStatus === 'Active' ? ' selected' : ''}>Active</option>
                    <option value="Discontinued"${selectedStatus === 'Discontinued' ? ' selected' : ''}>Discontinued</option>
                `);
            }
        }

        // Populate status dropdown when Add Fruit modal is shown
        $('#productModal').on('show.bs.modal', function (e) {
            // If editing, use the current status; otherwise, default to Active
            let selectedStatus = 'Active';
            let isDiscontinued = false;
            const currentStatus = $('#status').data('current-status');
            if (currentStatus) {
                selectedStatus = currentStatus;
                isDiscontinued = (currentStatus === 'Discontinued');
            }
            populateStatusDropdown(selectedStatus, isDiscontinued);
            $('#productForm')[0].reset();
            $('#priceWithVAT').text('0.00');
        });

        // When clicking edit, set the current status as a data attribute
        $(document).on('click', '.edit-btn', function() {
            const productId = $(this).data('id');
            // Fetch product details via AJAX
            $.get('products_inventory.php', { action: 'get_product', id: productId }, function(response) {
                if (response.success && response.data) {
                    const product = response.data;
                    // Set modal fields
                    $('#formAction').val('edit');
                    $('#productId').val(product.product_id);
                    $('#productName').val(product.name);
                    $('#variant').val(product.variant || '');
                    $('#size').val(product.size || '');
                    $('#cost').val(product.cost);
                    $('#price').val(product.price);
                    $('#initialStock').val(product.stock);
                    // Status dropdown logic
                    let isDiscontinued = (product.status === 'Discontinued');
                    populateStatusDropdown(product.status, isDiscontinued);
                    $('#status').val(isDiscontinued ? 'Discontinued' : product.status);
                    // Robust date formatting
                    let dateVal = '';
                    if (product.date_added) {
                        let parts = product.date_added.split(' ');
                        if (parts.length === 2) {
                            dateVal = parts[0] + 'T' + parts[1].slice(0,5);
                        } else {
                            dateVal = parts[0] + 'T00:00';
                        }
                    }
                    $('#dateAdded').val(dateVal);
                    $('#dateAddedDisplay').val(formatDateForDisplay(dateVal));
                    $('#productFormAlert').html('');
                    $('#productModalLabel').text('Edit Fruit');
                    // Set VAT display
                    const basePrice = parseFloat(product.price) / 1.12;
                    const priceWithVAT = parseFloat(product.price);
                    $('#price').val(basePrice.toFixed(2));
                    $('#priceWithVAT').text(priceWithVAT.toFixed(2));
                    // Show modal
                    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('productModal'));
                    modal.show();
                } else {
                    showAlert('Failed to fetch product details.', 'danger');
                }
            }, 'json');
        });

        // When clicking Add Fruit, clear the data attribute
        $(document).on('click', '[data-bs-target="#productModal"][data-action="add"]', function() {
            $('#status').removeData('current-status');
            // Set today's date for display and hidden
            const now = new Date();
            const iso = now.toISOString().slice(0, 10) + 'T' + now.toTimeString().slice(0,5);
            $('#dateAddedDisplay').val(formatDateForDisplay(iso));
            $('#dateAdded').val(iso);
        });

        // Add Fruit button handler
        $('#saveProductBtn').on('click', async function() {
            const $form = $('#productForm');
            // Remove previous alerts in the modal
            $('#productFormAlert').html('');
            // ... field validation ...
            let isValid = true;
            $form.find('.is-invalid').removeClass('is-invalid');
            $form.find('.invalid-feedback').remove();
            $form.find('[required]').each(function() {
                if (!this.value || (this.type === 'number' && this.value < 0)) {
                    isValid = false;
                    $(this).addClass('is-invalid');
                    $(this).after('<div class="invalid-feedback d-block"><i class="bi bi-exclamation-triangle-fill text-warning me-1"></i> This field is required.</div>');
                }
            });
            if (!isValid) {
                $form[0].reportValidity();
                return;
            }
            // Set price to VAT-inclusive value before submit
            const basePrice = parseFloat($('#price').val()) || 0;
            const priceWithVAT = (basePrice * 1.12).toFixed(2);
            $('#price').val(priceWithVAT);
            const formData = new FormData($form[0]);
            try {
                const response = await fetch('products_inventory.php', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();
                if (data.success) {
                    // Show success message in modal
                    $('#productFormAlert').html('<div class="alert alert-success alert-dismissible fade show" role="alert"><i class="bi bi-check-circle-fill text-success me-2"></i>Fruit added successfully!<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
                    setTimeout(() => { const modal = bootstrap.Modal.getInstance(document.getElementById('productModal')); if (modal) modal.hide(); window.location.reload(); }, 1200);
                } else {
                    // Show error message in modal
                    $('#productFormAlert').html('<div class="alert alert-danger alert-dismissible fade show" role="alert"><i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>' + (data.message || 'Failed to add fruit.') + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
                }
            } catch (error) {
                $('#productFormAlert').html('<div class="alert alert-danger alert-dismissible fade show" role="alert"><i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>Failed to add fruit. Please try again.<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
            }
        });

        // Show notification alert after adding fruit (after reload)
        if (localStorage.getItem('fruitAdded')) {
            showAlert('<i class="bi bi-check-circle-fill text-success me-2"></i>Fruit added successfully!', 'success');
            localStorage.removeItem('fruitAdded');
        }

        // Helper to title-case a string
        function toTitleCase(str) {
            return str.replace(/\w\S*/g, function(txt) {
                return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
            });
        }

        // Auto-standardize fruit name and variant fields as user types
        $('#productName, #variant').on('input', function() {
            const caret = this.selectionStart;
            this.value = toTitleCase(this.value);
            this.setSelectionRange(caret, caret);
        });

        // Also standardize before form submit
        $('#saveProductBtn').on('click', async function() {
            // Standardize before validation/submit
            $('#productName').val(toTitleCase($('#productName').val()));
            $('#variant').val(toTitleCase($('#variant').val()));
            $('#size').val(toTitleCase($('#size').val()));
            // ... existing code ...
        });
    });

    // Redirect to products inventory page when the Sale Recorded modal is closed
    $('#printConfirmModal').on('hidden.bs.modal', function () {
        window.location.href = 'products_inventory.php';
    });

    // Helper to recalculate and update payment summary in step 2
    function updatePaymentSummary() {
        let total = 0;
        let subtotal = 0;
        let vat = 0;
        $('.item-row').each(function() {
            const $row = $(this);
            const $select = $row.find('.product-select');
            const $quantity = $row.find('.quantity-input');
            if ($select.val() && $quantity.val() && !$quantity.hasClass('is-invalid')) {
                const quantity = parseInt($quantity.val()) || 0;
                const priceWithVAT = parseFloat($select.find('option:selected').data('price')) || 0;
                const itemTotal = priceWithVAT * quantity;
                const itemSubtotal = priceWithVAT / 1.12 * quantity;
                const itemVAT = itemTotal - itemSubtotal;
                total += itemTotal;
                subtotal += itemSubtotal;
                vat += itemVAT;
            }
        });
        $('#paymentSubtotal').text(subtotal.toFixed(2));
        $('#paymentVAT').text(vat.toFixed(2));
        $('#paymentTotalWithVAT').text(total.toFixed(2));
        // Update change
        const tendered = parseFloat($('#paymentTendered').val()) || 0;
        const change = tendered - total;
        $('#paymentChange').text(change >= 0 ? change.toFixed(2) : '0.00');
        // Validate amount tendered for confirm button
        validateAmountTendered();
    }

    // Enable/disable Confirm Payment button based on amount tendered
    function validateAmountTendered() {
        const tendered = parseFloat($('#paymentTendered').val()) || 0;
        const totalWithVAT = parseFloat($('#paymentTotalWithVAT').text()) || 0;
        const $confirmBtn = $('#confirmPaymentStep');
        
        if (tendered >= totalWithVAT && totalWithVAT > 0) {
            $confirmBtn.prop('disabled', false);
            $('#paymentTendered').removeClass('is-invalid');
        } else {
            $confirmBtn.prop('disabled', true);
            if (tendered > 0) {
                $('#paymentTendered').addClass('is-invalid');
            } else {
                $('#paymentTendered').removeClass('is-invalid');
            }
        }
    }

    // When entering step 2, always recalculate and validate
    $('#nextToStep2, #backToStep1').on('click', function() {
        setTimeout(updatePaymentSummary, 0);
        setTimeout(validateAmountTendered, 0);
    });

    // Also recalculate and validate when amount tendered changes
    $('#paymentTendered').on('input', function() {
        updatePaymentSummary();
        validateAmountTendered();
    });

    // If user changes items and goes back to step 2, recalculate and validate
    $(document).on('input change', '.product-select, .quantity-input', function() {
        if ($('#saleStep2').is(':visible')) {
            updatePaymentSummary();
            validateAmountTendered();
        }
    });

    // Status Confirmation Modal
    $('#statusConfirmModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        const status = button.data('status');
        const message = button.data('message');
        const modal = $(this);
        modal.find('.modal-title').text('Confirm Status Change');
        modal.find('.modal-body').text(message);
        modal.find('#confirmStatusBtn').data('status', status);
    });

    // Confirm status change
    $('#confirmStatusBtn').on('click', function() {
        const status = $(this).data('status');
        // Add your logic to update the status of the selected product
        showAlert('Status updated successfully!', 'success');
        $('#statusConfirmModal').modal('hide');
    });

    // Function to validate stock items
    function validateStockItems() {
        let isValid = true;
        $('.stock-item').each(function() {
            const productSelect = $(this).find('.stock-product-select');
            const quantity = $(this).find('.stock-quantity');
            
            if (!productSelect.val() || !quantity.val() || quantity.val() < 1) {
                isValid = false;
                return false;
            }
        });
        
        const dateAdded = $('#stockDate').val();
        if (!dateAdded) {
            isValid = false;
        }
        
        $('#saveStockBtn').prop('disabled', !isValid);
        return isValid;
    }

    // Function to update current stock display
    function updateCurrentStock(selectElement) {
        const productId = $(selectElement).val();
        const stockItem = $(selectElement).closest('.stock-item');
        const stockDisplay = stockItem.find('.current-stock');
        
        if (productId) {
            $.get('products_inventory.php', {
                action: 'get_stock_details',
                product_id: productId
            }, function(response) {
                if (response.success) {
                    const totalStock = response.data.reduce((sum, batch) => sum + batch.remaining, 0);
                    stockDisplay.text(`Current Stock: ${totalStock}`);
                }
            });
        } else {
            stockDisplay.text('');
        }
    }

    // Helper to get formatted date string (e.g., May 16, 2025)
    function getFormattedToday() {
        const today = new Date();
        return today.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }

    // Helper to get YYYY-MM-DD format
    function getISODateToday() {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    // Initialize stock modal
    $('#addStockModal').on('show.bs.modal', function() {
        // Reset form
        $('#stockItemsContainer').html(`
            <div class="stock-item mb-3 p-3 border rounded">
                <div class="row">
                    <div class="col-md-5">
                        <label class="form-label">Fruit</label>
                        <select class="form-select stock-product-select" required>
                            <option value="">Select a fruit</option>
                        </select>
                        <div class="current-stock text-muted small mt-1"></div>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">Quantity to Add</label>
                        <input type="number" class="form-control stock-quantity" min="1" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">&nbsp;</label>
                        <!-- No delete button for the first row -->
                    </div>
                </div>
            </div>
        `);
        // Populate product selects
        $('.stock-product-select').each(function() {
            populateProductSelect($(this));
        });
        // Set today's formatted date for display and ISO for hidden
        $('#stockDateDisplay').val(getFormattedToday());
        $('#stockDate').val(getISODateToday());
        // Reset validation
        validateStockItems();
    });

    // Add new stock item
    $('#addStockItemBtn').on('click', function() {
        const newItem = $(
            `<div class="stock-item mb-3 p-3 border rounded">
                <div class="row">
                    <div class="col-md-5">
                        <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">Fruit</label>
                        <select class="form-select stock-product-select" required>
                            <option value="">Select a fruit</option>
                        </select>
                        <div class="stock-indicator text-muted small mt-1"></div>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label" style="visibility:hidden;height:0;margin:0;padding:0;">Quantity to Add</label>
                        <input type="number" class="form-control stock-quantity" min="1" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-danger btn-sm d-block w-100 remove-stock-item">
                            <i class="bi bi-trash"></i> Remove
                        </button>
                    </div>
                </div>
            </div>`
        );
        $('#stockItemsContainer').append(newItem);
        populateProductSelect(newItem.find('.stock-product-select'));
        // Show remove buttons only for additional rows
        $('.remove-stock-item').show();
        validateStockItems();
    });

    // Remove stock item
    $(document).on('click', '.remove-stock-item', function() {
        $(this).closest('.stock-item').remove();
        // Hide remove buttons if only one item left
        if ($('.stock-item').length === 1) {
            $('.remove-stock-item').hide();
        }
        validateStockItems();
    });

    // Handle product selection change
    $(document).on('change', '.stock-product-select', function() {
        updateCurrentStock(this);
        validateStockItems();
    });

    // Handle quantity change
    $(document).on('input', '.stock-quantity', function() {
        validateStockItems();
    });

    // Handle date change
    $('#stockDate').on('change', function() {
        validateStockItems();
    });

    // Save stock
    $('#saveStockBtn').on('click', async function() {
        if (!validateStockItems()) {
            return;
        }
        
        const items = [];
        $('.stock-item').each(function() {
            const productId = $(this).find('.stock-product-select').val();
            const quantity = $(this).find('.stock-quantity').val();
            if (productId && quantity) {
                items.push({
                    product_id: productId,
                    quantity: parseInt(quantity)
                });
            }
        });
        
        const dateAdded = $('#stockDate').val();
        
        try {
            const formData = new FormData();
            formData.append('action', 'add_stock');
            formData.append('items', JSON.stringify(items));
            formData.append('date_added', dateAdded);
            
            const response = await fetch('products_inventory.php', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            const data = await response.json();
            if (data.success) {
                $('#addStockFormAlert').html(`
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <i class="bi bi-check-circle-fill text-success me-2"></i>${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `);
                
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addStockModal'));
                    if (modal) modal.hide();
                    window.location.reload();
                }, 1200);
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            $('#addStockFormAlert').html(`
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="bi bi-exclamation-circle-fill text-danger me-2"></i>${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `);
        }
    });

    // Stock Details Modal logic
    $(document).on('click', '.stock-details-icon', async function() {
        const productId = $(this).data('product-id');
        const $modal = $('#stockDetailsModal');
        const $alert = $('#stockDetailsAlert');
        const $tableBody = $('#stockDetailsTable tbody');
        const $productInfo = $('#stockDetailsProductInfo');
        $alert.html('');
        $tableBody.html('<tr><td colspan="4" class="text-center text-muted">Loading...</td></tr>');
        $productInfo.html('');
        $modal.modal('show');

        // Try to get product info from the row
        const $row = $(this).closest('tr');
        const name = $row.find('.fruit-name').text().trim();
        const size = $row.find('td').eq(2).text().trim();
        $productInfo.html(`<strong>Fruit:</strong> ${name} <span class="text-muted">(${size})</span>`);

        try {
            const response = await $.get('products_inventory.php', {
                action: 'get_stock_details',
                product_id: productId
            });
            if (response.success && response.data.length > 0) {
                $tableBody.html('');
                response.data.forEach(batch => {
                    const date = new Date(batch.date_added);
                    const formattedDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
                    $tableBody.append(`
                        <tr>
                            <td>${batch.batch_id}</td>
                            <td>${formattedDate}</td>
                            <td>${batch.quantity}</td>
                            <td>${batch.remaining}</td>
                        </tr>
                    `);
                });
            } else {
                $tableBody.html('<tr><td colspan="4" class="text-center text-muted">No stock batches found for this fruit.</td></tr>');
            }
        } catch (error) {
            $alert.html('<div class="alert alert-danger">Failed to load stock details. Please try again.</div>');
            $tableBody.html('<tr><td colspan="4" class="text-center text-danger">Error loading data</td></tr>');
        }
    });

    // Add JS handler for status-btn
    $(document).on('click', '.status-btn', function(e) {
        e.preventDefault();
        e.stopPropagation(); // Prevent event bubbling
        
        const productId = $(this).data('id');
        const newStatus = $(this).data('status');
        const $row = $(this).closest('tr, .product-card');
        const productName = $row.find('.fruit-name').text().trim();
        const currentStatus = $row.find('.badge').text().trim();
        const isDiscontinue = newStatus === 'Discontinued';
        
        // Update modal content
        $('#statusConfirmModalLabel').text(isDiscontinue ? 'Discontinue Product' : 'Recontinue Product');
        $('#statusConfirmTitle').text(isDiscontinue ? 'Discontinue this product?' : 'Recontinue this product?');
        $('#statusConfirmMessage').html(
            isDiscontinue 
                ? 'This will hide the product from active inventory. You can recontinue it later if needed.'
                : 'This will make the product visible in active inventory again.'
        );
        
        // Update product details
        $('#statusProductName').text(productName);
        $('#statusCurrentStatus')
            .text(currentStatus)
            .removeClass('bg-success bg-danger bg-secondary')
            .addClass(currentStatus === 'Active' ? 'bg-success' : 'bg-danger');
        
        // Update new status badge
        $('#statusNewStatus')
            .text(newStatus)
            .removeClass('bg-success bg-danger bg-warning')
            .addClass(isDiscontinue ? 'bg-danger' : 'bg-success');
        
        // Update button styles and text
        const confirmBtn = $('#confirmStatusBtn');
        confirmBtn
            .removeClass('btn-warning btn-success btn-danger')
            .addClass(isDiscontinue ? 'btn-danger' : 'btn-success')
            .data('product-id', productId)
            .data('status', newStatus)
            .html(`<i class="bi bi-check-circle me-2"></i>Confirm Status`);
        
        // Clear any existing alerts
        const alertElement = $('#statusConfirmAlert');
        alertElement.addClass('d-none').removeClass('alert-success alert-danger');
        
        // Show the modal
        $('#statusConfirmModal').modal('show');
    });

    // Single handler for confirm status button
    $(document).on('click', '#confirmStatusBtn', async function() {
        const productId = $(this).data('product-id');
        const newStatus = $(this).data('status');
        const isDiscontinue = newStatus === 'Discontinued';
        const alertElement = $('#statusConfirmAlert');
        const confirmButton = $(this);
        const modal = $('#statusConfirmModal');
        
        // Show loading state
        confirmButton.prop('disabled', true)
            .html('<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...');
        
        try {
            const formData = new FormData();
            formData.append('action', 'update_status');
            formData.append('product_id', productId);
            formData.append('status', newStatus);
            
            const response = await fetch('products_inventory.php', {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            
            const data = await response.json();
            if (data.success) {
                // Show success message in modal
                alertElement
                    .removeClass('d-none alert-danger')
                    .addClass('alert-success')
                    .html(`
                        <div class="d-flex">
                            <i class="bi bi-check-circle-fill"></i>
                            <div>
                                <strong>Success!</strong>
                                <div>${isDiscontinue ? 'Product has been discontinued' : 'Product has been recontinued'} successfully.</div>
                            </div>
                        </div>
                    `);
                
                // Update button to show success
                confirmButton
                    .removeClass('btn-danger btn-success')
                    .addClass('btn-success')
                    .html('<i class="bi bi-check-circle me-2"></i>Done');
                
                // Close modal after a short delay
                setTimeout(() => {
                    modal.modal('hide');
                    // Refresh the page
                    window.location.reload();
                }, 1500);
            } else {
                // Show error message in modal
                alertElement
                    .removeClass('d-none alert-success')
                    .addClass('alert-danger')
                    .html(`
                        <div class="d-flex">
                            <i class="bi bi-exclamation-circle-fill"></i>
                            <div>
                                <strong>Error!</strong>
                                <div>${data.message || 'Failed to update status. Please try again.'}</div>
                            </div>
                        </div>
                    `);
                
                // Reset button state
                confirmButton.prop('disabled', false)
                    .html(`<i class="bi bi-check-circle me-2"></i>Confirm Status`);
            }
        } catch (error) {
            console.error('Status update error:', error);
            // Show error message in modal
            alertElement
                .removeClass('d-none alert-success')
                .addClass('alert-danger')
                .html(`
                    <div class="d-flex">
                        <i class="bi bi-exclamation-circle-fill"></i>
                        <div>
                            <strong>Error!</strong>
                            <div>An unexpected error occurred. Please try again.</div>
                        </div>
                    </div>
                `);
            
            // Reset button state
            confirmButton.prop('disabled', false)
                .html(`<i class="bi bi-check-circle me-2"></i>Confirm Status`);
        }
    });

    // Reset modal state when closed
    $('#statusConfirmModal').on('hidden.bs.modal', function() {
        const alertElement = $('#statusConfirmAlert');
        const confirmButton = $('#confirmStatusBtn');
        
        alertElement.addClass('d-none').removeClass('alert-success alert-danger');
        confirmButton.prop('disabled', false)
            .html(`<i class="bi bi-check-circle me-2"></i>Confirm Status`);
    });
    </script>

    <!-- Status Confirmation Modal -->
    <div class="modal fade" id="statusConfirmModal" tabindex="-1" aria-labelledby="statusConfirmModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="statusConfirmModalLabel">Confirm Status Change</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="statusConfirmAlert" class="alert d-none mb-3" role="alert"></div>
                    <div class="status-icon">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                    </div>
                    <h5 class="text-center mb-3" id="statusConfirmTitle">Confirm Status Change</h5>
                    <p class="text-center mb-4" id="statusConfirmMessage"></p>
                    <div class="status-details">
                        <p><strong>Product:</strong> <span id="statusProductName"></span></p>
                        <p><strong>Current Status:</strong> <span id="statusCurrentStatus" class="badge"></span></p>
                        <p><strong>New Status:</strong> <span id="statusNewStatus" class="badge"></span></p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-light" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn" id="confirmStatusBtn">
                        <i class="bi bi-check-circle me-2"></i>Confirm Status
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Stock Details Modal -->
    <div class="modal fade" id="stockDetailsModal" tabindex="-1" aria-labelledby="stockDetailsModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="stockDetailsModalLabel">Stock Details</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-2 text-secondary small"><i class="bi bi-info-circle"></i> Oldest stock is used first (FIFO: First-In, First-Out). This helps keep your inventory fresh!</div>
            <div id="stockDetailsAlert"></div>
            <div id="stockDetailsProductInfo" class="mb-3"></div>
            <div class="table-responsive">
              <table class="table table-bordered align-middle" id="stockDetailsTable">
                <thead class="table-light">
                  <tr>
                    <th>Serial Number</th>
                    <th>Date Added</th>
                    <th>Quantity</th>
                    <th>Remaining</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Accessibility: return focus to first .stock-details-icon after closing Stock Details modal -->
    <script>
    $('#stockDetailsModal').on('hidden.bs.modal', function () {
      $('.stock-details-icon').first().focus();
    });
    </script>

    <!-- Inventory table stock column sorting -->
    <script>
    let stockSortOrder = 'desc'; // default sort order
    $(document).on('click', 'th.sortable[data-sort="stock"]', function() {
      // Toggle sort order
      stockSortOrder = (stockSortOrder === 'desc') ? 'asc' : 'desc';
      // Update icon
      const $icon = $(this).find('.sort-icon');
      $('.sort-icon').removeClass('bi-sort-up bi-sort-down').addClass('bi');
      if (stockSortOrder === 'desc') {
        $icon.removeClass('bi').addClass('bi-sort-down');
      } else {
        $icon.removeClass('bi').addClass('bi-sort-up');
      }
      // Sort table rows
      const $tbody = $('#inventoryTable tbody');
      const $rows = $tbody.find('tr').get();
      $rows.sort(function(a, b) {
        const stockA = parseInt($(a).find('.stock-value').text()) || 0;
        const stockB = parseInt($(b).find('.stock-value').text()) || 0;
        return (stockSortOrder === 'desc') ? stockB - stockA : stockA - stockB;
      });
      $.each($rows, function(idx, row) {
        $tbody.append(row);
      });
    });
    // On page load, set the default sort icon
    $(function() {
      $('th.sortable[data-sort="stock"] .sort-icon').addClass('bi bi-sort-down');
    });
    </script>

    <script>
    function formatDateForDisplay(dateStr) {
        if (!dateStr) return '';
        let d = new Date(dateStr.replace(' ', 'T'));
        if (isNaN(d.getTime())) return '';
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }
    </script>

    <script>
    let nameSortOrder = 'asc';
    $(document).on('click', 'th.sortable[data-sort="name"]', function() {
        nameSortOrder = (nameSortOrder === 'asc') ? 'desc' : 'asc';
        // Update icon
        const $icon = $(this).find('.sort-icon');
        $('.sort-icon').removeClass('bi-sort-alpha-down bi-sort-alpha-up').addClass('bi');
        if (nameSortOrder === 'asc') {
            $icon.removeClass('bi').addClass('bi-sort-alpha-down');
        } else {
            $icon.removeClass('bi').addClass('bi-sort-alpha-up');
        }
        // Sort table rows
        const $tbody = $('#inventoryTable tbody');
        const $rows = $tbody.find('tr').get();
        $rows.sort(function(a, b) {
            const nameA = $(a).find('.fruit-name').text().toUpperCase();
            const nameB = $(b).find('.fruit-name').text().toUpperCase();
            if (nameA < nameB) return (nameSortOrder === 'asc') ? -1 : 1;
            if (nameA > nameB) return (nameSortOrder === 'asc') ? 1 : -1;
            return 0;
        });
        $.each($rows, function(idx, row) {
            $tbody.append(row);
        });
    });
    // On page load, set the default name sort icon
    $(function() {
        $('th.sortable[data-sort="name"] .sort-icon').addClass('bi bi-sort-alpha-down');
    });
    </script>

    <script>
    // ... existing code ...
    $(document).on('click', '.sort-option', function() {
        const sortBy = $(this).data('sort');
        const sortOrder = $(this).data('order');
        // Update dropdown label
        let label = 'Sort by: ';
        if (sortBy === 'name') label += 'Name';
        else if (sortBy === 'date_added' && sortOrder === 'desc') label += 'Date Added (Newest First)';
        else if (sortBy === 'date_added' && sortOrder === 'asc') label += 'Date Added (Oldest First)';
        $('#sortDropdown').html(label + ' <span class="caret"></span>');
        // Get all cards
        const $cards = $('#productsGrid .col').get();
        $cards.sort(function(a, b) {
            let aVal, bVal;
            if (sortBy === 'name') {
                aVal = $(a).find('.fruit-name').text().trim().toUpperCase();
                bVal = $(b).find('.fruit-name').text().trim().toUpperCase();
            } else if (sortBy === 'date_added') {
                aVal = new Date($(a).find('.card-text.text-muted').text().replace('Added on: ', '').trim());
                bVal = new Date($(b).find('.card-text.text-muted').text().replace('Added on: ', '').trim());
            }
            if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
        $.each($cards, function(idx, card) {
            $('#productsGrid').append(card);
        });
    });
    // ... existing code ...
    </script>

    <!-- 1. Refresh button logic -->
    <script>
    $('#refreshInventory').on('click', function() {
        const $btn = $(this);
        $btn.prop('disabled', true);
        $btn.html('<span class="spinner-border spinner-border-sm"></span> Refreshing...');
        setTimeout(() => { window.location.reload(); }, 800);
    });
    // 2. Sidebar toggle logic
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
    // 3. Search bar logic
    $('#globalSearch').on('input', function() {
        const query = $(this).val().toLowerCase().trim();
        let count = 0;
        let seenProducts = new Set(); // Track unique products

        $('#inventoryTable tbody tr').each(function() {
            const $row = $(this);
            const id = $row.find('td').first().text().trim();
            const nameText = $row.find('.fruit-name').clone().children().remove().end().text().trim().toLowerCase();
            const variant = $row.find('.fruit-name').find('span, i').text().toLowerCase();
            const size = $row.find('td').eq(2).text().toLowerCase();
            let match = false;

            // For numeric queries, only match exact product ID
            if (!isNaN(query)) {
                match = (id === query);
            } else {
                // For text queries, match name, variant, or size
                const fullName = nameText + (variant ? ' ' + variant : '');
                match = fullName.includes(query) || size.includes(query);
            }

            // Only show if we haven't seen this product ID before
            if (match && !seenProducts.has(id)) {
                $row.show();
                seenProducts.add(id);
                count++;
            } else {
                $row.hide();
            }
        });

        $('#inventoryCount').text(count + ' fruits');
    });

    $('#searchBtn').on('click', function() {
        $('#globalSearch').trigger('input');
    });
    </script>
    <!-- Prevent duplicate fruits in the interface (Products tab) -->
    <script>
    (function() {
        const seen = {};
        $('#productsGrid .col').each(function() {
            const $col = $(this);
            const id = $col.find('.card-title').attr('id');
            if (id) {
                const productId = id.replace('product-', '');
                if (seen[productId]) {
                    $col.remove();
                } else {
                    seen[productId] = true;
                }
            }
        });
    })();
    </script>
    <!-- Prevent duplicate fruits in both inventory table and products grid -->
    <script>
    (function() {
        // Function to remove duplicates from inventory table
        function removeTableDuplicates() {
            const seen = new Set();
            $('#inventoryTable tbody tr').each(function() {
                const $row = $(this);
                const id = $row.find('td').first().text().trim();
                if (seen.has(id)) {
                    $row.remove();
                } else {
                    seen.add(id);
                }
            });
            // Update count after removing duplicates
            $('#inventoryCount').text(seen.size + ' fruits');
        }

        // Function to remove duplicates from products grid
        function removeGridDuplicates() {
            const seen = new Set();
            $('#productsGrid .col').each(function() {
                const $col = $(this);
                const id = $col.find('.card-title').attr('id')?.replace('product-', '');
                if (id) {
                    if (seen.has(id)) {
                        $col.remove();
                    } else {
                        seen.add(id);
                    }
                }
            });
        }

        // Remove duplicates on page load
        $(document).ready(function() {
            removeTableDuplicates();
            removeGridDuplicates();
        });

        // Also remove duplicates when search is performed
        $('#globalSearch').on('input', function() {
            setTimeout(removeTableDuplicates, 0);
        });

        // Remove duplicates when sorting
        $('.sort-option').on('click', function() {
            setTimeout(removeGridDuplicates, 0);
        });

        // Remove duplicates when stock sorting
        $('th.sortable[data-sort="stock"]').on('click', function() {
            setTimeout(removeTableDuplicates, 0);
        });

        // Remove duplicates when name sorting
        $('th.sortable[data-sort="name"]').on('click', function() {
            setTimeout(removeTableDuplicates, 0);
        });
    })();
    </script>

    <script>
    // ... existing code ...

    // Helper to get display text for selected fruit
    function getFruitDisplayText(option) {
        const productId = option.val();
        const name = option.data('name') || '';
        const variant = option.data('variant') ? ` (${option.data('variant')})` : '';
        const size = option.data('size') ? ` (${option.data('size')})` : '';
        return `#${productId} ${name}${variant}${size}`.trim();
    }

    // On change, update the selected option's text to only show the short format
    $(document).on('change', '.product-select, .stock-product-select', function() {
        const $select = $(this);
        $select.find('option').each(function() {
            // Restore all options to full text
            const $opt = $(this);
            if ($opt.data('fulltext')) {
                $opt.text($opt.data('fulltext'));
            }
        });
        const $selected = $select.find('option:selected');
        if ($selected.val()) {
            // Save full text if not already saved
            if (!$selected.data('fulltext')) {
                $selected.data('fulltext', $selected.text());
            }
            // Set display text to short format
            $selected.text($selected.data('display'));
        }
    });

    // When opening the dropdown, restore all options to full text
    $(document).on('focus', '.product-select, .stock-product-select', function() {
        $(this).find('option').each(function() {
            const $opt = $(this);
            if ($opt.data('fulltext')) {
                $opt.text($opt.data('fulltext'));
            }
        });
    });

    // When dynamically populating selects, ensure data attributes are set
    function populateProductSelect($select) {
        fetch('products_inventory.php?action=get_active_products', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const products = data.data;
                const currentValue = $select.val();
                $select.html('<option value="">Select a fruit</option>');
                products.forEach(product => {
                    const variant = product.variant ? `(${product.variant})` : '';
                    const size = product.size ? `(${product.size})` : '';
                    const price = product.price ? `(₱${parseFloat(product.price).toFixed(2)})` : '';
                    const stock = product.stock !== undefined ? `(Current Stock: ${product.stock})` : '';
                    const optionText = `#${product.product_id} ${product.name} ${variant} ${size} ${price} ${stock}`.replace(/  +/g, ' ').trim();
                    const displayText = `${product.name} ${variant} ${size}`.replace(/  +/g, ' ').trim();
                    const option = $('<option>', {
                        value: product.product_id,
                        text: optionText,
                        'data-stock': product.stock,
                        'data-price': product.price,
                        'data-name': product.name,
                        'data-variant': product.variant || '',
                        'data-size': product.size || '',
                        'data-display': displayText,
                        'data-fulltext': optionText
                    });
                    $select.append(option);
                });
                $select.val(currentValue);
            }
        });
    }

    // On modal show, repopulate selects with correct data attributes
    $('#buyModal').on('show.bs.modal', function () {
        // Set today's formatted date
        $('#purchaseDate').val(getFormattedToday());
        $('input[name="purchase_date"]').val(getFormattedToday());
        
        // Populate product selects
        $('.product-select').each(function() {
            populateProductSelect($(this));
        });
        // Ensure step indicator is set to first step
        updateSaleStepIndicator(1);
    });

    // ... existing code ...
    </script>

    <!-- Print receipt button handler -->
    <script>
    $('#printReceiptAfterBtn').on('click', function() {
        const saleId = $('#transactionNumber').text();
        if (!saleId) {
            showAlert('danger', 'No sale ID found. Please try again.');
            return;
        }
        printReceipt(saleId);
    });

    // ... existing code ...

    function printReceipt(saleId) {
        // First check if user can print
        fetch(`products_inventory.php?action=check_print_limit&sale_id=${saleId}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (!data.data.can_print) {
                    $('#printLimitModal').modal('show');
                    return;
                }
                // Proceed with printing
                const printWindow = window.open('', '_blank');
                const receiptContent = $('.receipt-container').clone();
                // Remove any focus/outline for print
                receiptContent.find(':focus').blur();
                // Add print-specific styles
                const printStyles = `
                    <style>
                        @media print {
                            body {
                                font-family: 'Courier New', Courier, monospace;
                                padding: 0;
                                margin: 0;
                                width: 80mm;
                            }
                            .receipt-container {
                                width: 100%;
                                max-width: none;
                                box-shadow: none;
                                border: none;
                                padding: 0;
                            }
                            .receipt-header {
                                text-align: center;
                                margin-bottom: 8px;
                            }
                            .receipt-header img {
                                max-width: 80px;
                                height: auto;
                            }
                            .company-name {
                                font-size: 1.1em;
                                font-weight: bold;
                                margin: 4px 0;
                            }
                            .company-details {
                                font-size: 0.95em;
                                margin: 2px 0;
                            }
                            .receipt-title {
                                font-size: 1.1em;
                                font-weight: bold;
                                text-align: center;
                                margin: 8px 0 4px 0;
                                letter-spacing: 1px;
                            }
                            .receipt-divider {
                                border-top: 1px dashed #000;
                                margin: 6px 0;
                            }
                            .receipt-info {
                                font-size: 0.95em;
                                margin-bottom: 2px;
                                display: flex;
                                justify-content: space-between;
                            }
                            .receipt-info-label {
                                font-weight: bold;
                                margin-right: 8px;
                            }
                            .receipt-table {
                                width: 100%;
                                font-size: 0.95em;
                                border-collapse: collapse;
                                margin: 6px 0;
                            }
                            .receipt-table th {
                                text-align: left;
                                padding: 2px 0;
                                border-bottom: 1px solid #000;
                            }
                            .receipt-table td {
                                padding: 2px 0;
                            }
                            .receipt-table .align-right {
                                text-align: right;
                            }
                            .receipt-summary {
                                font-size: 0.95em;
                                margin: 6px 0;
                            }
                            .receipt-summary-row {
                                display: flex;
                                justify-content: space-between;
                                margin: 2px 0;
                            }
                            .receipt-summary-row.total {
                                font-weight: bold;
                                margin-top: 4px;
                            }
                            .receipt-footer {
                                text-align: center;
                                margin-top: 15px;
                                font-size: 12px;
                            }
                            .no-print {
                                display: none !important;
                            }
                        }
                    </style>
                `;
                printWindow.document.write(`
                    <!DOCTYPE html>
                    <html>
                        <head>
                            <title>Receipt</title>
                            ${printStyles}
                        </head>
                        <body>
                            ${receiptContent.html()}
                        </body>
                    </html>
                `);
                printWindow.document.close();
                printWindow.focus();
                printWindow.print();
                printWindow.close();

                // Record the print after successful printing
                console.log('Recording print for sale ID:', saleId);
                fetch(`products_inventory.php?action=record_print&sale_id=${saleId}`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => {
                    console.log('Print record response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Print record response:', data);
                    if (!data.success) {
                        console.error('Failed to record print:', data.message);
                    }
                })
                .catch(error => {
                    console.error('Error recording print:', error);
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
    // ... existing code ...
    </script>

    <!-- Add sidebar overlay for mobile drawer -->
    <div id="sidebarOverlay" onclick="$('.sidebar').removeClass('active');$('#sidebarOverlay').hide();"></div>
    <!-- Back to Top Button -->
    <button id="backToTopBtn" title="Back to top" aria-label="Back to top">
        <i class="bi bi-arrow-up"></i>
    </button>
    <script>
    // ... existing code ...
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
    // ... existing code ...
    </script>

    <script>
    // ... existing code ...
    // Add this to the JS after let currentStep = 1; ...
    function updateSaleStepIndicator(step) {
        for (let i = 1; i <= 3; i++) {
            const el = document.getElementById('stepIndicator' + i);
            if (!el) continue;
            el.classList.remove('active', 'completed');
            if (i < step) el.classList.add('completed');
            else if (i === step) el.classList.add('active');
        }
    }
    // After each currentStep = ... assignment in the modal JS, call:
    // updateSaleStepIndicator(currentStep);
    // ... existing code ...
    </script>

    <script>
    // ... existing code ...
    // Add this JS to dynamically set the header text
    function updateFruitHeader() {
        var itemCount = $('#paymentTableItems tr').length;
        $('#fruitHeader').text(itemCount === 1 ? 'Fruit' : 'Fruits');
    }
    // Call this after updating paymentTableItems
    $(document).on('DOMSubtreeModified', '#paymentTableItems', updateFruitHeader);
    // ... existing code ...
    </script>

    <script>
    // ... existing code ...
    // After updating paymentTableItems, add the class to Quantity cells
    $(function() {
        const paymentTable = document.getElementById('paymentTableItems');
        if (paymentTable) {
            const observer = new MutationObserver(function(mutationsList, observer) {
                // Add class to Quantity cells
                $('#paymentTableItems tr').each(function() {
                    $(this).find('td').eq(1).addClass('quantity-col text-center');
                });
                // Update header
                var itemCount = $('#paymentTableItems tr').length;
                $('#fruitHeader').text(itemCount === 1 ? 'Fruit' : 'Fruits');
            });
            observer.observe(paymentTable, { childList: true, subtree: true });
        }
    });
    // ... existing code ...
    </script>

    <!-- Update stock indicator for Add Stock modal -->
    <script>
    $(document).on('change', '.stock-product-select', function() {
        const $select = $(this);
        const $indicator = $select.closest('.col-md-5').find('.stock-indicator');
        const $selected = $select.find('option:selected');
        if ($selected.val()) {
            const stock = parseInt($selected.data('stock')) || 0;
            const priceWithVAT = parseFloat($selected.data('price')) || 0;
            $indicator.html(`
                <div class="text-${stock < 10 ? 'danger' : (stock <= 30 ? 'warning' : 'success')}">
                    <i class="bi bi-${stock < 10 ? 'exclamation-triangle-fill' : (stock <= 30 ? 'exclamation-circle-fill' : 'check-circle-fill')}"></i>
                    Current Stock: ${stock} boxes
                </div>
                <div class="text-muted small">Price: ₱${priceWithVAT.toFixed(2)} (VAT inclusive)</div>
            `);
        } else {
            $indicator.html('');
        }
    });
    </script>

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

    <script>
    // Helper to standardize text (remove numbers, special chars, and format properly)
    function standardizeText(str) {
        // Keep numbers, letters, and hyphens, only remove other special characters
        str = str.replace(/[^a-zA-Z0-9\s-]/g, '');
        // Convert to title case but preserve numbers and hyphens
        return str.replace(/\w\S*/g, function(txt) {
            // If the word starts with a number or hyphen, keep it as is
            if (/^[\d-]/.test(txt)) return txt;
            // Otherwise convert to title case
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }

    // Function to check if product exists
    async function checkProductExists(name, variant, size, productId = null) {
        try {
            const response = await fetch('products_inventory.php?action=check_product_exists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    name: name,
                    variant: variant || null,
                    size: size || null, // Allow null/empty size
                    product_id: productId
                })
            });
            const data = await response.json();
            return data.exists;
        } catch (error) {
            console.error('Error checking product:', error);
            return false;
        }
    }

    // Handle name and variant fields with standardization
    $('#productName, #variant').on('input', async function() {
        const $field = $(this);
        const originalValue = $field.val();
        const caret = this.selectionStart;
        
        // Standardize the text
        const standardizedValue = standardizeText(originalValue, this.id);
        $field.val(standardizedValue);
        
        // Restore cursor position
        const newCaret = caret + (standardizedValue.length - originalValue.length);
        this.setSelectionRange(newCaret, newCaret);

        // Check for duplicates
        const name = $('#productName').val();
        const variant = $('#variant').val() || null;
        const size = $('#size').val() || null; // Allow empty size
        const productId = $('#productId').val();

        if (name) { // Only require name for duplicate check
            const exists = await checkProductExists(name, variant, size, productId);
            if (exists) {
                showFormAlert('A fruit with this name, variant, and size already exists.', 'warning', 'productModal');
                $('#saveProductBtn').prop('disabled', true);
            } else {
                $('#productFormAlert').empty();
                $('#saveProductBtn').prop('disabled', false);
            }
        }
    });

    // Handle size field without standardization
    $('#size').on('input', async function() {
        // Only check for duplicates
        const name = $('#productName').val();
        const variant = $('#variant').val() || null;
        const size = $(this).val() || null; // Allow empty size
        const productId = $('#productId').val();

        if (name) { // Only require name for duplicate check
            const exists = await checkProductExists(name, variant, size, productId);
            if (exists) {
                showFormAlert('A fruit with this name, variant, and size already exists.', 'warning', 'productModal');
                $('#saveProductBtn').prop('disabled', true);
            } else {
                $('#productFormAlert').empty();
                $('#saveProductBtn').prop('disabled', false);
            }
        }
    });

    // Also validate before form submission
    $('#saveProductBtn').on('click', async function(e) {
        e.preventDefault();
        const name = $('#productName').val();
        const variant = $('#variant').val();
        const size = $('#size').val();
        const productId = $('#productId').val();

        // Standardize all fields before submission
        $('#productName').val(standardizeText(name, 'text'));
        $('#variant').val(standardizeText(variant, 'text'));
        $('#size').val(standardizeText(size, 'size'));

        // Check for duplicates
        const exists = await checkProductExists(name, variant, size, productId);
        if (exists) {
            showFormAlert('A fruit with this name, variant, and size already exists.', 'warning', 'productModal');
            return;
        }

        // If no duplicates, proceed with form submission
        const $form = $('#productForm');
        if ($form[0].checkValidity()) {
            // ... existing form submission code ...
        } else {
            $form[0].reportValidity();
            showFormAlert('Please fill in all required fields correctly.', 'danger', 'productModal');
        }
    });

    // Reset form and alerts when modal is closed
    $('#productModal').on('hidden.bs.modal', function() {
        $('#productFormAlert').empty();
        $('#saveProductBtn').prop('disabled', false);
    });

    // Remove size from the combined input handler
    $('#productName, #variant').on('input', async function() {
        const $field = $(this);
        const originalValue = $field.val();
        const caret = this.selectionStart;
        
        // Standardize the text
        const standardizedValue = standardizeText(originalValue, this.id);
        $field.val(standardizedValue);
        
        // Restore cursor position
        const newCaret = caret + (standardizedValue.length - originalValue.length);
        this.setSelectionRange(newCaret, newCaret);

        // Check for duplicates
        const name = $('#productName').val();
        const variant = $('#variant').val();
        const size = $('#size').val();
        const productId = $('#productId').val();

        if (name && size) {
            const exists = await checkProductExists(name, variant, size, productId);
            if (exists) {
                showFormAlert('A fruit with this name, variant, and size already exists.', 'warning', 'productModal');
                $('#saveProductBtn').prop('disabled', true);
            } else {
                $('#productFormAlert').empty();
                $('#saveProductBtn').prop('disabled', false);
            }
        }
    });

    // Separate handler for size field without standardization
    $('#size').on('input', async function() {
        // Only check for duplicates
        const name = $('#productName').val();
        const variant = $('#variant').val();
        const size = $(this).val();
        const productId = $('#productId').val();

        if (name && size) {
            const exists = await checkProductExists(name, variant, size, productId);
            if (exists) {
                showFormAlert('A fruit with this name, variant, and size already exists.', 'warning', 'productModal');
                $('#saveProductBtn').prop('disabled', true);
            } else {
                $('#productFormAlert').empty();
                $('#saveProductBtn').prop('disabled', false);
            }
        }
    });

    // Modify form submission to not standardize size
    $('#saveProductBtn').on('click', async function(e) {
        e.preventDefault();
        const name = $('#productName').val();
        const variant = $('#variant').val();
        const size = $('#size').val();
        const productId = $('#productId').val();

        // Only standardize name and variant
        $('#productName').val(standardizeText(name, 'text'));
        $('#variant').val(standardizeText(variant, 'text'));
        // Size is left as-is without standardization

        // Check for duplicates
        const exists = await checkProductExists(name, variant, size, productId);
        if (exists) {
            showFormAlert('A fruit with this name, variant, and size already exists.', 'warning', 'productModal');
            return;
        }

        // If no duplicates, proceed with form submission
        const $form = $('#productForm');
        if ($form[0].checkValidity()) {
            // ... existing form submission code ...
        } else {
            $form[0].reportValidity();
            showFormAlert('Please fill in all required fields correctly.', 'danger', 'productModal');
        }
    });
</script>
</body>
</html>