from django import forms
from accounts.models import UserAddress


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, initial=1)


class CheckoutForm(forms.Form):
    address_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_address_id(self):
        address_id = self.cleaned_data.get('address_id')
        if address_id:
            try:
                address = UserAddress.objects.get(id=address_id, user=self.user)
                return address
            except UserAddress.DoesNotExist:
                raise forms.ValidationError('Invalid address')
        raise forms.ValidationError('Please select an address')


class CouponForm(forms.Form):
    code = forms.CharField(max_length=50)