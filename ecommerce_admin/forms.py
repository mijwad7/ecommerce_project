from django import forms
from ecommerce_app.models import UserProfile, Product, ProductImage, ProductSpec
from django.forms import inlineformset_factory


class UserProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password', 'is_blocked']

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

    # def save(self, commit=True):
    #     product = super().save(commit=commit)

    #     # Save multiple images
    #     if self.files.getlist('images'):
    #         for image in self.files.getlist('images'):
    #             ProductImage.objects.create(product=product, image=image)

    #     return product


ProductSpecFormSet = inlineformset_factory(Product, ProductSpec, fields=('key', 'value'), extra=5, can_delete=True)
