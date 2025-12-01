from django.db import migrations


def is_unit_like(text: str) -> bool:
    if not text:
        return False
    t = str(text).strip().lower()
    if t in ("kilo", "kg"):
        return True
    # Numeric sizes like 50, 100, 120, 130, etc.
    import re
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", t))


def fix_products(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    import re

    for p in Product.objects.all():
        name = (p.name or '').strip()
        variant = (p.variant or '').strip()
        unit = (p.quantity_unit or '').strip()

        parts = [m.group(1).strip() for m in re.finditer(r"\(([^)]+)\)", name)]
        base = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()

        # Choose variant candidate from parentheses that is not unit-like
        variant_candidate = ''
        for part in parts:
            if part.strip() == unit.strip():
                continue
            if is_unit_like(part):
                continue
            variant_candidate = part
            break

        # If current variant is missing or incorrectly set to unit-like, override
        if (not variant) or (variant.strip() == unit.strip()) or is_unit_like(variant):
            if variant_candidate:
                p.variant = variant_candidate

        # Always normalize name to base-only (no parentheses)
        if base and base != name:
            p.name = base

        try:
            if p.name != name or (p.variant or '') != variant:
                p.save(update_fields=['name', 'variant'])
        except Exception:
            # Skip problematic rows to avoid blocking migration
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0046_normalize_product_name_variant'),
    ]

    operations = [
        migrations.RunPython(fix_products, reverse_code=migrations.RunPython.noop),
    ]

