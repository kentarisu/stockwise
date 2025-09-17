import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from core.models import FruitMaster

class Command(BaseCommand):
    help = "Load (or reload) the FruitMaster table from a CSV file. Clears the table first.\n\nCSV format: name,variant,size  (header row optional)."

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to CSV file.')

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path']).expanduser()
        if not csv_path.exists():
            raise CommandError(f"File not found: {csv_path}")

        # purge existing
        FruitMaster.objects.all().delete()
        self.stdout.write('Existing FruitMaster rows deleted.')

        created = 0
        with csv_path.open(newline='', encoding='utf-8') as fh:
            reader = csv.reader(fh)
            # detect header if first row contains non-numeric size strings
            first = next(reader)
            has_header = any(h.lower() in ('name', 'variant', 'size') for h in first)
            if not has_header:
                # rewind
                fh.seek(0)
                reader = csv.reader(fh)
            else:
                # start after header row already consumed
                pass

            for row in reader:
                if len(row) < 1:
                    continue
                name    = row[0].strip()
                variant = row[1].strip() if len(row) >= 2 else ''
                size    = row[2].strip() if len(row) >= 3 else ''
                if not name:
                    continue
                _, is_created = FruitMaster.objects.get_or_create(name=name, variant=variant, size=size)
                if is_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {created} fruit master rows from {csv_path}")) 