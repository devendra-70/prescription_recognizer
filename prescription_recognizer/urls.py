from django.contrib import admin
from django.urls import path
from recognition.views import upload_prescription, medicine_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', upload_prescription, name='home'),  # Set the root URL to the upload_prescription view
    path('upload/', upload_prescription, name='upload_prescription'),
    path('medicine/<int:id>/', medicine_detail, name='medicine_detail'),
]
