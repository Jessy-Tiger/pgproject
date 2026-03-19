from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import PickupRequest, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirm Password'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'city', 'state', 'zipcode']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Street Address',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'zipcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Zip Code'
            }),
        }


class PickupRequestForm(forms.ModelForm):
    """Form for creating a pickup request"""
    sender_email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Sender Email'}))

    class Meta:
        model = PickupRequest
        fields = [
            'sender_name', 'sender_email', 'sender_phone', 'sender_address', 'sender_city', 'sender_state', 'sender_zipcode',
            'receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'receiver_state', 'receiver_zipcode',
            'parcel_type', 'parcel_weight', 'parcel_description', 'pickup_date', 'pickup_time', 'additional_notes'
        ]
        widgets = {
            'sender_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sender Name'}),
            'sender_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'sender_address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Street Address', 'rows': 3}),
            'sender_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'sender_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'sender_zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip Code'}),
            'receiver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receiver Name'}),
            'receiver_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'receiver_address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Street Address', 'rows': 3}),
            'receiver_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'receiver_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'receiver_zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip Code'}),
            'parcel_type': forms.Select(attrs={'class': 'form-control'}),
            'parcel_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight (kg)', 'step': '0.01'}),
            'parcel_description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Parcel Description', 'rows': 2}),
            'pickup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pickup_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'additional_notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Additional Notes', 'rows': 2}),
        }


class AdminActionForm(forms.Form):
    """Form for admin to accept/reject requests"""
    ACTION_CHOICES = [
        ('accept', 'Accept Request'),
        ('reject', 'Reject Request'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Reason for rejection (if applicable)',
            'rows': 3
        })
    )
    estimated_cost = forms.DecimalField(
        required=True,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Estimated Cost',
            'step': '0.01'
        })
    )
    assigned_driver = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Assign Driver (Optional - will auto-assign if not selected)'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load drivers from UserProfile
        from .models import UserProfile
        self.fields['assigned_driver'].queryset = User.objects.filter(profile__role='driver', profile__is_active_user=True)

    def clean(self):
        cleaned_data = super().clean()
        # Driver selection is now optional - automatic assignment will be used if none selected
        return cleaned_data


class DriverCreationForm(UserCreationForm):
    """Form for admin to create a driver account"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Phone Number'
    }))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email


class DriverStatusUpdateForm(forms.Form):
    """Form for drivers to update parcel status"""
    STATUS_CHOICES = [
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Update Notes',
            'rows': 3
        })
    )