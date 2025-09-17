<?php
// login.php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
include 'config.php';

// Initialize error message
$error = '';
if (isset($_SESSION['redirect_reason'])) {
    $error = "Redirected: " . $_SESSION['redirect_reason'];
    unset($_SESSION['redirect_reason']);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim(filter_input(INPUT_POST, 'username'));
    $password = trim(filter_input(INPUT_POST, 'password'));

    error_log("Login attempt - Username: '$username', Password length: " . strlen($password));

    if (empty($username) || empty($password)) {
        $error = "Username and password are required.";
        error_log("Login.php - Error: Username or password empty");
    } else {
        try {
            $stmt = $pdo->prepare("SELECT user_id, username, password, role, last_login, last_active, is_active, status FROM users WHERE username = ?");
            $stmt->execute([$username]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            error_log("Login.php - Query executed for username: '$username', User found: " . ($user ? 'Yes' : 'No'));

            if ($user) {
                // First check if account is disabled
                if ($user['status'] === 'disabled') {
                    $error = "Your account is disabled. Please contact the administrator.";
                    error_log("Login.php - Disabled account attempted login: $username");
                    // Clear any existing session data
                    session_unset();
                    session_destroy();
                } else if (password_verify($password, $user['password'])) {
                    // Double check status again before allowing login
                    $stmt = $pdo->prepare("SELECT status FROM users WHERE user_id = ? AND status = 'enabled'");
                    $stmt->execute([$user['user_id']]);
                    if (!$stmt->fetch()) {
                        $error = "Your account is disabled. Please contact the administrator.";
                        error_log("Login.php - Account became disabled during login attempt: $username");
                        session_unset();
                        session_destroy();
                    } else {
                        $_SESSION['user_id'] = $user['user_id'];
                        $_SESSION['username'] = $user['username'];
                        $_SESSION['role'] = $user['role'];
                        // Update last_login and last_active to NOW()
                        if ($user['role'] === 'user') {
                            $stmt = $pdo->prepare("UPDATE users SET last_login = NOW(), last_active = NOW(), is_active = 1 WHERE user_id = ? AND status = 'enabled'");
                            $stmt->execute([$user['user_id']]);
                            error_log("Login.php - Secretary login successful. User ID: {$user['user_id']}, Username: $username");
                        } else {
                            $stmt = $pdo->prepare("UPDATE users SET last_login = NOW(), last_active = NOW() WHERE user_id = ? AND status = 'enabled'");
                            $stmt->execute([$user['user_id']]);
                            error_log("Login.php - Admin login successful. User ID: {$user['user_id']}, Username: $username");
                        }
                        header("Location: dashboard.php");
                        exit;
                    }
                } else {
                    $error = "Password is incorrect.";
                    error_log("Login.php - Password verification failed for username: $username. Stored hash: {$user['password']}, Input password length: " . strlen($password));
                }
            } else {
                $error = "Username not found.";
                error_log("Login.php - No user found for username: '$username'");
            }
        } catch (PDOException $e) {
            $error = "Database error: " . $e->getMessage();
            error_log("Login.php - Database error: " . $e->getMessage());
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWise - Login</title>
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
        }

        body {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }

        .login-card {
            max-width: 400px;
            width: 100%;
            padding: 30px;
            border: none;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            background: #fff;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .login-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }

        .login-card h3 {
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-card h3 i {
            margin-right: 10px;
            color: var(--primary);
        }

        .form-control {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            transition: all 0.3s ease;
        }

        .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }

        .btn-primary {
            background: var(--primary);
            border: none;
            border-radius: 8px;
            padding: 10px;
            transition: all 0.3s ease;
            width: 100%;
        }

        .btn-primary:hover {
            background: #e85959;
            transform: translateY(-1px);
        }

        .alert {
            border-radius: 8px;
            padding: 12px;
            font-size: 0.9rem;
        }

        .form-label {
            font-weight: 500;
            color: #495057;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h3><i class="bi bi-basket-fill fs-4" aria-hidden="true"></i> STOCKWISE LOGIN</h3>
        <?php if ($error): ?>
            <div class="alert alert-danger alert-dismissible fade show">
                <?php echo htmlspecialchars($error); ?>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        <?php endif; ?>
        <form method="POST">
            <div class="mb-3">
                <label for="username" class="form-label">Username</label>
                <input type="text" class="form-control" id="username" name="username" required>
                <div class="invalid-feedback">Please enter your username.</div>
            </div>
            <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" name="password" required>
                <div class="invalid-feedback">Please enter your password.</div>
            </div>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('form');
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    form.classList.add('was-validated');
                }
            });
        });
    </script>
</body>
</html>