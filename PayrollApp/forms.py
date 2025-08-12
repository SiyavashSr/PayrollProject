from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import authenticate
from .models import CustomUser, Payroll, ExcelUpload


# -------------------------
# 1. فرم ورود با رمز عبور
# -------------------------
class LoginWithPasswordForm(forms.Form):
    phone_number = forms.CharField(label="شماره موبایل", max_length=11)
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)

    def clean(self):
        phone = self.cleaned_data.get('phone_number')
        pwd = self.cleaned_data.get('password')
        user = authenticate(phone_number=phone, password=pwd)
        if not user:
            raise forms.ValidationError("نام کاربری یا رمز عبور اشتباه است")
        return self.cleaned_data


# -------------------------
# فرم ورود با کد یکبار مصرف + ارسال مجدد
# -------------------------
# class LoginWithOTPForm(forms.Form):
#     phone_number = forms.CharField(label="شماره موبایل", max_length=11)
#     code = forms.CharField(label="کد یکبار مصرف", max_length=6, required=False)
#     resend_code = forms.BooleanField(label="ارسال مجدد کد", required=False)

#     def clean(self):
#         phone = self.cleaned_data.get("phone_number")
#         code = self.cleaned_data.get("code")
#         resend = self.cleaned_data.get("resend_code")

#         if not resend and not code:
#             raise forms.ValidationError("لطفاً کد را وارد کنید یا ارسال مجدد را بزنید")

#         # اعتبارسنجی کد در view انجام خواهد شد
#         return self.cleaned_data
class LoginWithOTPForm(forms.Form):
    phone_number = forms.CharField(label="شماره موبایل", max_length=11, required=True)
    code = forms.CharField(label="کد تأیید", max_length=6, required=False)

# -------------------------
# 2. فرم آپلود اکسل فیش حقوقی
# -------------------------
class PayrollExcelUploadForm(forms.Form):
    file = forms.FileField(label="آپلود فایل اکسل فیش حقوقی")
    class Meta:
        model = ExcelUpload
        fields = ['file']


# -------------------------
# 3. فرم آپلود اکسل کاربران
# -------------------------
class UserExcelUploadForm(forms.Form):
    file = forms.FileField(label='آپلود فایل اکسل')
    class Meta:
        model = ExcelUpload
        fields = ['file']


# -------------------------
# 4. فرم ثبت دستی کاربر توسط ادمین
# -------------------------
class AdminUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار رمز عبور", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('phone_number', 'full_name')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمزها یکسان نیستند")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# -------------------------
# 5. فرم تغییر رمز عبور توسط کاربر (با بررسی رمز فعلی)
# -------------------------
class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="رمز قبلی", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="رمز جدید", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="تکرار رمز جدید", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if not self.user.check_password(old):
            raise forms.ValidationError("رمز قبلی اشتباه است")
        return old

    def clean(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمزهای جدید با هم مطابقت ندارند")
        return self.cleaned_data


# -------------------------
# 6. فرم انتخاب ماه از روی دیتاهای واقعی
# -------------------------
class MonthSelectForm(forms.Form):
    month = forms.ChoiceField(label="انتخاب ماه", choices=[])

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        months = Payroll.objects.filter(user=user).values_list("month", flat=True).distinct()
        self.fields["month"].choices = [(m, m) for m in sorted(months)]
