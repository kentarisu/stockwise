"""
Unified SMS Formatter for StockWise
Ensures all SMS messages follow the exact format specified by the user.
Supports multipart messages with 1/2, 2/2 prefixes when messages are too long.
"""
from decimal import Decimal
from datetime import datetime


def format_daily_sales_summary(date, total_sales, total_revenue, total_boxes, top_products, kilos_sold):
    """
    Format Daily Sales Summary SMS message.
    
    Format:
    Daily Sales Report
    
    Date: December 08, 2025
    == OVERALL SUMMARY ==
    
    Total Revenue: PHP 0.00
    Total Boxes Sold: 0
    Total kg Sold: 0
    Total Transactions: 0
    
    == TOP PRODUCTS TODAY ==
    1. Apple (Gala) (50)
    Sold: 40 boxes
    Revenue: PHP 69,778.55
    Remaining: 36 boxes
    ...
    """
    date_str = date.strftime('%B %d, %Y')
    message = "Daily Sales Report\n\n"
    message += f"Date: {date_str}\n\n"
    message += "== OVERALL SUMMARY ==\n\n"
    message += f"Total Revenue: PHP {float(total_revenue):,.2f}\n"
    message += f"Total Boxes Sold: {int(total_boxes)}\n"
    message += f"Total kg Sold: {int(kilos_sold or 0)}\n"
    message += f"Total Transactions: {int(total_sales)}\n\n"
    
    if top_products:
        message += "== TOP PRODUCTS TODAY ==\n\n"
        for i, product in enumerate(top_products, 1):
            name = product.get('product__name') or product.get('name') or ''
            variant = (product.get('product__variant') or product.get('variant') or '').strip()
            unit = (product.get('product__quantity_unit') or product.get('quantity_unit') or '').strip()
            remaining = int(product.get('product__stock') or product.get('stock') or 0)
            sold_qty = int(product.get('quantity') or 0)
            revenue = float(product.get('revenue') or 0)
            
            unit_label = 'kg' if (unit or '').strip().lower() == 'kg' else 'boxes'
            rem_label = 'kg' if (unit or '').strip().lower() == 'kg' else ('box' if remaining == 1 else 'boxes')
            
            # Format product label: Name (Variant) (Unit)
            label = name
            if variant:
                label += f" ({variant})"
            if unit:
                label += f" ({unit})"
            
            message += f"{i}. {label}\n"
            message += f"Sold: {sold_qty} {unit_label}\n"
            message += f"Revenue: PHP {revenue:,.2f}\n"
            message += f"Remaining: {remaining} {rem_label}\n\n"
    
    return message


def format_stock_alert(out_of_stock_products, low_stock_products):
    """
    Format Stock Alert SMS message.
    
    Format:
    Stock Alert
    
    CRITICAL - OUT OF STOCK:
    1. Apple (Red Delicious) (200)
    2. Apple (Granny Smith) (50)
    ...
    
    WARNING - LOW STOCK:
    1. Apple (Fuji) (130): 2 boxes left
    2. Apple (Gala) (kg): 5 kg left
    ...
    """
    message = "Stock Alert\n\n"
    
    def _label(name, variant, quantity_unit):
        """Create product label: Name (Variant) (Unit)"""
        n = (name or "").strip()
        v = (variant or "").strip()
        u = (quantity_unit or "").strip()
        label = n
        if v:
            label += f" ({v})"
        if u:
            label += f" ({u})"
        return label
    
    if out_of_stock_products:
        message += "CRITICAL - OUT OF STOCK:\n\n"
        # Handle both queryset and list
        products_list = list(out_of_stock_products) if hasattr(out_of_stock_products, '__iter__') and not isinstance(out_of_stock_products, str) else out_of_stock_products
        for i, product in enumerate(products_list, 1):
            if hasattr(product, 'name'):
                name = product.name
                variant = getattr(product, 'variant', None)
                unit = getattr(product, 'quantity_unit', None)
            elif isinstance(product, dict):
                name = product.get('name') or product.get('product__name', '')
                variant = product.get('variant') or product.get('product__variant')
                unit = product.get('quantity_unit') or product.get('product__quantity_unit')
            else:
                continue
            label = _label(name, variant, unit)
            message += f"{i}. {label}\n"
        message += "\n"
    
    if low_stock_products:
        message += "WARNING - LOW STOCK:\n\n"
        # Handle both queryset and list
        products_list = list(low_stock_products) if hasattr(low_stock_products, '__iter__') and not isinstance(low_stock_products, str) else low_stock_products
        for i, product in enumerate(products_list, 1):
            if hasattr(product, 'name'):
                name = product.name
                variant = getattr(product, 'variant', None)
                unit = getattr(product, 'quantity_unit', None)
                stock = int(getattr(product, 'stock', 0))
            elif isinstance(product, dict):
                name = product.get('name') or product.get('product__name', '')
                variant = product.get('variant') or product.get('product__variant')
                unit = product.get('quantity_unit') or product.get('product__quantity_unit')
                stock = int(product.get('stock') or product.get('product__stock', 0))
            else:
                continue
            
            unit_label = 'kg' if (unit or '').strip().lower() == 'kg' else 'boxes'
            label = _label(name, variant, unit)
            message += f"{i}. {label}: {stock} {unit_label} left\n"
        message += "\n"
    
    if not out_of_stock_products and not low_stock_products:
        message += "All products have sufficient stock.\n\n"
    
    return message


