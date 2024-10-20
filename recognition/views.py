from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q, Count, F
from django.urls import reverse
from .forms import PrescriptionForm
from .models import PrescriptionImage, Medicine
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch
import re

# Load TrOCR model and processor
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

def predict_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        pixel_values = processor(image, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        prediction = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return prediction.strip()
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None

def upload_prescription(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, request.FILES)
        if form.is_valid():
            prescription_image = form.save()
            uploaded_image_path = prescription_image.image.path
            result = predict_image(uploaded_image_path)

            if result:
                # Clean the result
                cleaned_result = re.sub(r'[^\w\s]', '', result.lower())
                words = cleaned_result.split()
                
                # Create Q objects for word and character matching
                word_q = Q()
                char_q = Q()
                
                for word in words:
                    word_q |= Q(product_name__icontains=word) | Q(salt_composition__icontains=word)
                    for char in word:
                        char_q |= Q(product_name__icontains=char) | Q(salt_composition__icontains=char)
                
                # Query the database
                medicines = Medicine.objects.filter(word_q | char_q).distinct()
                
                # Annotate with word and character match counts
                for word in words:
                    medicines = medicines.annotate(**{
                        f'word_count_{word}': (
                            Count('pk', filter=Q(product_name__icontains=word)) +
                            Count('pk', filter=Q(salt_composition__icontains=word))
                        )
                    })
                
                medicines = medicines.annotate(
                    total_word_count=sum(F(f'word_count_{word}') for word in words),
                    char_count=Count('pk', filter=char_q)
                )
                
                # Order by total word count (primary) and character count (secondary)
                medicines = medicines.order_by('-total_word_count', '-char_count')
                
                # Filter results to ensure at least one word matches or a significant portion of characters match
                min_char_match_percentage = 0.5
                medicines = medicines.filter(
                    Q(total_word_count__gt=0) |
                    Q(char_count__gte=len(cleaned_result) * min_char_match_percentage)
                )
                
                print(f"Recognized text: {result}")
                print(f"Cleaned text: {cleaned_result}")
                print(f"Words: {words}")
                print(f"Number of matches: {medicines.count()}")
                print(f"Matching medicines: {list(medicines.values_list('product_name', 'total_word_count', 'char_count'))}")
            else:
                medicines = []
                result = "Not Recognized"

            return render(request, 'recognition/results.html', {
                'result': result,
                'medicines': medicines
            })
        else:
            return HttpResponse("Invalid form submission.")
    else:
        form = PrescriptionForm()
    return render(request, 'recognition/upload.html', {'form': form})

def medicine_detail(request, id):
    medicine = get_object_or_404(Medicine, id=id)
    return render(request, 'recognition/medicine_detail.html', {'medicine': medicine})