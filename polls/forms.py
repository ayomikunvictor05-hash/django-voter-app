# polls/forms.py

from django import forms
from .models import Poll, Choice


# class PollForm(forms.ModelForm):
#     end_time = forms.DateTimeField(
#         widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#         help_text="Select when voting closes."
#     )

#     class Meta:
#         model = Poll
#         fields = [
#             'title',
#             'description',
#             'end_time',
#             'results_visibility',
#             'passcode',
#             'allowed_domains',
#             'allowed_voter_group',
#         ]
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Department Executive Election 2026'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'results_visibility': forms.Select(attrs={'class': 'form-select'}),
#             'passcode': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Optional access passcode'}),
#             'allowed_domains': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., company.com, university.edu'}),
#             'allowed_voter_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Engineering'}),
#         }


# polls/forms.py

from django import forms
from .models import Poll

COMMON_DOMAINS = [
    ('ALL', '🌐 All / Open to All Domains'),
    ('gmail.com', 'Gmail (gmail.com)'),
    ('yahoo.com', 'Yahoo (yahoo.com)'),
    ('outlook.com', 'Outlook (outlook.com)'),
    ('hotmail.com', 'Hotmail (hotmail.com)'),
    ('icloud.com', 'iCloud (icloud.com)'),
]

class PollForm(forms.ModelForm):
    domain_checkboxes = forms.MultipleChoiceField(
        choices=COMMON_DOMAINS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        initial=['ALL'],
    )
    
    custom_domains = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Add custom domains e.g. mycompany.com, university.edu'
        })
    )

    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text="When voting opens."
    )
    
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text="When voting closes."
    )

    class Meta:
        model = Poll
        fields = [
            'title',
            'description',
            'start_time',
            'end_time',
            'results_visibility',
            'passcode',
            'allowed_voter_group',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Department Executive Election'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'results_visibility': forms.Select(attrs={'class': 'form-select'}),
            'passcode': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Optional access passcode'}),
            'allowed_voter_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Engineering'}),
        }

class CodeSearchForm(forms.Form):
    code = forms.CharField(
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-uppercase text-center fw-bold',
            'placeholder': 'ENTER VOTING CODE (e.g., A1B2C3D4)',
            'autocomplete': 'off'
        })
    )


class PasscodeVerifyForm(forms.Form):
    passcode = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Poll Passcode'})
    )
    
    
    
