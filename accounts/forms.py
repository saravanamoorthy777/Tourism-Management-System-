from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Profile

class CustomerRegistrationForm(forms.ModelForm):
    """
    Form for registering new customers with full name, username, email, and password confirmation.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'id': 'reg_first_name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'id': 'reg_last_name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'id': 'reg_email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a secure password',
            'id': 'reg_password'
        }),
        min_length=6,
        help_text="Password must be at least 6 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'reg_confirm_password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose unique username',
                'id': 'reg_username'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please re-enter.")
        return cleaned_data


class CustomerLoginForm(forms.Form):
    """
    Dual-mode login form allowing authentication by either Username or Email address.
    """
    username_or_email = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'id': 'login_identifier'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'login_password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'remember_me'})
    )

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if identifier and password:
            # Check if identifier is an email
            user_obj = None
            if '@' in identifier:
                user_match = User.objects.filter(email__iexact=identifier).first()
                if user_match:
                    user_obj = authenticate(username=user_match.username, password=password)
            else:
                user_obj = authenticate(username=identifier, password=password)

            if not user_obj:
                raise forms.ValidationError("Invalid credentials. Please verify your username/email and password.")
            
            if not user_obj.is_active:
                raise forms.ValidationError("This account has been disabled. Please contact support.")

            self.user_cache = user_obj
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating standard User attributes (name and email).
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'profile_first_name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'profile_last_name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'profile_email'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already registered to another user.")
        return email


class ProfileDetailsUpdateForm(forms.ModelForm):
    """
    Form for updating extended Profile attributes.
    """
    class Meta:
        model = Profile
        fields = ('phone_number', 'city', 'state', 'pincode', 'address', 'profile_image')
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 9876543210', 'id': 'profile_phone'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'id': 'profile_city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'id': 'profile_state'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN / Postal Code', 'id': 'profile_pincode'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full street address', 'id': 'profile_address'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control', 'id': 'profile_image_input'}),
        }
