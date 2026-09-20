from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User, PatientProfile
from patients.models import PredictionRecord, ContactMessage

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True, initial='patient')
    
    # Optional clinical values if registering as a patient
    age = forms.IntegerField(required=False, min_value=0, max_value=120)
    gender = forms.ChoiceField(choices=[('', 'Select Gender')] + PatientProfile.GENDER_CHOICES, required=False)
    education_level = forms.ChoiceField(choices=[('', 'Select Education Level')] + PatientProfile.EDUCATION_CHOICES, required=False)
    bmi = forms.FloatField(required=False, min_value=10.0, max_value=60.0)
    smoking = forms.BooleanField(required=False)
    cognitive_score = forms.FloatField(required=False, min_value=0.0, max_value=30.0, label="Cognitive Score (MMSE 0-30)")
    family_history = forms.BooleanField(required=False, label="Family History of Alzheimer's")
    physical_activity = forms.FloatField(required=False, min_value=0.0, label="Physical Activity (hours/week)")

    # Optional staff details
    department = forms.CharField(required=False, max_length=50)
    qualification = forms.CharField(required=False, max_length=100)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            
            # Fill profile fields based on role
            if user.role == 'patient':
                profile = user.patient_profile
                profile.age = self.cleaned_data.get('age')
                profile.gender = self.cleaned_data.get('gender')
                profile.education_level = self.cleaned_data.get('education_level')
                profile.bmi = self.cleaned_data.get('bmi')
                profile.smoking = self.cleaned_data.get('smoking') or False
                profile.cognitive_score = self.cleaned_data.get('cognitive_score')
                profile.family_history = self.cleaned_data.get('family_history') or False
                profile.physical_activity = self.cleaned_data.get('physical_activity')
                profile.save()
            else:
                profile = user.provider_profile
                profile.department = self.cleaned_data.get('department') or 'General Medicine'
                profile.qualification = self.cleaned_data.get('qualification') or 'Credentialed Staff'
                profile.save()
                
        return user


class PatientIntakeForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['age', 'gender', 'education_level', 'bmi', 'smoking', 'cognitive_score', 'family_history', 'physical_activity']
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 68'}),
            'bmi': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'e.g. 24.5'}),
            'cognitive_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '30', 'placeholder': 'MMSE Score (0-30)'}),
            'physical_activity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'hours per week'}),
            'smoking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'family_history': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'cognitive_score': 'Cognitive Score (MMSE 0-30)',
            'family_history': "Family History of Alzheimer's",
            'physical_activity': 'Physical Activity (Hours/Week)',
        }


class CaseReviewForm(forms.ModelForm):
    class Meta:
        model = PredictionRecord
        fields = ['review_comments']
        widgets = {
            'review_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide clinical annotation or remarks...'}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message', 'is_critical']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name', 'required': 'true'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com', 'required': 'true'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'How can we help you?', 'required': 'true'}),
            'is_critical': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'is_critical_checkbox'}),
        }
        labels = {
            'is_critical': 'Flag as Critical Alert (Notifies on-duty clinical team immediately)'
        }
