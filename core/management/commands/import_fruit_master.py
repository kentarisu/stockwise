from django.core.management.base import BaseCommand
from core.models import Product, FruitMaster
import re

class Command(BaseCommand):
    help = "Populate FruitMaster table from existing Product records"

    def handle(self, *args, **options):
        created = 0
        for p in Product.objects.all():
            name = p.name.strip().lstrip("'").rstrip("'")
            variant = ''
            # extract variant inside first parentheses in name
            m = re.search(r"\(([^)]+)\)", name)
            if m:
                variant = m.group(1).strip()
                name = re.sub(r"\s*\([^)]*\)", "", name).strip()
            size = p.size.strip() if p.size else ''
            obj, is_created = FruitMaster.objects.get_or_create(name=name, variant=variant, size=size)
            if is_created:
                created += 1

        # built-in extra fruits not in Product table
        extras = [
            ("Banana", "Cavendish", "Large"),
            ("Banana", "Lakatan", "Medium"),
            ("Mango", "Carabao", "16-18"),
            ("Mango", "Tommy Atkins", "Large"),
            ("Pineapple", "Queen", "Medium"),
            ("Strawberry", "Fresh", "Small"),
            ("Blueberry", "Fresh", "Small"),
            ("Watermelon", "Seedless", "5kg"),
        ]
        for name, variant, size in extras:
            _, is_created = FruitMaster.objects.get_or_create(name=name, variant=variant, size=size)
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {created} fruit master records.")) 