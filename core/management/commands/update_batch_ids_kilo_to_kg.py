from django.core.management.base import BaseCommand
from core.models import StockAddition


class Command(BaseCommand):
    help = 'Update all batch IDs containing "kilo" to use "kg" instead'

    def handle(self, *args, **options):
        # Find all stock additions with "kilo" in batch_id
        batches_to_update = StockAddition.objects.filter(batch_id__icontains='kilo')
        count = batches_to_update.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No batch IDs found with "kilo" - all good!'))
            return
        
        updated = 0
        for batch in batches_to_update:
            old_batch_id = batch.batch_id
            new_batch_id = batch.batch_id.replace('kilo', 'kg').replace('Kilo', 'kg').replace('KILO', 'kg')
            batch.batch_id = new_batch_id
            batch.save(update_fields=['batch_id'])
            updated += 1
            self.stdout.write(f'  Updated: {old_batch_id} → {new_batch_id}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully updated {updated} batch ID(s) from "kilo" to "kg"')
        )

