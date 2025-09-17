<?php
ini_set('display_errors', 0);
ini_set('log_errors', 1);
error_reporting(E_ALL);
// profile.php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
include 'config.php';

// Ensure CSRF token is generated
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// Debug: Log session data
error_log("Profile.php - Session data: " . print_r($_SESSION, true));

// Check if user is logged in
if (!isset($_SESSION['user_id']) || empty($_SESSION['user_id'])) {
    error_log("Profile.php - Redirecting to login.php: user_id not set or empty");
    $_SESSION['redirect_reason'] = 'user_id not set or empty';
    header("Location: login.php");
    exit;
}

// Initialize messages
$success = '';
$errors = [];
$error = '';

// Fetch user details
$userId = $_SESSION['user_id'];
try {
    $stmt = $pdo->prepare("SELECT username, name, role, profile_picture, password, created_at, last_login, is_active, phone_number FROM users WHERE user_id = ?");
    $stmt->execute([$userId]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    
    error_log("Profile.php - User query result for ID $userId: " . print_r($user, true));
    
    if (!$user) {
        error_log("Profile.php - User not found for ID: $userId");
        session_unset();
        session_destroy();
        header("Location: login.php");
        exit;
    }

    // Force logout if account is disabled
    if (isset($user['status']) && $user['status'] !== 'enabled') {
        session_unset();
        session_destroy();
        header("Location: login.php?disabled=1");
        exit;
    }

    // Update last_active for real-time online status
    if (isset($_SESSION['user_id'])) {
        $stmt = $pdo->prepare("UPDATE users SET last_active = NOW() WHERE user_id = ?");
        $stmt->execute([$_SESSION['user_id']]);
    }

    // Fetch additional account information for admin users
    if ($user['role'] === 'admin') {
        // Get total number of users
        $stmt = $pdo->query("SELECT COUNT(*) FROM users");
        $user['total_users'] = $stmt->fetchColumn();

        // Get total number of active users (users active in last 5 minutes)
        $stmt = $pdo->prepare("SELECT COUNT(*) FROM users WHERE last_active >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)");
        $stmt->execute();
        $user['active_users'] = $stmt->fetchColumn();

        // Get account creation date and last login in readable format
        $user['created_at_formatted'] = date('F j, Y g:i A', strtotime($user['created_at']));
        $user['last_login_formatted'] = $user['last_login'] ? date('F j, Y g:i A', strtotime($user['last_login'])) : 'Never';

        // Fetch all users and their online status
        $stmt = $pdo->query("SELECT user_id, username, name, role, last_active, last_login, is_active, status, phone_number, profile_picture, created_at FROM users");
        $user['all_users'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
    } else {
        // For non-admins, still format dates
        $user['created_at_formatted'] = date('F j, Y g:i A', strtotime($user['created_at']));
        $user['last_login_formatted'] = $user['last_login'] ? date('F j, Y g:i A', strtotime($user['last_login'])) : 'Never';
    }
} catch (PDOException $e) {
    $errors[] = "Error fetching user data: " . $e->getMessage();
    error_log("Profile.php - Database error: " . $e->getMessage());
}

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !isset($_POST['user_id'])) {
    $name = trim($_POST['name'] ?? '');
    $username = trim($_POST['username'] ?? '');
    $phone_number = trim($_POST['phone_number'] ?? '');
    $current_password = $_POST['current_password'] ?? '';
    $new_password = $_POST['new_password'] ?? '';
    $confirm_password = $_POST['confirm_password'] ?? '';
    $profile_picture = $user['profile_picture'];

    // Validate and handle file upload as before...
    if (isset($_FILES['profile_picture']) && $_FILES['profile_picture']['error'] === UPLOAD_ERR_OK) {
        $file = $_FILES['profile_picture'];
        $allowed_types = ['image/jpeg', 'image/png'];
        $max_size = 2 * 1024 * 1024; // 2MB
        if (!in_array($file['type'], $allowed_types)) {
            $errors[] = "Only JPEG and PNG images are allowed.";
        } elseif ($file['size'] > $max_size) {
            $errors[] = "Image size must be less than 2MB.";
        } else {
            $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
            $filename = 'profile_' . $userId . '_' . time() . '.' . $ext;
            $upload_path = 'Uploads/' . $filename;
            if (move_uploaded_file($file['tmp_name'], $upload_path)) {
                $profile_picture = $upload_path;
                if ($user['profile_picture'] && file_exists($user['profile_picture'])) {
                    unlink($user['profile_picture']);
                }
                error_log("Profile.php - Profile picture uploaded: $upload_path");
            } else {
                $errors[] = "Failed to upload image.";
                error_log("Profile.php - Upload failed for path: $upload_path");
            }
        }
    } elseif ($_FILES['profile_picture']['error'] !== UPLOAD_ERR_NO_FILE) {
        $errors[] = "File upload error: " . $_FILES['profile_picture']['error'];
    }

    // Only require current password if changing password
    if (!empty($new_password)) {
        if (empty($current_password)) {
            $errors[] = "Current password is required to change your password.";
        } elseif (!password_verify($current_password, $user['password'])) {
            $errors[] = "Incorrect current password.";
        }
        if ($new_password && strlen($new_password) < 8) {
            $errors[] = "New password must be at least 8 characters long.";
        }
        if ($new_password !== $confirm_password) {
            $errors[] = "New passwords do not match.";
        }
    }

    if (empty($username)) {
        $errors[] = "Username is required.";
    }
    if (empty($name)) {
        $errors[] = "Name is required.";
    }

    // Proceed with update if no errors
    if (empty($errors)) {
        try {
            // Check for duplicate username
            $stmt = $pdo->prepare("SELECT user_id FROM users WHERE username = ? AND user_id != ?");
            $stmt->execute([$username, $userId]);
            if ($stmt->fetch()) {
                $errors[] = "Username already exists.";
            } else {
                // Build update query
                $query = "UPDATE users SET name = ?, username = ?, phone_number = ?, profile_picture = ?";
                $params = [$name, $username, $phone_number, $profile_picture];
                if (!empty($new_password)) {
                    $hashed_password = password_hash($new_password, PASSWORD_DEFAULT);
                    $query .= ", password = ?";
                    $params[] = $hashed_password;
                }
                $query .= " WHERE user_id = ?";
                $params[] = $userId;

                error_log("Profile.php - Update query: $query");
                error_log("Profile.php - Update params: " . print_r($params, true));

                $stmt = $pdo->prepare($query);
                $result = $stmt->execute($params);

                if ($result) {
                    // Update session and user data
                    $_SESSION['username'] = $username;
                    $user['username'] = $username;
                    $user['name'] = $name;
                    $user['phone_number'] = $phone_number;
                    $user['profile_picture'] = $profile_picture;
                    if (!empty($new_password)) {
                        $user['password'] = $hashed_password;
                        session_regenerate_id(true); // Prevent session fixation
                    }
                    $success = "Profile updated successfully.";
                    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
                    error_log("Profile.php - Profile updated for ID $userId: username=$username, new_password=" . (!empty($new_password) ? 'yes' : 'no'));
                } else {
                    $errors[] = "Failed to update profile in database.";
                    error_log("Profile.php - Database update failed for ID $userId");
                }
            }
        } catch (PDOException $e) {
            $errors[] = "Error updating profile: " . $e->getMessage();
            error_log("Profile.php - Update error: " . $e->getMessage());
        }
    }
    // Set $error for template
    if (!empty($errors)) {
        $error = $errors[0];
    }
}

// Handle admin edit user form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['user_id']) && $user['role'] === 'admin') {
    // Handle enable/disable secretary status
    if (isset($_POST['toggle_user_id']) && isset($_POST['new_status'])) {
        $toggleUserId = (int)$_POST['toggle_user_id'];
        $newStatus = $_POST['new_status'];
        if ($toggleUserId === $user['user_id']) {
            echo json_encode(['error' => 'You cannot disable your own account.']);
            exit;
        }
        try {
            $stmt = $pdo->prepare("UPDATE users SET status = ? WHERE user_id = ?");
            $stmt->execute([$newStatus, $toggleUserId]);
            echo json_encode(['success' => true, 'new_status' => $newStatus]);
        } catch (PDOException $e) {
            echo json_encode(['error' => 'Error updating status: ' . $e->getMessage()]);
        }
        exit;
    }
    $editUserId = $_POST['user_id'];
    $editName = trim($_POST['name'] ?? '');
    $editUsername = trim($_POST['username'] ?? '');
    $editPassword = $_POST['password'] ?? '';
    $editIsActive = isset($_POST['is_active']) ? 1 : 0;
    $editProfilePicture = null;

    // Fetch current user info
    $stmt = $pdo->prepare("SELECT profile_picture, phone_number FROM users WHERE user_id = ?");
    $stmt->execute([$editUserId]);
    $editUser = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$editUser) {
        $errors[] = "User not found.";
    } else {
        // Handle file upload
        if (isset($_FILES['profile_picture']) && $_FILES['profile_picture']['error'] === UPLOAD_ERR_OK) {
            $file = $_FILES['profile_picture'];
            $allowed_types = ['image/jpeg', 'image/png'];
            $max_size = 2 * 1024 * 1024; // 2MB
            if (!in_array($file['type'], $allowed_types)) {
                $errors[] = "Only JPEG and PNG images are allowed.";
            } elseif ($file['size'] > $max_size) {
                $errors[] = "Image size must be less than 2MB.";
            } else {
                $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
                $filename = 'profile_' . $editUserId . '_' . time() . '.' . $ext;
                $upload_path = 'Uploads/' . $filename;
                if (move_uploaded_file($file['tmp_name'], $upload_path)) {
                    $editProfilePicture = $upload_path;
                    if ($editUser['profile_picture'] && file_exists($editUser['profile_picture'])) {
                        unlink($editUser['profile_picture']);
                    }
                } else {
                    $errors[] = "Failed to upload image.";
                }
            }
        } elseif ($_FILES['profile_picture']['error'] !== UPLOAD_ERR_NO_FILE) {
            $errors[] = "File upload error: " . $_FILES['profile_picture']['error'];
        } else {
            $editProfilePicture = $editUser['profile_picture'];
        }

        if (empty($errors)) {
            try {
                $query = "UPDATE users SET name = ?, username = ?, is_active = ?";
                $params = [$editName, $editUsername, $editIsActive];
                if ($editProfilePicture) {
                    $query .= ", profile_picture = ?";
                    $params[] = $editProfilePicture;
                }
                if (!empty($editPassword)) {
                    $hashed_password = password_hash($editPassword, PASSWORD_DEFAULT);
                    $query .= ", password = ?";
                    $params[] = $hashed_password;
                }
                $query .= " WHERE user_id = ?";
                $params[] = $editUserId;
                $stmt = $pdo->prepare($query);
                $stmt->execute($params);
                $success = "User updated successfully.";
            } catch (PDOException $e) {
                $errors[] = "Error updating user: " . $e->getMessage();
            }
        }
    }
}

