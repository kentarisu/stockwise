# QR Code Scanning for Adding Stock

## Overview
The StockWise system now supports QR code scanning directly within the web interface for adding stock. This eliminates the need for external QR scanner apps when using the system on mobile devices.

## Features Added

### 1. QR Scanner Button
- Added a "Scan QR Code" button to the Add Stock page header
- Green button with QR code scan icon for easy identification

### 2. QR Scanner Modal
- Full-screen camera interface for scanning QR codes
- Automatic camera selection (tries back camera first, then front camera)
- Real-time QR code detection and processing
- User-friendly error handling and instructions

### 3. Automatic Form Population
- Scanned QR codes automatically populate the stock addition form
- Supports both single product and multi-product QR codes
- Preserves quantity and supplier information from QR codes
- Allows modification of populated data before submission

### 4. Backend API Enhancement
- New `/api/stock/qr/decode/` endpoint for processing QR tokens
- Secure token validation and product information extraction
- JSON response format for seamless frontend integration

## How to Use

### For Users:
1. Navigate to the Add Stock page
2. Click the "Scan QR Code" button in the header
3. Allow camera permissions when prompted
4. Point the camera at a valid stock QR code
5. The form will automatically populate with the scanned information
6. Review and modify quantities/suppliers as needed
7. Click "Add Stock" to submit

### For Developers:
The system supports two types of QR codes:

#### Type 1: Direct Product QR Codes
- URL format: `/qr/generate/{product_id}/?date={date}`
- Automatically extracts product ID and populates form

#### Type 2: Token-based QR Codes
- URL format: `/api/stock/qr/apply/?t={token}`
- Contains multiple products with quantities and suppliers
- Uses signed tokens for security

## Technical Implementation

### Frontend (JavaScript)
- Uses HTML5-QRCode library for camera access
- Handles multiple camera configurations
- Processes QR data and populates form fields
- Provides user feedback and error handling

### Backend (Django)
- `stock_qr_decode` view function for token processing
- Secure token validation using Django's signing framework
- Product information extraction and JSON response
- Error handling for invalid/expired tokens

### Browser Compatibility
- Works on modern browsers with camera support
- Optimized for mobile devices
- Graceful degradation when camera access is unavailable

## Security Features
- Signed tokens with expiration (5 minutes)
- Salt-based token signing for additional security
- Input validation and sanitization
- Error handling without exposing sensitive information

## Testing
The system has been tested with:
- Single product QR codes
- Multi-product QR codes
- Invalid/expired tokens
- Camera permission scenarios
- Mobile device compatibility

## Future Enhancements
Potential improvements could include:
- Batch QR code generation for multiple products
- QR code history and tracking
- Offline QR code caching
- Enhanced error reporting and user guidance
