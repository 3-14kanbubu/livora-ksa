from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

class HealthReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symptoms = models.TextField()
    other_symptoms = models.TextField(blank=True, null=True)
    extra_comments = models.TextField(blank=True)
    medical_record = models.FileField(upload_to='medical_records/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    duration= models.PositiveIntegerField(default=0)
    nurse_viewed = models.BooleanField(default=False)
    nurse_comment = models.TextField(blank=True, null=True)
    starred = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Health Report #{self.id}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return f"{self.user.username} - {self.student_id}"
    
from django.db import models
from django.contrib.auth.models import User

class MedicalHistory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Info
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], blank=True)

    # Health History
    allergies = models.CharField(max_length=255, blank=True)
    other_issues = models.TextField(blank=True)

    # Insurance Info
    insurance = models.CharField(max_length=100, blank=True)
    insurance_start = models.DateField(null=True, blank=True)
    insurance_end = models.DateField(null=True, blank=True)

    # Certificate (file upload)
    certificate = models.FileField(upload_to='certificates/', blank=True, null=True)

    # Emergency Contact
    emergency_name = models.CharField(max_length=100, blank=True)
    emergency_relationship = models.CharField(max_length=50, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # Health Care Provider
    clinic_name = models.CharField(max_length=100, blank=True)
    doctor_name = models.CharField(max_length=100, blank=True)
    clinic_phone = models.CharField(max_length=20, blank=True)
    clinic_address = models.TextField(blank=True)
    clinic_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Medical History"

class Surgery(models.Model):
    medical_history = models.ForeignKey(MedicalHistory, on_delete=models.CASCADE, related_name='surgeries')
    name = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Surgery: {self.name} for {self.medical_history.user.username}"

    
    
class NurseStatus(models.Model):
    status = models.CharField(max_length=10, choices=[('open', 'Open'), ('closed', 'Closed')])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.status} at {self.updated_at}"
    

class NurseAnnouncement(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message[:50]
