<?php
// Prevent multiple header sends
if (headers_sent()) {
    return;
}

// Set security headers
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('X-XSS-Protection: 1; mode=block');
header('Referrer-Policy: strict-origin-when-cross-origin');

// Set content type headers based on request type
if (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && 
    strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest') {
    // AJAX request - set JSON content type
    header('Content-Type: application/json; charset=utf-8');
} else {
    // Regular request - set HTML content type
    header('Content-Type: text/html; charset=utf-8');
}

// Set cache control headers for static resources
$staticExtensions = ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'woff', 'woff2', 'ttf', 'eot'];
$requestUri = $_SERVER['REQUEST_URI'];
$extension = pathinfo($requestUri, PATHINFO_EXTENSION);

if (in_array($extension, $staticExtensions)) {
    // Cache static resources for 1 year with immutable directive
    header('Cache-Control: public, max-age=31536000, immutable');
    // Add version-based cache busting
    if (isset($_GET['v'])) {
        header('ETag: "' . $_GET['v'] . '"');
    }
} else {
    // For dynamic content, use no-cache
    header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
    header('Pragma: no-cache');
    header('Expires: 0');
}

// Set CORS headers if needed
if (isset($_SERVER['HTTP_ORIGIN'])) {
    header('Access-Control-Allow-Origin: ' . $_SERVER['HTTP_ORIGIN']);
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Max-Age: 86400'); // 24 hours
}

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}
?> 