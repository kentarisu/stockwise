from django.db import migrations


def normalize_names(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    import re
    for p in Product.objects.all():
        name = (p.name or '').strip()
        variant = (p.variant or '').strip()
        m = re.match(r'^(?P<base>.+?)\s*\((?P<var>[^)]+)\)\s*$', name)
        try:
            if not variant and m:
                base = m.group('base').strip()
                var = m.group('var').strip()
                p.name = base
                p.variant = var
                p.save(update_fields=['name', 'variant'])
            elif variant and re.search(r'\(\s*' + re.escape(variant) + r'\s*\)\s*$', name):
                base = re.sub(r'\(\s*' + re.escape(variant) + r'\s*\)\s*$', '', name).strip()
                if base != name:
                    p.name = base
                    p.save(update_fields=['name'])
        except Exception:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0045_smsnotificationsettings_pricing_frequency_days_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_names, reverse_code=migrations.RunPython.noop),
    ]

