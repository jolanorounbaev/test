from django.urls import path
from .views import register_view, activate_account, login_view, custom_password_reset_request, logout_view
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView, PasswordResetView

urlpatterns = [
    path('register/', register_view, name='register'),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('login/', login_view, name='login'),
    path('forgot-password/', custom_password_reset_request, name='forgot_password'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='registerandlogin/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='registerandlogin/password_reset_complete.html'), name='password_reset_complete'),
    path('reset-sent/', PasswordResetDoneView.as_view(template_name='registerandlogin/password_reset_done.html'), name='password_reset_done'),
    path('logout/', logout_view, name='logout'),
    path('password-reset/', PasswordResetView.as_view(template_name='registerandlogin/password_reset_form.html'), name='password_reset'),
]
