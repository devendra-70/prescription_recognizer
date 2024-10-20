from django.contrib import admin
from .models import PrescriptionImage, Medicine

class MedicineAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'salt_composition',  'product_price', 'product_manufactured')
    search_fields = ('product_name', 'salt_composition')

admin.site.register(PrescriptionImage)
admin.site.register(Medicine, MedicineAdmin)
