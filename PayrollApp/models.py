from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django_jalali.db import models as jmodels
import random
from django.utils import timezone
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('شماره موبایل الزامی است')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=11, unique=True)
    full_name = models.CharField(max_length=100)
    personal_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True, blank=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'personal_id']

    objects = CustomUserManager()

    def __str__(self):
        return self.full_name or self.phone_number
# -------------------------
# 2. فیش حقوقی
# -------------------------
class Payroll(models.Model):
    user = models.ForeignKey(
        'CustomUser', 
        to_field='personal_id',  # توجه کن نام دقیق فیلد رو بنویس
        on_delete=models.CASCADE, 
        related_name='payrolls'
    )
    month = models.CharField(max_length=7)  # مثلا "1403/04"
    base_salary = models.PositiveIntegerField()
    bonus = models.PositiveIntegerField(default=0)
    tax = models.PositiveIntegerField(default=0)
    insurance = models.PositiveIntegerField(default=0)
    total_received = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.month}"
    
class ExcelUpload(models.Model):
    file = models.FileField(upload_to='excels/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Excel uploaded at {self.uploaded_at}"
    
class OTPRequest(models.Model):
    phone_number = models.CharField(max_length=11)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        return self.created_at >= timezone.now() - timedelta(minutes=2)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone_number} - {self.code}"