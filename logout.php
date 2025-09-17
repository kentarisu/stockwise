<?php
// logout.php
include 'config.php';
session_start();

if (isset($_SESSION['user_id'])) {
    // Fetch user role
    $stmt = $pdo->prepare("SELECT role, status FROM users WHERE user_id = ?");
    $stmt->execute([$_SESSION['user_id']]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    // Set last_active to 10 minutes ago so user appears offline, but last active time is preserved
    $stmt = $pdo->prepare("UPDATE users SET last_active = DATE_SUB(NOW(), INTERVAL 10 MINUTE) WHERE user_id = ?");
    $stmt->execute([$_SESSION['user_id']]);
    // Only update is_active, preserving the status field
    if ($row) {
        $stmt = $pdo->prepare("UPDATE users SET is_active = 0 WHERE user_id = ?");
        $stmt->execute([$_SESSION['user_id']]);
        error_log("Logout.php - User {$row['role']} logged out. Status: {$row['status']}, is_active set to 0");
    }
}
// Destroy the session
session_unset();
session_destroy();

// Redirect to login page
header("Location: login.php");
exit;
?>