from django import forms
from core.enums import ReportType


class ReportGenerateForm(forms.Form):
    report_type = forms.ChoiceField(
        choices=ReportType.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    period_start = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    period_end = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


class AnnouncementForm(forms.Form):
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    announcement_type = forms.ChoiceField(
        choices=[('info', 'Info'), ('warning', 'Warning'), ('success', 'Success'), ('danger', 'Critical')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    target_roles = forms.MultipleChoiceField(
        choices=[('CUSTOMER', 'Customer'), ('STAFF', 'Staff'), ('ADMIN', 'Admin')],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )


class InventoryUpdateForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    reason = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))