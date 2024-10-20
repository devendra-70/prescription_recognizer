import csv
from django.core.management.base import BaseCommand
from recognition.models import Medicine

class Command(BaseCommand):
    help = 'Load medicine data from CSV file'

    def handle(self, *args, **kwargs):
        # Change the path to your actual CSV file
        csv_file_path = 'D:\Dev_Web_With_Donut_V2\prescription_recognizer\medicine_data_cleaned.csv'
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Medicine.objects.create(
                    sub_category=row['sub_category'],
                    product_name=row['product_name'],
                    salt_composition=row['salt_composition'],
                    product_price=row['product_price'],
                    product_manufactured=row['product_manufactured'],
                    medicine_desc=row['medicine_desc'],
                    side_effects=row['side_effects'],
                )
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
