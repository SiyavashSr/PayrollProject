from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Payroll
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PayrollExcelUploadForm, UserExcelUploadForm  
import pandas as pd
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('phone_number', 'full_name', 'personal_id', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active','full_name', 'personal_id')
    search_fields = ('phone_number', 'full_name', 'personal_id')
    ordering = ('phone_number', 'personal_id')
    readonly_fields = ('date_joined','last_login',)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        (_('اطلاعات شخصی'), {'fields': ('full_name', 'personal_id')}),
        #(_('دسترسی‌ها'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('تاریخ‌ها'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'full_name', 'personal_id', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active')
            }
        ),
    )

    # مسیر سفارشی برای آپلود
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.admin_site.admin_view(self.upload_excel), name='customuser_upload_excel'),
        ]
        return custom_urls + urls
# -------------------------
# 2. فرم آپلود اکسل کاربران 
# -------------------------
    def upload_excel(self, request):
        if request.method == 'POST':
            form = UserExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                df = pd.read_excel(file)

                for _, row in df.iterrows():
                    phone = str(row['phone_number']).strip()
                    if not phone.startswith('0'):
                        phone = '0' + phone
                    name = row.get('full_name', '')
                    personal_id = str(row.get('personal_id', '')).strip()
                    password = str(row.get('password', '123456'))  # پسورد پیش‌فرض

                    if not CustomUser.objects.filter(phone_number=phone).exists():
                        CustomUser.objects.create_user(
                            phone_number=phone,
                            full_name=name,
                            personal_id=personal_id,
                            password=password
                        )
                messages.success(request, 'کاربران با موفقیت از فایل اکسل ثبت شدند.')
                return redirect('admin:PayrollApp_customuser_changelist')
        else:
            form = UserExcelUploadForm()
        
        return render(request, 'admin/PayrollApp/customuser/upload_excel.html', {'form': form})

# 2. فیش حقوقی
@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'base_salary', 'tax', 'total_received']
    change_list_template = 'admin/PayrollApp/payroll/change_list.html'  # تمپلیت سفارشی

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-excel/', self.admin_site.admin_view(self.upload_excel), name='payroll_upload_excel'),
        ]
        return custom_urls + urls
# -------------------------
# 2. فرم آپلود اکسل فیش حقوقی
# -------------------------
    def upload_excel(self, request):
        if request.method == 'POST':
            form = PayrollExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                df = pd.read_excel(file)

                for _, row in df.iterrows():
                    Payroll.objects.create(
                        user = CustomUser.objects.get(personal_id=str(row['personal_id']).strip()),
                        month=row['month'],
                        base_salary=row['base_salary'],
                        tax=row['tax'],
                        total_received=row['total_received']
                    )
                messages.success(request, 'فایل با موفقیت بارگذاری شد و اطلاعات ثبت شدند.')
                return redirect('admin:PayrollApp_payroll_changelist')
        else:
            form = PayrollExcelUploadForm()

        return render(request, 'admin/PayrollApp/payroll/upload_excel.html', {'form': form})
    
