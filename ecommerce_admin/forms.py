from django import forms
from ecommerce_app.models import UserProfile, Product, ProductImage, ProductSpec
from django.forms import inlineformset_factory


class UserProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password', 'is_blocked', 'is_active', "is_superuser"]
        widgets = {
            'username': forms.TextInput(attrs={'help_text': ''}),
            'email': forms.EmailInput(attrs={'help_text': ''}),
            'is_blocked': forms.CheckboxInput(attrs={'help_text': ''}),
            'is_active': forms.CheckboxInput(attrs={'help_text': ''}),
            'is_superuser': forms.CheckboxInput(attrs={'help_text': ''}),
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'stock', 'price', 'is_on_sale', 'is_featured', 'sale_price', 'category', 'coupons']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    # def save(self, commit=True):
    #     product = super().save(commit=commit)

    #     # Save multiple images
    #     if self.files.getlist('images'):
    #         for image in self.files.getlist('images'):
    #             ProductImage.objects.create(product=product, image=image)

    #     return product


ProductSpecFormSet = inlineformset_factory(Product, ProductSpec, fields=('key', 'value'), extra=5, can_delete=True)
