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
    
    def __str__(self):
        return f"Health Report #{self.id}"
    
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
