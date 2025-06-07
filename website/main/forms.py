from django import forms
from .models import HealthReport
from django.contrib.auth.forms import AuthenticationForm


class HealthReportForm(forms.ModelForm):
    symptoms = forms.MultipleChoiceField(
        choices=[
            ('fever', 'Fever'),
            ('cough', 'Cough'),
            ('sore throat', 'Sore throat'),
            ('runny/stuffy nose', 'Runny/Stuffy Nose'),
            ('fatigue', 'Fatigue'),
            ('muscle ache', 'Muscle Ache'),
            ('numbness', 'Numbness'),
            ('sleepiness', 'Sleepiness'),
            ('headache', 'Headache'),
            ('nausea', 'Nausea'),
            ('sweating', 'Sweating'),
        ],
        widget=forms.CheckboxSelectMultiple
    )
    duration=forms.IntegerField()

    other_symptoms = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea
    )
    
    extra_comments = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea
    )

    medical_record = forms.FileField(
        required=False
    )

    class Meta:
        model = HealthReport
        fields = ['symptoms', 'other_symptoms', 'extra_comments', 'medical_record','duration']
        
        
class StyledLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter ID'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter Password'
    }))