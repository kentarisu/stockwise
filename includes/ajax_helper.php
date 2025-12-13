<?php
function sendJsonResponse($data, $statusCode = 200) {
    // Prevent multiple header sends
    if (headers_sent()) {
        error_log('Headers already sent when trying to send JSON response');
        return;
    }

    // Set proper JSON headers
    header('Content-Type: application/json; charset=utf-8');
    http_response_code($statusCode);
    
    // Add cache control for AJAX responses
    header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
    header('Pragma: no-cache');
    header('Expires: 0');
    
    // Add security headers
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    
    // Add CORS headers if needed
    if (isset($_SERVER['HTTP_ORIGIN'])) {
        header('Access-Control-Allow-Origin: ' . $_SERVER['HTTP_ORIGIN']);
        header('Access-Control-Allow-Credentials: true');
    }
    
    // Output JSON response with proper encoding
    $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR);
    if ($json === false) {
        error_log('JSON encoding error: ' . json_last_error_msg());
        http_response_code(500);
        $json = json_encode(['error' => 'Internal server error'], JSON_UNESCAPED_UNICODE);
    }
    echo $json;
    exit;
}

// Helper function to check if request is AJAX
function isAjaxRequest() {
    return isset($_SERVER['HTTP_X_REQUESTED_WITH']) && 
           strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';
}

// Helper function to get file version for cache busting
function getFileVersion($filePath) {
    if (file_exists($filePath)) {
        return filemtime($filePath);
    }
    return time();
}

// Helper function to generate cache-busted URL
function getCacheBustedUrl($url) {
    $version = getFileVersion($_SERVER['DOCUMENT_ROOT'] . parse_url($url, PHP_URL_PATH));
    $separator = (strpos($url, '?') === false) ? '?' : '&';
    return $url . $separator . 'v=' . $version;
}
?> 