# Generated by Django 5.1.2 on 2024-10-15 14:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recognition', '0002_medicine'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='medicine',
            name='drug_interactions',
        ),
    ]