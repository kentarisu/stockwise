<?php
// Prevent direct access to template
if (!isset($user)) {
    header("Location: login.php");
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Profile</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        :root {
            --primary: #ff6b6b;
            --primary-light: rgba(255, 107, 107, 0.1);
            --success: #51cf66;
            --success-light: rgba(81, 207, 102, 0.1);
            --danger: #ff3f34;
            --danger-light: rgba(255, 63, 52, 0.1);
            --warning: #fcc419;
            --warning-light: rgba(252, 196, 25, 0.1);
            --dark: #212529;
            --sidebar-width: 280px;
            --sidebar-collapsed-width: 80px;
            --topbar-height: 70px;
            --radius: 0.75rem;
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
            left: 0;
            top: 0;
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
                transform: translateX(-100%);
                width: min(var(--sidebar-width), 80vw);
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
                background: rgba(0, 0, 0, 0.5);
                z-index: 1020;
            }
            #sidebarOverlay.active {
                display: block;
            }
            .sidebar-close-btn {
                display: block;
                position: absolute;
                top: 10px;
                right: 10px;
                background: transparent;
                border: none;
                color: white;
                font-size: 1.5rem;
                padding: 5px;
                cursor: pointer;
                z-index: 1031;
            }
            #content {
                margin-left: 0 !important;
                width: 100vw !important;
                max-width: 100vw !important;
                padding: 0.5rem 0.5rem 1.5rem 0.5rem !important;
            }
        }

        /* Additional improvements for very small screens */
        @media (max-width: 576px) {
            .container-fluid {
                padding: 0.5rem !important;
            }

            .card {
                border-radius: 8px;
            }

            .card-header {
                padding: 0.75rem;
            }

            .card-body {
                padding: 0.75rem !important;
            }

            .profile-picture {
                width: 70px !important;
                height: 70px !important;
            }

            .btn {
                padding: 0.25rem 0.5rem;
                font-size: 0.85rem;
            }

            .form-control, .form-select {
                font-size: 0.85rem;
                padding: 0.25rem 0.5rem;
            }

            .modal-dialog {
                margin: 0.25rem;
            }

            .modal-body {
                padding: 0.75rem;
            }

            .modal-footer {
                padding: 0.75rem;
            }

            /* Improve text readability */
            .fw-medium {
                font-size: 0.9rem;
            }

            small.text-muted {
                font-size: 0.75rem;
            }

            /* Adjust spacing */
            .mb-3 {
                margin-bottom: 0.75rem !important;
            }

            .mb-2 {
                margin-bottom: 0.5rem !important;
            }

            /* Improve form layout */
            .form-label {
                font-size: 0.9rem;
                margin-bottom: 0.25rem;
            }

            /* Adjust icons */
            .bi {
                font-size: 0.9rem;
            }

            /* Improve dropdown menu */
            .dropdown-menu {
                min-width: 180px;
                font-size: 0.85rem;
            }

            .dropdown-item {
                padding: 0.4rem 0.75rem;
            }

            /* Improve alert messages */
            .alert {
                font-size: 0.8rem;
                padding: 0.5rem;
            }

            /* Adjust profile info spacing */
            .row.align-items-center.mb-3 {
                margin-bottom: 0.75rem !important;
            }

            .col-md-4.text-center {
                margin-bottom: 0.75rem !important;
            }
        }

        /* Improve sidebar backdrop for mobile */
        .sidebar-backdrop {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1030;
        }

        @media (max-width: 768px) {
            .sidebar-backdrop.active {
                display: block;
            }
        }

        /* Fixed Navbar Styles */
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

        /* Back to Top Button Styles */
        #backToTopBtn {
            display: none;
            position: fixed;
            bottom: 32px;
            right: 32px;
            z-index: 9999;
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

        /* Refresh Button Styles */
        #refreshProfile {
            transition: all 0.3s ease;
        }

        #refreshProfile:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }

        #refreshProfile .spinner-border {
            width: 1rem;
            height: 1rem;
            margin-right: 0.5rem;
        }

        /* Mobile Navbar Adjustments */
        @media (max-width: 768px) {
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
                <li>
                    <a href="dashboard.php"><i class="bi bi-speedometer2 me-2" aria-hidden="true"></i><span>Dashboard</span></a>
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
                <li class="active">
                    <a href="profile.php" aria-current="page"><i class="bi bi-person me-2" aria-hidden="true"></i><span>Profile</span></a>
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
                    <button type="button" id="sidebarCollapseNavbar" class="btn btn-light me-2" aria-label="Toggle sidebar" title="Show/hide sidebar">
                        <i class="bi bi-list" aria-hidden="true"></i>
                    </button>
                    <div class="ms-auto d-flex align-items-center">
                        <div class="dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                <img src="<?php echo $user['profile_picture'] ? htmlspecialchars($user['profile_picture']) : 'https://via.placeholder.com/32'; ?>" class="rounded-circle" width="32" height="32" alt="User">
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end shadow">
                                <li><a class="dropdown-item" href="profile.php"><i class="bi bi-person me-2"></i>Profile</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="logout.php"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </nav>
            <div class="container-fluid">
                <div id="alertContainer">
                    <?php if ($error): ?>
                        <div class="alert alert-danger alert-dismissible fade show">
                            <?php echo htmlspecialchars($error); ?>
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    <?php endif; ?>
                    <?php if (!empty($errors)): ?>
                        <?php foreach ($errors as $err): ?>
                            <div class="alert alert-danger alert-dismissible fade show">
                                <?php echo htmlspecialchars($err); ?>
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h2 class="mb-1 fw-bold">Profile</h2>
                        <p class="text-muted">Manage your account settings and preferences.</p>
                    </div>
                    <div class="col-md-6 text-md-end d-flex justify-content-md-end align-items-center flex-wrap gap-2">
                        <button class="btn btn-outline-secondary" id="refreshProfile" aria-label="Refresh profile data" title="Reload profile data">
                            <i class="bi bi-arrow-clockwise me-1"></i> Refresh
                        </button>
                    </div>
                </div>
                <div class="row g-4 justify-content-center">
                    <div class="col-lg-6">
                        <div class="container" style="max-width:900px;margin:0 auto;">
                        <!-- Account Information Card (all info in one card) -->
                        <div class="card mb-4 shadow-sm">
                            <div class="card-header bg-light">
                                <h5 class="card-title mb-0"><i class="bi bi-shield-lock me-2"></i>Account Information</h5>
                            </div>
                            <div class="card-body">
                                <!-- First row: Profile Picture | Info -->
                                <div class="row align-items-center mb-3">
                                    <div class="col-md-4 text-center mb-3 mb-md-0">
                                        <!-- View-only profile picture, opens modal for larger view -->
                                        <img src="<?php echo $user['profile_picture'] ? htmlspecialchars($user['profile_picture']) : 'https://via.placeholder.com/200'; ?>" alt="Profile Picture" class="profile-picture mb-2 shadow" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%; border: 3px solid #dee2e6; cursor: pointer; transition: box-shadow 0.2s;" data-bs-toggle="modal" data-bs-target="#profilePictureModal">
                                    </div>
                                    <div class="col-md-8">
                                        <div class="mb-2">
                                            <span class="fw-medium"><i class="bi bi-person-vcard me-2"></i>Name:</span>
                                            <span><?php echo htmlspecialchars($user['name']); ?></span>
                                        </div>
                                        <div class="mb-2">
                                            <span class="fw-medium"><i class="bi bi-person me-2"></i>Username:</span>
                                            <span><?php echo htmlspecialchars($user['username']); ?></span>
                                        </div>
                                        <div class="mb-2">
                                            <span class="fw-medium"><i class="bi bi-telephone me-2"></i>Phone Number:</span>
                                            <span><?php echo htmlspecialchars($user['phone_number'] ?? ''); ?></span>
                                        </div>
                                        <div class="mb-2">
                                            <span class="fw-medium"><i class="bi bi-person-badge me-2"></i>Role:</span>
                                            <span><?php echo ($user['role'] === 'user') ? 'Secretary' : ucfirst(htmlspecialchars($user['role'])); ?></span>
                                        </div>
                                    </div>
                                </div>
                                <!-- Second row: Account Created | Last Login -->
                                <div class="row g-3 mb-3">
                                    <div class="col-md-6">
                                        <div class="d-flex align-items-center mb-2">
                                            <i class="bi bi-calendar-check me-2 text-primary"></i>
                                            <div>
                                                <small class="text-muted d-block">Account Created</small>
                                                <span class="fw-medium"><?php echo htmlspecialchars($user['created_at_formatted']); ?></span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="d-flex align-items-center mb-2">
                                            <i class="bi bi-clock-history me-2 text-primary"></i>
                                            <div>
                                                <small class="text-muted d-block">Last Login</small>
                                                <span class="fw-medium"><?php echo htmlspecialchars($user['last_login_formatted']); ?></span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="text-end mt-3">
                                    <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#editProfileModal">
                                        <i class="bi bi-pencil me-2"></i>Edit Profile
                                    </button>
                                </div>
                            </div>
                        </div>
                        </div>
                    </div>
                    <?php if ($user['role'] === 'admin' && !empty($user['all_users'])): ?>
                    <div class="col-lg-6">
                        <!-- Secretary's Account Information Card -->
                        <div class="card mb-4 shadow-sm">
                            <div class="card-header bg-light">
                                <h5 class="card-title mb-0"><i class="bi bi-shield-lock me-2"></i>Secretary's Account Information</h5>
                            </div>
                            <div class="card-body">
                                <div class="row g-4">
                                    <?php foreach ($user['all_users'] as $u): ?>
                                    <?php if ($u['user_id'] == $_SESSION['user_id'] || $u['role'] !== 'user') continue; ?>
                                    <div class="col-12">
                                        <div class="card mb-3 shadow-sm border-0">
                                            <div class="card-body">
                                                <!-- First row: Profile Picture | Info -->
                                                <div class="row align-items-center mb-3">
                                                    <div class="col-md-4 text-center mb-3 mb-md-0">
                                                        <img src="<?php echo $u['profile_picture'] ? htmlspecialchars($u['profile_picture']) : 'https://via.placeholder.com/200'; ?>" alt="Profile Picture" class="profile-picture mb-2 shadow" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%; border: 3px solid #dee2e6; cursor: pointer; transition: box-shadow 0.2s;" data-bs-toggle="modal" data-bs-target="#profilePictureModal">
                                                    </div>
                                                    <div class="col-md-8">
                                                        <div class="mb-2">
                                                            <span class="fw-medium"><i class="bi bi-person-vcard me-2"></i>Name:</span>
                                                            <span><?php echo htmlspecialchars($u['name']); ?></span>
                                                        </div>
                                                        <div class="mb-2">
                                                            <span class="fw-medium"><i class="bi bi-person me-2"></i>Username:</span>
                                                            <span><?php echo htmlspecialchars($u['username']); ?></span>
                                                        </div>
                                                        <div class="mb-2">
                                                            <span class="fw-medium"><i class="bi bi-telephone me-2"></i>Phone Number:</span>
                                                            <span><?php echo htmlspecialchars($u['phone_number'] ?? ''); ?></span>
                                                        </div>
                                                        <div class="mb-2">
                                                            <span class="fw-medium"><i class="bi bi-person-badge me-2"></i>Role:</span>
                                                            <span>Secretary</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <!-- Second row: Account Created | Last Login -->
                                                <div class="row g-3 mb-3">
                                                    <div class="col-md-6">
                                                        <div class="d-flex align-items-center mb-2">
                                                            <i class="bi bi-calendar-check me-2 text-primary"></i>
                                                            <div>
                                                                <small class="text-muted d-block">Account Created</small>
                                                                <span class="fw-medium"><?php echo isset($u['created_at']) ? htmlspecialchars(date('F j, Y g:i A', strtotime($u['created_at']))) : '-'; ?></span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="col-md-6">
                                                        <div class="d-flex align-items-center mb-2">
                                                            <i class="bi bi-clock-history me-2 text-primary"></i>
                                                            <div>
                                                                <small class="text-muted d-block">Last Login</small>
                                                                <span class="fw-medium"><?php echo $u['last_login'] ? date('F j, Y g:i A', strtotime($u['last_login'])) : 'Never'; ?></span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <!-- Status and Action Buttons -->
                                                <div class="mb-2">
                                                    <span class="fw-medium"><i class="bi bi-circle me-2"></i>Status:</span>
                                                    <?php $is_online = isset($u['last_active']) && (strtotime($u['last_active']) >= strtotime('-5 minutes')); ?>
                                                    <span class="badge <?php echo $is_online ? 'bg-success' : 'bg-secondary'; ?>">
                                                        <?php echo $is_online ? 'Online' : 'Offline'; ?>
                                                    </span>
                                                </div>
                                                <div class="text-end mt-3">
                                                    <button type="button" class="btn btn-<?php echo $u['status'] === 'enabled' ? 'danger' : 'success'; ?> me-2 toggle-active-btn" data-user-id="<?php echo $u['user_id']; ?>" data-active="<?php echo $u['status'] === 'enabled' ? 1 : 0; ?>" data-role="<?php echo htmlspecialchars($u['role']); ?>" data-phone="<?php echo htmlspecialchars($u['phone_number'] ?? ''); ?>">
                                                        <i class="bi bi-<?php echo $u['status'] === 'enabled' ? 'person-x' : 'person-check'; ?> me-2"></i><?php echo $u['status'] === 'enabled' ? 'Disable' : 'Enable'; ?>
                                                    </button>
                                                    <button type="button" class="btn btn-primary edit-user-btn" data-user-id="<?php echo $u['user_id']; ?>" data-username="<?php echo htmlspecialchars($u['username']); ?>" data-name="<?php echo htmlspecialchars($u['name']); ?>" data-role="<?php echo htmlspecialchars($u['role']); ?>" data-is-active="<?php echo $u['status'] === 'enabled' ? 1 : 0; ?>" data-phone="<?php echo htmlspecialchars($u['phone_number'] ?? ''); ?>">
                                                        <i class="bi bi-pencil me-2"></i>Edit Profile
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        </div>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>

    <!-- Edit Profile Modal -->
    <div class="modal fade" id="editProfileModal" tabindex="-1" aria-labelledby="editProfileModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="editProfileModalLabel"><i class="bi bi-person-gear fs-5"></i> Edit Profile</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="alertContainer">
                        <?php if ($success): ?>
                            <div class="alert alert-success alert-dismissible fade show mb-3">
                                <i class="bi bi-check-circle-fill text-success me-2"></i><?php echo htmlspecialchars($success); ?>
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        <?php endif; ?>
                        <?php if (!empty($errors)): ?>
                            <?php foreach ($errors as $err): ?>
                                <div class="alert alert-danger alert-dismissible fade show mb-3">
                                    <?php echo htmlspecialchars($err); ?>
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </div>
                    <form id="updateProfileForm" method="POST" enctype="multipart/form-data">
                        <div class="text-center mb-3">
                            <label for="profile_picture" style="cursor:pointer;display:block;">
                                <img id="profilePicturePreview" src="<?php echo $user['profile_picture'] ? htmlspecialchars($user['profile_picture']) : 'https://via.placeholder.com/200'; ?>" alt="Profile Picture Preview" class="profile-picture mb-2 shadow" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%; border: 3px solid #dee2e6; cursor: pointer; transition: box-shadow 0.2s;">
                                <div class="fw-medium mt-1">Edit Profile Picture</div>
                            </label>
                            <input type="file" class="form-control mt-2 d-none" id="profile_picture" name="profile_picture" accept="image/jpeg,image/png">
                        </div>
                        <div class="mb-3">
                            <label for="editName" class="form-label fw-medium"><i class="bi bi-person-vcard me-2"></i>Name</label>
                            <input type="text" class="form-control" id="editName" name="name" value="<?php echo htmlspecialchars($user['name']); ?>" required autocomplete="name">
                        </div>
                        <div class="mb-3">
                            <label for="username" class="form-label fw-medium"><i class="bi bi-person me-2"></i>Username</label>
                            <input type="text" class="form-control" id="username" name="username" value="<?php echo htmlspecialchars($user['username']); ?>" required autocomplete="username">
                            <div class="invalid-feedback">Username is required.</div>
                        </div>
                        <div class="mb-3">
                            <label for="editPhoneNumber" class="form-label fw-medium"><i class="bi bi-telephone me-2"></i>Phone Number</label>
                            <input type="text" class="form-control" id="editPhoneNumber" name="phone_number" value="<?php echo htmlspecialchars($user['phone_number'] ?? ''); ?>" pattern="[0-9+\-() ]*" maxlength="20" autocomplete="tel">
                        </div>
                        <div class="mb-3">
                            <label for="editRole" class="form-label fw-medium"><i class="bi bi-person-badge me-2"></i>Role</label>
                            <input type="text" class="form-control" id="editRole" value="<?php echo ($user['role'] === 'user') ? 'Secretary' : ucfirst(htmlspecialchars($user['role'])); ?>" readonly>
                        </div>
                        <div class="mb-3">
                            <div class="input-group mb-2">
                                <input type="password" class="form-control" id="current_password" name="current_password" placeholder="Current Password" autocomplete="current-password">
                                <button type="button" class="input-group-text toggle-password" data-target="current_password"><i class="bi bi-eye"></i></button>
                            </div>
                            <div class="input-group mb-2">
                                <input type="password" class="form-control" id="new_password" name="new_password" placeholder="New Password" autocomplete="new-password">
                                <button type="button" class="input-group-text toggle-password" data-target="new_password"><i class="bi bi-eye"></i></button>
                            </div>
                            <div class="input-group">
                                <input type="password" class="form-control" id="confirm_password" name="confirm_password" placeholder="Confirm Password" autocomplete="new-password">
                                <button type="button" class="input-group-text toggle-password" data-target="confirm_password"><i class="bi bi-eye"></i></button>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary" id="saveProfileBtn">Save Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Edit User Modal -->
    <div class="modal fade" id="editUserModal" tabindex="-1" aria-labelledby="editUserModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="editUserModalLabel"><i class="bi bi-person-gear fs-5"></i> Edit User</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="adminAlertContainer">
                        <?php if ($success): ?>
                            <div class="alert alert-success alert-dismissible fade show mb-3">
                                <i class="bi bi-check-circle-fill text-success me-2"></i><?php echo htmlspecialchars($success); ?>
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        <?php endif; ?>
                        <?php if (!empty($errors)): ?>
                            <?php foreach ($errors as $err): ?>
                                <div class="alert alert-danger alert-dismissible fade show mb-3">
                                    <?php echo htmlspecialchars($err); ?>
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </div>
                    <form id="adminEditUserForm" method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="user_id" id="editUserId">
                        <div class="text-center mb-3">
                            <label for="adminEditProfilePicture" style="cursor:pointer;display:block;">
                                <img id="adminProfilePicturePreview" src="https://via.placeholder.com/200" alt="Profile Picture Preview" class="profile-picture mb-2 shadow" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%; border: 3px solid #dee2e6; cursor: pointer; transition: box-shadow 0.2s;">
                                <div class="fw-medium mt-1">Edit Profile Picture</div>
                            </label>
                            <input type="file" class="form-control mt-2 d-none" id="adminEditProfilePicture" name="profile_picture" accept="image/jpeg,image/png">
                        </div>
                        <div class="mb-3">
                            <label for="adminEditName" class="form-label fw-medium"><i class="bi bi-person-vcard me-2"></i>Name</label>
                            <input type="text" class="form-control" id="adminEditName" name="name" required autocomplete="name">
                        </div>
                        <div class="mb-3">
                            <label for="adminEditUsername" class="form-label fw-medium"><i class="bi bi-person me-2"></i>Username</label>
                            <input type="text" class="form-control" id="adminEditUsername" name="username" required autocomplete="username">
                            <div class="invalid-feedback">Username is required.</div>
                        </div>
                        <div class="mb-3">
                            <label for="adminEditPhoneNumber" class="form-label fw-medium"><i class="bi bi-telephone me-2"></i>Phone Number</label>
                            <input type="text" class="form-control" id="adminEditPhoneNumber" name="phone_number" value="<?php echo htmlspecialchars($u['phone_number'] ?? ''); ?>" pattern="[0-9+\-() ]*" maxlength="20" autocomplete="tel">
                        </div>
                        <div class="mb-3">
                            <label for="adminEditRole" class="form-label fw-medium"><i class="bi bi-person-badge me-2"></i>Role</label>
                            <input type="text" class="form-control" id="adminEditRole" value="Secretary" readonly>
                        </div>
                        <div class="mb-3">
                            <div class="input-group mb-2">
                                <input type="password" class="form-control" id="adminEditCurrentPassword" name="current_password" placeholder="Current Password" autocomplete="current-password">
                                <button type="button" class="input-group-text toggle-password" data-target="adminEditCurrentPassword"><i class="bi bi-eye"></i></button>
                            </div>
                            <div class="input-group mb-2">
                                <input type="password" class="form-control" id="adminEditNewPassword" name="new_password" placeholder="New Password" autocomplete="new-password">
                                <button type="button" class="input-group-text toggle-password" data-target="adminEditNewPassword"><i class="bi bi-eye"></i></button>
                            </div>
                            <div class="input-group">
                                <input type="password" class="form-control" id="adminEditConfirmPassword" name="confirm_password" placeholder="Confirm Password" autocomplete="new-password">
                                <button type="button" class="input-group-text toggle-password" data-target="adminEditConfirmPassword"><i class="bi bi-eye"></i></button>
                            </div>
                        </div>
                        <div class="mb-3 form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="adminEditIsActive" name="is_active" value="1">
                            <label class="form-check-label fw-medium" for="adminEditIsActive">Account Status</label>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary" id="saveUserBtn">Save Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Profile Picture Modal -->
    <div class="modal fade" id="profilePictureModal" tabindex="-1" aria-labelledby="profilePictureModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-transparent border-0">
                <div class="modal-header border-0">
                    <button type="button" class="btn-close btn-close-white ms-auto" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="<?php echo $user['profile_picture'] ? htmlspecialchars($user['profile_picture']) : 'https://via.placeholder.com/400'; ?>" alt="Profile Picture Large" style="max-width: 100%; max-height: 70vh; border-radius: 16px; box-shadow: 0 4px 32px rgba(0,0,0,0.25);">
                </div>
            </div>
        </div>
    </div>

    <!-- Add Enable/Disable Confirmation Modal -->
    <div class="modal fade" id="toggleActiveModal" tabindex="-1" aria-labelledby="toggleActiveModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="toggleActiveModalLabel"><i class="bi bi-exclamation-triangle text-warning me-2"></i>Confirm Action</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div id="toggleActiveAlertContainer"></div>
                    <span id="toggleActiveModalMessage"></span>
                    <form id="setPasswordForm" onsubmit="return false;" style="display:none; margin-top:15px;">
                        <label for="setPasswordInput" class="form-label">New Password (minimum 8 characters)</label>
                        <input type="password" class="form-control" id="setPasswordInput" minlength="8" autocomplete="new-password" required>
                        <div class="invalid-feedback">Password must be at least 8 characters.</div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="confirmToggleActiveBtn">Confirm</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Back to Top Button -->
    <button id="backToTopBtn" title="Back to top" aria-label="Back to top">
        <i class="bi bi-arrow-up"></i>
    </button>

    <!-- jQuery (required for custom scripts using $) -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Sidebar elements
            const sidebar = document.getElementById('sidebar');
            const sidebarOverlay = document.getElementById('sidebarOverlay');
            const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
            const sidebarCollapseNavbar = document.getElementById('sidebarCollapseNavbar');
            const content = document.getElementById('content');

            // Function to toggle sidebar
            function toggleSidebar() {
                if (window.innerWidth <= 768) {
                    // Mobile view
                    sidebar.classList.toggle('active');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.toggle('active');
                    }
                    document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
                } else {
                    // Desktop view
                    sidebar.classList.toggle('collapsed');
                    content.style.marginLeft = sidebar.classList.contains('collapsed') ? 
                        'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)';
                }
            }

            // Event listeners for sidebar toggle
            if (sidebarCollapseNavbar) {
                sidebarCollapseNavbar.addEventListener('click', function(e) {
                    e.preventDefault();
                    toggleSidebar();
                });
            }

            // Close sidebar when clicking overlay (mobile only)
            if (sidebarOverlay) {
                sidebarOverlay.addEventListener('click', function() {
                    if (window.innerWidth <= 768) {
                        sidebar.classList.remove('active');
                        sidebarOverlay.classList.remove('active');
                        document.body.style.overflow = '';
                    }
                });
            }

            // Close sidebar when clicking close button (mobile only)
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

            // Handle window resize
            window.addEventListener('resize', function() {
                if (window.innerWidth > 768) {
                    // Reset mobile-specific classes
                    sidebar.classList.remove('active');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.remove('active');
                    }
                    document.body.style.overflow = '';
                    
                    // Set desktop margin
                    content.style.marginLeft = sidebar.classList.contains('collapsed') ? 
                        'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)';
                } else {
                    // Reset desktop-specific classes
                    sidebar.classList.remove('collapsed');
                    content.style.marginLeft = '0';
                }
            });

            // Initial setup
            if (window.innerWidth > 768) {
                content.style.marginLeft = sidebar.classList.contains('collapsed') ? 
                    'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)';
            }

            // Initialize dropdowns
            function initializeDropdowns() {
                const dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]');
                dropdownElements.forEach(element => {
                    if (!bootstrap.Dropdown.getInstance(element)) {
                        new bootstrap.Dropdown(element);
                    }
                });
            }

            initializeDropdowns();

            function showAlert(message, type) {
                const alertContainer = document.getElementById('alertContainer');
                const alert = document.createElement('div');
                alert.className = `alert alert-${type} alert-dismissible fade show`;
                alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
                alertContainer.appendChild(alert);
                setTimeout(() => alert.remove(), 3000);
            }

            // Password toggle functionality
            document.querySelectorAll('.toggle-password').forEach(button => {
                button.addEventListener('click', function() {
                    const targetId = this.getAttribute('data-target');
                    const input = document.getElementById(targetId);
                    const icon = this.querySelector('i');

                    if (!input || !icon) {
                        console.error(`Toggle password failed: input or icon not found for target ${targetId}`);
                        return;
                    }

                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    } else {
                        input.type = 'password';
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    }
                });
            });

            const form = document.getElementById('updateProfileForm');
            const usernameInput = document.getElementById('username');
            const currentPasswordInput = document.getElementById('current_password');
            const newPasswordInput = document.getElementById('new_password');
            const confirmPasswordInput = document.getElementById('confirm_password');
            const fileInput = document.getElementById('profile_picture');

            // Profile picture preview
            fileInput.addEventListener('change', function() {
                const preview = document.getElementById('profilePicturePreview');
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    }
                    reader.readAsDataURL(this.files[0]);
                } else {
                    preview.style.display = 'none';
                }
            });

            form.addEventListener('submit', function(e) {
                let isValid = true;

                // Validate username
                if (!usernameInput.value.trim()) {
                    usernameInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    usernameInput.classList.remove('is-invalid');
                }

                // Validate name
                if (!nameInput.value.trim()) {
                    nameInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    nameInput.classList.remove('is-invalid');
                }

                // Validate phone (required, but pattern is loose)
                if (!phoneInput.value.trim()) {
                    phoneInput.classList.add('is-invalid');
                    isValid = false;
                } else {
                    phoneInput.classList.remove('is-invalid');
                }

                // Password validation: only if any password field is filled
                const currentVal = currentPasswordInput.value;
                const newVal = newPasswordInput.value;
                const confirmVal = confirmPasswordInput.value;
                if (currentVal || newVal || confirmVal) {
                    // Current password required if changing password
                    if (!currentVal) {
                        currentPasswordInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        currentPasswordInput.classList.remove('is-invalid');
                    }
                    // New password min length
                    if (!newVal || newVal.length < 8) {
                        newPasswordInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        newPasswordInput.classList.remove('is-invalid');
                    }
                    // Confirm password match
                    if (newVal !== confirmVal) {
                        confirmPasswordInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        confirmPasswordInput.classList.remove('is-invalid');
                    }
                } else {
                    currentPasswordInput.classList.remove('is-invalid');
                    newPasswordInput.classList.remove('is-invalid');
                    confirmPasswordInput.classList.remove('is-invalid');
                }

                // Validate file
                if (fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    const allowedTypes = ['image/jpeg', 'image/png'];
                    const maxSize = 2 * 1024 * 1024; // 2MB
                    if (!allowedTypes.includes(file.type)) {
                        showAlert('Only JPEG and PNG images are allowed.', 'danger');
                        isValid = false;
                    } else if (file.size > maxSize) {
                        showAlert('Image size must be less than 2MB.', 'danger');
                        isValid = false;
                    }
                }

                if (!isValid) {
                    e.preventDefault();
                    showAlert('Please fix the errors in the form.', 'danger');
                    // Scroll modal to top for error
                    const modalBody = document.querySelector('#editProfileModal .modal-body');
                    if (modalBody) modalBody.scrollTop = 0;
                    return;
                }

                // AJAX form submission
                e.preventDefault();
                const modalBody = document.querySelector('#editProfileModal .modal-body');
                // Remove any existing alerts
                modalBody.querySelectorAll('.alert').forEach(a => a.remove());
                // Prepare form data
                const formData = new FormData(form);
                saveBtn.disabled = true;
                fetch(window.location.pathname, {
                    method: 'POST',
                    body: formData,
                })
                .then(response => response.text())
                .then(html => {
                    // Try to parse for success or error
                    let success = false;
                    let message = 'Profile updated successfully!';
                    // Look for a success message in the returned HTML
                    if (html.includes('Profile updated successfully')) {
                        success = true;
                    } else if (html.indexOf('alert-danger') !== -1) {
                        // Try to extract error using DOM parsing
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const alertDiv = doc.querySelector('.alert-danger');
                        if (alertDiv) {
                            message = alertDiv.textContent.trim();
                        } else {
                            message = 'There was an error saving your profile.';
                        }
                    }
                    // Show notification with check icon for success
                    const alert = document.createElement('div');
                    alert.className = `alert alert-${success ? 'success' : 'danger'} alert-dismissible fade show mb-3`;
                    if (success) {
                        alert.innerHTML = `<i class='bi bi-check-circle-fill text-success me-2'></i>${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
                    } else {
                        alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
                    }
                    modalBody.insertBefore(alert, modalBody.firstChild);
                    modalBody.scrollTop = 0;
                    if (success) {
                        setTimeout(function() {
                            const modalInstance = bootstrap.Modal.getOrCreateInstance(document.getElementById('editProfileModal'));
                            modalInstance.hide();
                            // Optionally, refresh the page or update the profile info on the main page here
                            window.location.reload();
                        }, 1000);
                    } else {
                        saveBtn.disabled = false;
                    }
                })
                .catch(() => {
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-danger alert-dismissible fade show mb-3';
                    alert.innerHTML = 'There was an error saving your profile.<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
                    modalBody.insertBefore(alert, modalBody.firstChild);
                    modalBody.scrollTop = 0;
                    saveBtn.disabled = false;
                });
            });

            // Real-time password strength feedback
            newPasswordInput.addEventListener('input', function() {
                if (this.value.length > 0 && this.value.length < 8) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            });

            document.querySelectorAll('.edit-user-btn').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var btn = $(this);
                    var userId = btn.data('user-id');
                    var username = btn.data('username');
                    var name = btn.data('name');
                    var role = btn.data('role');
                    var isActive = btn.data('is-active');
                    var phoneNumber = btn.data('phone');
                    
                    // Pre-fill modal fields
                    $('#editUserId').val(userId);
                    $('#adminEditUsername').val(username);
                    $('#adminEditName').val(name);
                    $('#adminEditPhoneNumber').val(phoneNumber);
                    $('#adminEditRole').val('Secretary');
                    $('#adminEditCurrentPassword').val('');
                    $('#adminEditNewPassword').val('');
                    $('#adminEditConfirmPassword').val('');
                    $('#adminEditProfilePicture').val('');
                    $('#adminEditIsActive').prop('checked', !!isActive);
                    
                    // Update profile picture preview
                    var profilePicture = btn.closest('.card-body').find('.profile-picture').attr('src');
                    if (profilePicture && $('#adminProfilePicturePreview').length) {
                        $('#adminProfilePicturePreview').attr('src', profilePicture);
                    }
                    
                    $('#editUserModalLabel').html('<i class="bi bi-person-gear"></i> Edit Profile');
                    $('#editUserModal').modal('show');
                });
            });

            // Disable Save Changes button until required fields are valid
            const saveBtn = form.querySelector('button[type="submit"]');
            const nameInput = document.getElementById('editName');
            const phoneInput = document.getElementById('editPhoneNumber');

            function checkFormValidity() {
                // Require name, username, and phone number (autofilled OK)
                const isNameValid = nameInput.value.trim() !== '';
                const isUsernameValid = usernameInput.value.trim() !== '';
                const isPhoneValid = phoneInput.value.trim() !== '';
                saveBtn.disabled = !(isNameValid && isUsernameValid && isPhoneValid);
            }

            // Initial check
            checkFormValidity();

            // Listen for input changes
            nameInput.addEventListener('input', checkFormValidity);
            usernameInput.addEventListener('input', checkFormValidity);
            phoneInput.addEventListener('input', checkFormValidity);

            // Auto-fill phone number (should already be filled by PHP, but ensure it)
            phoneInput.value = phoneInput.value || <?php echo json_encode($user['phone_number'] ?? ''); ?>;

            // Profile picture preview for admin edit modal
            const adminFileInput = document.getElementById('adminEditProfilePicture');
            const adminPreview = document.getElementById('adminProfilePicturePreview');

            if (adminFileInput && adminPreview) {
                adminFileInput.addEventListener('change', function() {
                    if (this.files && this.files[0]) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            adminPreview.src = e.target.result;
                            adminPreview.style.display = 'block';
                        }
                        reader.readAsDataURL(this.files[0]);
                    } else {
                        adminPreview.style.display = 'none';
                    }
                });
            }

            // Admin Edit User Form handling
            const adminForm = document.getElementById('adminEditUserForm');
            if (adminForm) {
                adminForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const modalBody = document.querySelector('#editUserModal .modal-body');
                    const alertContainer = document.getElementById('adminAlertContainer');
                    // Remove any existing alerts
                    alertContainer.querySelectorAll('.alert').forEach(a => a.remove());
                    // Prepare form data
                    const formData = new FormData(this);
                    const saveBtn = this.querySelector('button[type="submit"]');
                    let isValid = true;
                    const adminUsernameInput = document.getElementById('adminEditUsername');
                    const adminNameInput = document.getElementById('adminEditName');
                    const adminPhoneInput = document.getElementById('adminEditPhoneNumber');
                    const adminCurrentPassword = document.getElementById('adminEditCurrentPassword');
                    const adminNewPassword = document.getElementById('adminEditNewPassword');
                    const adminConfirmPassword = document.getElementById('adminEditConfirmPassword');
                    // Validate username
                    if (!adminUsernameInput.value.trim()) {
                        adminUsernameInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        adminUsernameInput.classList.remove('is-invalid');
                    }
                    // Validate name
                    if (!adminNameInput.value.trim()) {
                        adminNameInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        adminNameInput.classList.remove('is-invalid');
                    }
                    // Validate phone
                    if (!adminPhoneInput.value.trim()) {
                        adminPhoneInput.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        adminPhoneInput.classList.remove('is-invalid');
                    }
                    // Password validation: only if any password field is filled
                    const adminCurrentVal = adminCurrentPassword.value;
                    const adminNewVal = adminNewPassword.value;
                    const adminConfirmVal = adminConfirmPassword.value;
                    if (adminCurrentVal || adminNewVal || adminConfirmVal) {
                        if (!adminCurrentVal) {
                            adminCurrentPassword.classList.add('is-invalid');
                            isValid = false;
                        } else {
                            adminCurrentPassword.classList.remove('is-invalid');
                        }
                        if (!adminNewVal || adminNewVal.length < 8) {
                            adminNewPassword.classList.add('is-invalid');
                            isValid = false;
                        } else {
                            adminNewPassword.classList.remove('is-invalid');
                        }
                        if (adminNewVal !== adminConfirmVal) {
                            adminConfirmPassword.classList.add('is-invalid');
                            isValid = false;
                        } else {
                            adminConfirmPassword.classList.remove('is-invalid');
                        }
                    } else {
                        adminCurrentPassword.classList.remove('is-invalid');
                        adminNewPassword.classList.remove('is-invalid');
                        adminConfirmPassword.classList.remove('is-invalid');
                    }
                    if (!isValid) {
                        showAlert('Please fix the errors in the form.', 'danger');
                        modalBody.scrollTop = 0;
                        saveBtn.disabled = false;
                        return;
                    }
                    saveBtn.disabled = true;
                    fetch(window.location.pathname, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.text())
                    .then(html => {
                        let success = false;
                        let message = 'User updated successfully!';
                        if (html.includes('User updated successfully')) {
                            success = true;
                        } else if (html.indexOf('alert-danger') !== -1) {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(html, 'text/html');
                            const alertDiv = doc.querySelector('.alert-danger');
                            if (alertDiv) {
                                message = alertDiv.textContent.trim();
                            } else {
                                message = 'There was an error updating the user.';
                            }
                        }
                        const alert = document.createElement('div');
                        alert.className = `alert alert-${success ? 'success' : 'danger'} alert-dismissible fade show mb-3`;
                        if (success) {
                            alert.innerHTML = `<i class="bi bi-check-circle-fill text-success me-2"></i>${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
                        } else {
                            alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
                        }
                        alertContainer.insertBefore(alert, alertContainer.firstChild);
                        modalBody.scrollTop = 0;
                        if (success) {
                            setTimeout(function() {
                                const modalInstance = bootstrap.Modal.getOrCreateInstance(document.getElementById('editUserModal'));
                                modalInstance.hide();
                                window.location.reload();
                            }, 1000);
                        } else {
                            saveBtn.disabled = false;
                        }
                    })
                    .catch(() => {
                        const alert = document.createElement('div');
                        alert.className = 'alert alert-danger alert-dismissible fade show mb-3';
                        alert.innerHTML = 'There was an error updating the user.<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
                        alertContainer.insertBefore(alert, alertContainer.firstChild);
                        modalBody.scrollTop = 0;
                        saveBtn.disabled = false;
                    });
                });
            }

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

            // Refresh profile data
            document.getElementById('refreshProfile').addEventListener('click', function() {
                const btn = this;
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                
                // Reload the entire page after a short delay to show the loading state
                setTimeout(() => {
                    window.location.reload();
                }, 800);
            });
        });
    </script>
    <script>
    $(document).ready(function() {
        // Toggle status button click handler
        $(document).on('click', '.toggle-active-btn', function(e) {
            e.preventDefault();
            const userId = $(this).data('user-id');
            const isActive = $(this).data('active');
            const status = isActive ? 'disabled' : 'enabled';
            const action = isActive ? 'disable' : 'enable';
            
            // Clear any existing alerts
            $('#toggleActiveAlertContainer').empty();
            
            // Store data for the confirmation button
            $('#confirmToggleActiveBtn')
                .data('user-id', userId)
                .data('status', status)
                .data('is-active', isActive ? 0 : 1);
            
            // Update modal content with notification
            let message = '';
            if (action === 'disable') {
                message = `<div class="alert alert-warning mb-3">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <strong>Warning:</strong> Disabling this account will prevent the secretary from logging in until it is re-enabled.
                </div>
                <p>Are you sure you want to <b>disable</b> this account?</p>`;
            } else {
                message = `<div class="alert alert-info mb-3">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    <strong>Note:</strong> You will need to set a new password to enable this account.
                </div>
                <p>Are you sure you want to <b>enable</b> this account?</p>`;
            }
            $('#toggleActiveModalMessage').html(message);
            
            // Show/hide password input for enabling accounts
            if (action === 'enable') {
                $('#setPasswordForm').show();
                $('#setPasswordInput').val('').removeClass('is-invalid');
            } else {
                $('#setPasswordForm').hide();
            }
            
            $('#toggleActiveModal').modal('show');
        });

        // Confirm toggle status button click handler
        $('#confirmToggleActiveBtn').on('click', async function() {
            const userId = $(this).data('user-id');
            const status = $(this).data('status');
            const newActive = $(this).data('is-active');
            const btn = $(this);
            const alertContainer = $('#toggleActiveAlertContainer');
            
            // Clear any existing alerts
            alertContainer.empty();
            
            // Validate password if enabling account
            if (status === 'enabled') {
                const password = $('#setPasswordInput').val();
                if (!password || password.length < 8) {
                    $('#setPasswordInput').addClass('is-invalid');
                    alertContainer.html(`<div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle-fill me-2"></i>
                        Password must be at least 8 characters long.
                    </div>`);
                    return;
                }
            }
            
            try {
                btn.prop('disabled', true);
                // Show loading state
                alertContainer.html(`<div class="alert alert-info">
                    <i class="bi bi-arrow-repeat me-2"></i>
                    Processing your request...
                </div>`);
                
                // Prepare request data
                const formData = new URLSearchParams({
                    'toggle_user_id': userId,
                    'new_active': newActive,
                    'csrf_token': '<?php echo $_SESSION['csrf_token']; ?>'
                });
                
                // Add password if enabling account
                if (status === 'enabled') {
                    formData.append('set_password', $('#setPasswordInput').val());
                }
                
                // Send request
                const response = await fetch('profile.php', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: formData
                });
                
                const text = await response.text();
                let result;
                try {
                    result = JSON.parse(text);
                } catch (e) {
                    alertContainer.html(`<div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle-fill me-2"></i>
                        Server error: ${text}
                    </div>`);
                    return;
                }
                
                if (result.success) {
                    // Show success message
                    if (status === 'disabled') {
                        alertContainer.html(`<div class="alert alert-success">
                            <i class="bi bi-check-circle-fill me-2"></i>
                            Account disabled successfully.
                        </div>`);
                    } else {
                        alertContainer.html(`<div class="alert alert-success">
                            <i class="bi bi-check-circle-fill me-2"></i>
                            Account enabled successfully with new password.
                            ${result.logout ? '<br><br><strong>Note:</strong> The secretary has been logged out and will need to log in with the new password.' : ''}
                        </div>`);
                    }
                    
                    if (result.logout) {
                        // If the current user is the one being enabled/disabled, log them out
                        setTimeout(() => {
                            window.location.href = 'logout.php';
                        }, 2000); // Give user time to read the message
                        return;
                    }
                    
                    setTimeout(() => {
                        location.reload();
                    }, 2000); // Give user time to read the message
                } else {
                    alertContainer.html(`<div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle-fill me-2"></i>
                        ${result.error || 'Failed to update user status.'}
                    </div>`);
                }
            } catch (error) {
                alertContainer.html(`<div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle-fill me-2"></i>
                    Request failed: ${error.message}
                </div>`);
            } finally {
                btn.prop('disabled', false);
            }
        });

        // Clear modal data when hidden
        $('#toggleActiveModal').on('hidden.bs.modal', function() {
            $('#confirmToggleActiveBtn')
                .removeData('user-id')
                .removeData('status')
                .removeData('is-active');
            $('#setPasswordInput').val('').removeClass('is-invalid');
            $('#toggleActiveAlertContainer').empty();
            $('#setPasswordForm').hide();
        });
    });
    </script>
</body>
</html>