def format_pricing_recommendation(recommendations):
    """
    Format Pricing Recommendation SMS message.
    
    Format:
    Pricing Recommendation
    
    1. Melon (Small) (kg)
    PHP 60.00 -> 57.00 (-5%)
    Reason: Low sales activity in the past 3 days
    
    OR
    
    Pricing Recommendation
    
    No Pricing Recommendation Today.
    """
    message = "Pricing Recommendation\n\n"
    
    if not recommendations or (hasattr(recommendations, '__len__') and len(recommendations) == 0):
        message += "No Pricing Recommendation Today.\n"
        return message
    
    # Handle different input types
    if hasattr(recommendations, 'iterrows'):  # pandas DataFrame
        recs_list = [row for _, row in recommendations.iterrows()]
    elif hasattr(recommendations, '__iter__') and not isinstance(recommendations, str):
        recs_list = list(recommendations)
    else:
        recs_list = [recommendations]
    
    if not recs_list:
        message += "No Pricing Recommendation Today.\n"
        return message
    
    for i, rec in enumerate(recs_list, 1):
        # Extract data from different formats
        if hasattr(rec, 'name'):
            name = rec.name
            variant = getattr(rec, 'variant', None)
            unit = getattr(rec, 'quantity_unit', None) or getattr(rec, 'unit', None)
            current_price = float(getattr(rec, 'current_price', 0) or getattr(rec, 'price', 0))
            suggested_price = float(getattr(rec, 'suggested_price', 0))
            change_pct = float(getattr(rec, 'change_pct', 0))
            reason = getattr(rec, 'reason', '') or ''
        elif isinstance(rec, dict):
            name = rec.get('name') or ''
            variant = rec.get('variant')
            unit = rec.get('quantity_unit') or rec.get('unit')
            current_price = float(rec.get('current_price', 0) or rec.get('price', 0))
            suggested_price = float(rec.get('suggested_price', 0))
            change_pct = float(rec.get('change_pct', 0))
            reason = rec.get('reason', '') or ''
        else:
            # Try to get product from related object
            product = getattr(rec, 'product', None)
            if product:
                name = getattr(product, 'name', '')
                variant = getattr(product, 'variant', None)
                unit = getattr(product, 'quantity_unit', None)
                current_price = float(getattr(product, 'price', 0))
            else:
                continue
            suggested_price = float(getattr(rec, 'suggested_price', 0))
            change_pct = float(getattr(rec, 'change_pct', 0))
            reason = getattr(rec, 'reason', '') or ''
        
        # Build product label
        label = name
        if variant:
            label += f" ({variant})"
        if unit:
            label += f" ({unit})"
        
        # Calculate percentage change
        if current_price > 0:
            pct = ((suggested_price / current_price) - 1.0) * 100.0
        else:
            pct = change_pct
        
        # Enforce maximum 10% change - skip this recommendation if it exceeds
        if abs(pct) > 10.0:
            continue  # Skip recommendations that exceed 10% change
        
        sign = '-' if pct < 0 else ('+' if pct > 0 else '')
        pct_abs = abs(pct)
        
        # Clean reason
        reason_clean = reason.split('[Data:')[0].strip() if '[Data:' in reason else reason.strip()
        if not reason_clean:
            reason_clean = 'Price optimization'
        
        message += f"{i}. {label}\n"
        message += f"PHP {current_price:.2f} -> {suggested_price:.2f} ({sign}{pct_abs:.0f}%)\n"
        if reason_clean:
            message += f"Reason: {reason_clean}\n\n"
        else:
            message += "\n"
    
    return message


def split_long_message(message, max_length=160):
    """
    Split a long message into multiple parts with 1/2, 2/2 prefixes.
    Only splits if message exceeds max_length.
    
    Args:
        message: The message to split
        max_length: Maximum length per segment (default 160 for single SMS)
    
    Returns:
        List of message parts with prefixes if multipart, or single message if short enough
    """
    if len(message) <= max_length:
        return [message]
    
    # Reserve space for prefix (e.g., "1/2 " = 5 chars, "10/10 " = 7 chars)
    # We'll estimate 8 chars for prefix to be safe
    prefix_reserve = 8
    segment_length = max_length - prefix_reserve
    
    # Split by lines first to preserve structure
    lines = message.split('\n')
    segments = []
    current_segment = ''
    
    for line in lines:
        # If adding this line would exceed segment length, start new segment
        line_with_newline = line + '\n'
        if len(current_segment) + len(line_with_newline) > segment_length:
            if current_segment:
                segments.append(current_segment.rstrip())
            current_segment = line_with_newline
        else:
            current_segment += line_with_newline
    
    # Add final segment
    if current_segment:
        segments.append(current_segment.rstrip())
    
    # If we still have segments that are too long, split them by character
    final_segments = []
    for seg in segments:
        if len(seg) <= segment_length:
            final_segments.append(seg)
        else:
            # Split by character
            start = 0
            while start < len(seg):
                end = min(start + segment_length, len(seg))
                final_segments.append(seg[start:end])
                start = end
    
    # Add prefixes
    total_parts = len(final_segments)
    if total_parts == 1:
        return final_segments
    
    prefixed_segments = []
    for i, segment in enumerate(final_segments, 1):
        prefixed_segments.append(f"{i}/{total_parts} {segment}")
    
    return prefixed_segments

