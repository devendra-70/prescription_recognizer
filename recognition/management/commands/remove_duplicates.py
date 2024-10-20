from django.core.management.base import BaseCommand
from recognition.models import Medicine  # Replace 'your_app' with the actual app name

class Command(BaseCommand):
    help = 'Remove duplicate entries from Medicine table'

    def handle(self, *args, **kwargs):
        # Get all Medicine records
        medicines = Medicine.objects.values('product_name', 'salt_composition')  # Use 'product_name' instead
        duplicates = {}
        
        # Find duplicates
        for medicine in medicines:
            key = (medicine['product_name'], medicine['salt_composition'])
            if key in duplicates:
                duplicates[key].append(medicine)
            else:
                duplicates[key] = [medicine]

        # Delete duplicates while keeping one instance
        for key, instances in duplicates.items():
            if len(instances) > 1:
                # Keep the first instance and delete the rest
                instances_to_delete = instances[1:]  # All except the first
                for instance in instances_to_delete:
                    Medicine.objects.filter(
                        product_name=instance['product_name'],  # Use 'product_name' here as well
                        salt_composition=instance['salt_composition']
                    ).delete()

        self.stdout.write(self.style.SUCCESS('Duplicates removed successfully.'))
