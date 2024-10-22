from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Address


class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password1']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def __init__(self, *args, **kwargs):
        super(UserSignUpForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'line_1', 'line_2', 'city', 'state', 'post_code', 'is_primary', 'address_type'
        ]
        widgets = {
            'line_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'line_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'post_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Post Code'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address_type': forms.Select(attrs={'class': 'form-select'}),
        }