from django.urls import path
from . import views
from .views import SendOTPView, VerifyOTPView, login_with_otp_view

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('select-month/', views.select_month_view, name='select_month'),
    path('payroll/<str:month>/', views.view_payroll_view, name='view_payroll'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('admin/upload-payroll/', views.upload_payroll_excel_view, name='upload_payroll_excel'),
    path('auth/send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('otp-login/', login_with_otp_view, name='login_otp'),
]
