from django import forms
from .models import ServiceBooking, StaffTask, StaffShift
from core.enums import ServiceStatus


class ServiceBookingForm(forms.ModelForm):
    preferred_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    preferred_time_slot = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Morning/Afternoon/Evening'}))
    
    class Meta:
        model = ServiceBooking
        fields = [
            'device_type', 'device_model', 'issue_description',
            'address_line1', 'address_line2', 'city', 'state', 'pincode', 'landmark', 'map_link',
            'preferred_date', 'preferred_time_slot', 'notes'
        ]
        widgets = {
            'device_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Laptop, Printer, CCTV, etc.'}),
            'device_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model number if known'}),
            'issue_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nearby landmark'}),
            'map_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Google Maps link'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any additional information'}),
        }
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        from core.utils import validate_pincode
        if not validate_pincode(pincode):
            raise forms.ValidationError('Enter a valid 6-digit PIN code')
        return pincode


class StaffTaskForm(forms.ModelForm):
    class Meta:
        model = StaffTask
        fields = ['priority', 'notes']
        widgets = {
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class StaffShiftForm(forms.ModelForm):
    shift_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    
    class Meta:
        model = StaffShift
        fields = ['shift_date', 'start_time', 'end_time', 'branch', 'notes']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ServiceStatusForm(forms.Form):
    status = forms.ChoiceField(choices=ServiceStatus.choices, widget=forms.Select(attrs={'class': 'form-control'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)