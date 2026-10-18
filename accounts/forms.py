from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import UserProfile
import re

User = get_user_model()


class CustomerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'Last Name'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'Choose Username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'name@example.com'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': '10-digit mobile number'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control bg-dark text-light border-secondary'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'Minimum 8 characters'})
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'Re-enter password'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control bg-dark text-light border-secondary'})
    )
    agree_terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to the Terms of Service & Privacy Policy.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'date_of_birth', 'profile_picture']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please pick another one.")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise ValidationError("Username can only contain alphanumeric characters, underscores, and dots.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        if len(clean_phone) < 10 or not clean_phone.isdigit():
            raise ValidationError("Please provide a valid 10-digit mobile phone number.")
        return clean_phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one number.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please re-enter.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_CUSTOMER
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    login_id = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark text-light border-secondary py-2',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-dark text-light border-secondary py-2',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control bg-dark text-light border-secondary'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control bg-dark text-light border-secondary'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control bg-dark text-light border-secondary'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'profile_picture']


class PreferencesForm(forms.ModelForm):
    preferred_language = forms.ChoiceField(
        choices=[('English', 'English'), ('Hindi', 'Hindi'), ('Tamil', 'Tamil'), ('Telugu', 'Telugu'), ('Spanish', 'Spanish')],
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-light border-secondary'})
    )
    favorite_genre = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'e.g. Action, Sci-Fi'})
    )

    class Meta:
        model = UserProfile
        fields = ['preferred_language', 'favorite_genre']


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'Enter registered email address'})
    )


class SetNewPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'New password (min 8 chars)'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control bg-dark text-light border-secondary', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        if p1 and len(p1) < 8:
            self.add_error('new_password', "Password must be at least 8 characters.")
        return cleaned_data
