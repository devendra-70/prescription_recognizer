from django import forms
from .models import PrescriptionImage

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = PrescriptionImage
        fields = ['image']
