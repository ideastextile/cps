# forms.py
from django import forms
from .models import Parcel, Driver, Job

class ParcelUpdateForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = ['status', 'current_driver']


class JobUpdateForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['driver', 'job_type', 'status']  # ✅ Corrected field name
        widgets = {
            'driver': forms.Select(attrs={'class': 'bg-gray-800 text-white rounded px-2 py-1'}),
            'job_type': forms.Select(attrs={'class': 'bg-gray-800 text-white rounded px-2 py-1'}),  # ✅ Corrected
            'status': forms.Select(attrs={'class': 'bg-gray-800 text-white rounded px-2 py-1'}),
        }




class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = [
            'pickup_address',
            'delivery_address',
            'recipient_name',
            'recipient_phone',
            'description',
            'weight',
            'dimensions',
            'expected_delivery_date',
            'delivery_instructions',
        ]