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
import json

# Load TrOCR model and processor
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

def predict_image(image_path, crop_data=None):
    try:
        image = Image.open(image_path).convert("RGB")
        
        if crop_data:
            # Get image dimensions
            width, height = image.size
            
            # Calculate crop coordinates
            crop_x = int(crop_data['x'] * width)
            crop_y = int(crop_data['y'] * height)
            crop_width = int(crop_data['width'] * width)
            crop_height = int(crop_data['height'] * height)
            
            # Perform the crop
            image = image.crop((
                crop_x,
                crop_y,
                crop_x + crop_width,
                crop_y + crop_height
            ))

        # Process the image (either cropped or full)
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
            
            # Get crop data if it exists
            crop_data = request.POST.get('crop_data')
            if crop_data:
                try:
                    crop_data = json.loads(crop_data)
                    # Validate crop data
                    if not all(0 <= crop_data.get(key, 0) <= 1 for key in ['x', 'y', 'width', 'height']):
                        crop_data = None
                except (json.JSONDecodeError, AttributeError):
                    crop_data = None
            
            # Process the image with crop data if available
            result = predict_image(uploaded_image_path, crop_data)

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