// Handle AJAX enable/disable user
if (
    isset($_POST['toggle_user_id'], $_POST['new_active']) &&
    $user['role'] === 'admin' &&
    isset($_SERVER['HTTP_X_REQUESTED_WITH']) &&
    strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest'
) {
    ob_clean(); // Clear any previous output
    header('Content-Type: application/json');

    // Validate CSRF token
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        echo json_encode(['error' => 'Invalid CSRF token.']);
        exit;
    }

    $toggleUserId = (int)$_POST['toggle_user_id'];
    $newActive = (int)$_POST['new_active'];

    // Prevent self-toggle for admin
    if ($toggleUserId === $user['user_id'] && $user['role'] === 'admin') {
        echo json_encode(['error' => 'You cannot toggle your own admin account.']);
        exit;
    }

    try {
        // Verify the target user exists and is a secretary
        $stmt = $pdo->prepare("SELECT role FROM users WHERE user_id = ?");
        $stmt->execute([$toggleUserId]);
        $targetUser = $stmt->fetch(PDO::FETCH_ASSOC);

        if (!$targetUser) {
            echo json_encode(['error' => 'Target user not found.']);
            exit;
        }
        if ($targetUser['role'] !== 'user') {
            echo json_encode(['error' => 'Can only toggle secretary accounts.']);
            exit;
        }

        if ($newActive === 0) {
            // Disable secretary: set both status and is_active
            $stmt = $pdo->prepare("UPDATE users SET status = 'disabled', is_active = 0 WHERE user_id = ?");
            $stmt->execute([$toggleUserId]);
            // If the disabled user is currently logged in, log them out
            $shouldLogout = false;
            if (isset($_SESSION['user_id']) && $_SESSION['user_id'] == $toggleUserId) {
                session_unset();
                session_destroy();
                $shouldLogout = true;
            }
            echo json_encode(['success' => true, 'logout' => $shouldLogout]);
        } else {
            // Enable secretary: require a new password and set status to enabled
            if (!isset($_POST['set_password']) || strlen($_POST['set_password']) < 8) {
                echo json_encode(['error' => 'A new password (min 8 chars) must be set to enable this account.']);
                exit;
            }
            $hashedPassword = password_hash($_POST['set_password'], PASSWORD_DEFAULT);
            $stmt = $pdo->prepare("UPDATE users SET status = 'enabled', password = ? WHERE user_id = ?");
            $stmt->execute([$hashedPassword, $toggleUserId]);
            
            // Check if the enabled user is currently logged in
            $shouldLogout = false;
            if (isset($_SESSION['user_id']) && $_SESSION['user_id'] == $toggleUserId) {
                session_unset();
                session_destroy();
                $shouldLogout = true;
            }
            
            echo json_encode(['success' => true, 'logout' => $shouldLogout]);                                                                                                                   
        }
    } catch (PDOException $e) {
        echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
        exit;
    }
    exit;
}

// Include the template only for non-AJAX requests
if (!(
    isset($_POST['toggle_user_id'], $_POST['new_active']) &&
    $user['role'] === 'admin' &&
    isset($_SERVER['HTTP_X_REQUESTED_WITH']) &&
    strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest'
)) {
    include 'profile_template.php';
}
?>