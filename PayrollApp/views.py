from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views import View
from .forms import (
    LoginWithPasswordForm, LoginWithOTPForm, ChangePasswordForm,
    PayrollExcelUploadForm, MonthSelectForm
)
from .models import Payroll
from django.contrib.auth.models import User
import openpyxl
from django.contrib.auth.forms import PasswordChangeForm
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import OTPRequest
from django.utils import timezone
import random
from .models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken


# 1. ورود کاربر
def user_login(request):
    if request.method == 'POST':
        form = LoginWithPasswordForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['phone_number'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "نام کاربری یا رمز اشتباه است.")
        else:
                messages.error(request, "نام کاربری یا رمز اشتباه است.")
    else:
        form = LoginWithPasswordForm()
    return render(request, 'login_password.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

# 2. داشبورد کاربر
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')


# 3. انتخاب ماه برای مشاهده فیش‌ها
@login_required
def select_month_view(request):
    form = MonthSelectForm(user=request.user, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        selected_month = form.cleaned_data['month']
        return redirect('view_payroll', month=selected_month)

    return render(request, 'select_payroll_month.html', {'form': form})


# 4. مشاهده فیش حقوقی برای یک ماه خاص
@login_required
def view_payroll_view(request, month):
    payrolls = Payroll.objects.filter(user=request.user, month=month)
    return render(request, 'view_payroll.html', {'payrolls': payrolls, 'month': month})


# 5. تغییر رمز عبور
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # برای logout نشدن بعد از تغییر رمز
            messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
            return redirect('dashboard')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})


# 6. آپلود فایل اکسل فیش حقوقی توسط ادمین
def upload_payroll_excel_view(request):
    if request.method == 'POST':
        form = PayrollExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active

            success_count = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    national_code = str(row[0])
                    user = User.objects.get(profile__national_code=national_code)

                    Payroll.objects.create(
                        user=user,
                        period_title=row[1],
                        basic_salary=row[2],
                        tax=row[3],
                        insurance=row[4],
                        benefits=row[5],
                        deductions=row[6],
                        final_salary=row[7]
                    )
                    success_count += 1
                except Exception as e:
                    print(f"خطا در ردیف: {row} | خطا: {str(e)}")

            messages.success(request, f"{success_count} ردیف با موفقیت ثبت شد.")
            return redirect('admin:PayrollApp_payroll_changelist')

    else:
        form = PayrollExcelUploadForm()

    context = {'form': form}
    return render(request, 'admin/payroll_excel_upload.html', context)

#ساخت کد یکبار مصرف و  ارسال
class SendOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        if not phone or len(phone) != 11:
            return Response({'error': 'شماره موبایل نامعتبر است'}, status=400)

        # ساخت یا به‌روزرسانی رکورد OTP
        otp_obj, created = OTPRequest.objects.get_or_create(phone_number=phone, is_verified=False)
        otp_obj.created_at = timezone.now()
        otp_obj.code = str(random.randint(100000, 999999))
        otp_obj.save()

        # فعلاً فقط چاپ در کنسول
        print(f"📨 OTP برای {phone}: {otp_obj.code}")

        return Response({'message': 'کد ارسال شد'})
    
#بررسی و تایید کد یکبار مصرف
class VerifyOTPView(APIView):
    def post(self, request):
        phone = request.data.get('phone_number')
        code = request.data.get('code')

        try:
            otp = OTPRequest.objects.filter(phone_number=phone, code=code, is_verified=False).latest('created_at')
        except OTPRequest.DoesNotExist:
            return Response({'error': 'کد نامعتبر است'}, status=400)

        if not otp.is_valid():
            return Response({'error': 'کد منقضی شده است'}, status=400)

        otp.is_verified = True
        otp.save()

        # ساخت یا دریافت کاربر
        user, created = CustomUser.objects.get_or_create(phone_number=phone)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
        })
    
#ورود با کد یکبار مصرف
def login_with_otp_view(request):
    phone_stage = True  # مرحله‌ی شماره موبایل

    if request.method == 'POST':
        form = LoginWithOTPForm(request.POST)

        if 'send_code' in request.POST and form.is_valid():
            phone = form.cleaned_data['phone_number']
            otp = str(random.randint(100000, 999999))

            # ذخیره شماره در سشن
            request.session['otp_phone'] = phone

            # ذخیره OTP در دیتابیس
            OTPRequest.objects.create(phone_number=phone, code=otp)

            messages.success(request, f"کد تایید ارسال شد. (تست: {otp})")
            phone_stage = False

        elif 'verify_code' in request.POST and form.is_valid():
            phone = request.session.get('otp_phone')
            code = form.cleaned_data['code']

            otp_obj = OTPRequest.objects.filter(phone_number=phone, code=code).last()

            if otp_obj and otp_obj.is_valid():
                otp_obj.is_verified = True
                otp_obj.save()

                user, _ = CustomUser.objects.get_or_create(phone_number=phone)
                login(request, user)

                messages.success(request, "با موفقیت وارد شدید.")
                return redirect('dashboard')
            else:
                messages.error(request, "کد تایید اشتباه یا منقضی شده.")
                phone_stage = False
    else:
        form = LoginWithOTPForm()
        if request.session.get('otp_phone'):
            phone_stage = False
            form.fields['phone_number'].initial = request.session['otp_phone']

    return render(request, 'login_with_otp.html', {
        'form': form,
        'phone_stage': phone_stage
    })
