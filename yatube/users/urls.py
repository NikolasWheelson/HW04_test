from django.contrib.auth.views import LogoutView, LoginView, PasswordChangeView
from django.contrib.auth.views import PasswordChangeDoneView, PasswordResetView
from django.contrib.auth.views import PasswordResetDoneView
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'logged_out/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'),
    path(
        'signup/',
        views.SignUp.as_view(template_name='users/signup.html'),
        name='signup'),
    path(
        'login/',
        LoginView.as_view(
            template_name='users/login.html'),
        name='login'),
    path(
        'pasword_change/',
        PasswordChangeView.as_view(
            template_name='users/password_change_form.html'),
        name='password_change'),
    path(
        'password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'),
        name='password_change_done'),
    path(
        'password_reset_form/',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html'),
        name='password_reset_form'),
    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'),
]
