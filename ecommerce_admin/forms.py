from django import forms
from ecommerce_app.models import UserProfile, Product, ProductImage, ProductSpec, ProductVariant, Coupon, CategoryOffer
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
        fields = ['name', 'description', 'stock', 'price', 'is_on_sale', 'is_featured', 'sale_price', 'category', 'tags', 'brand', 'coupons', 'max_per_user']

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


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'variant_type', 'value', 'stock', 'price', 'is_on_sale', 'sale_price']
    
    def __init__(self, *args, **kwargs):
        super(ProductVariantForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        is_on_sale = cleaned_data.get("is_on_sale")
        sale_price = cleaned_data.get("sale_price")

        # Ensure sale price is present if the product is marked as on sale
        if is_on_sale and not sale_price:
            self.add_error('sale_price', 'Sale price is required when marking as on sale.')

        # Ensure sale price is less than regular price if it exists
        if sale_price and sale_price >= cleaned_data.get("price"):
            self.add_error('sale_price', 'Sale price must be less than the regular price.')
        
        return cleaned_data


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_percent', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super(CouponForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})


class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = ['category', 'discount_percent', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super(CategoryOfferForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
