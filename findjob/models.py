from django.db import models
from django.contrib.auth.models import AbstractUser

# =========================
# Custom User Model
# =========================
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('company', 'Company'),
        ('candidate', 'Candidate'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    # Mobile number added directly to User for easy access
    mobile_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username


# =========================
# Company Profile
# =========================
class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    # Additional fields for company
    contact_number = models.CharField(max_length=15, blank=True, null=True, help_text="Company phone number for WhatsApp/call")

    def __str__(self):
        return self.company_name


# =========================
# Candidate Profile
# =========================
class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    skills = models.TextField(help_text="Comma-separated skills (e.g., Python, Django, React)")
    experience = models.IntegerField(help_text="Years of experience")
    location = models.CharField(max_length=255, help_text="Current city/location")
    # New fields as requested
    qualification = models.CharField(max_length=255, blank=True, null=True, help_text="Highest qualification (e.g., B.Tech, MCA)")
    # Mobile number is already in User model, but you can keep a separate one if needed
    # We'll use User.mobile_number as primary

    def __str__(self):
        return self.user.username


# =========================
# Job Post
# =========================
class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
    )
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    category = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Customer Support, Python Developer")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ✅ New field: is_active
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide job from dashboard")

    def __str__(self):
        return self.title


# =========================
# Job Application
# =========================
class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.candidate.user.username} -> {self.job.title}"