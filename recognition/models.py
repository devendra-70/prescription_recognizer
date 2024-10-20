from django.db import models

class PrescriptionImage(models.Model):
    image = models.ImageField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Medicine(models.Model):
    sub_category = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    salt_composition = models.CharField(max_length=200)
    product_price = models.CharField(max_length=50)
    product_manufactured = models.CharField(max_length=100)
    medicine_desc = models.TextField()
    side_effects = models.TextField()

    def __str__(self):
        return self.product_name
