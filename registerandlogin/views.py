from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .forms import RegisterForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until email confirmed
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate your ProximityLinked account'
            message = render_to_string('registerandlogin/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(subject, message, 'noreply@proximitylinked.com', [user.email])

            return render(request, 'registerandlogin/email_verification_sent.html')
    else:
        form = RegisterForm()
    return render(request, 'registerandlogin/register.html', {'form': form})


def activate_account(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'registerandlogin/activation_success.html')
    else:
        return render(request, 'registerandlogin/activation_failed.html')


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from .forms import LoginForm
from django.contrib import messages

User = get_user_model()

def login_view(request):
    form = LoginForm(request.POST or None)
    error_message = None

    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['identifier']
        password = form.cleaned_data['password']

        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                user = None
                error_message = "No account found with this email or phone number."

        if user:
            if not user.check_password(password):
                error_message = "Incorrect password."
            elif not user.is_active:
                error_message = "Please activate your account first."
            else:
                login(request, user)
                return redirect('/')  # or dashboard/home

    return render(request, 'registerandlogin/login.html', {'form': form, 'error_message': error_message})


def custom_password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            subject = 'Password Reset Request - ProximityLinked'
            message = render_to_string('registerandlogin/password_reset_email.html', {
                'user': user,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'domain': request.get_host(),
            })
            send_mail(subject, message, 'noreplyproximitylinked@gmail.com', [email])
            return redirect('password_reset_done')

    return render(request, 'registerandlogin/forgot_password.html')

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')  # or wherever you want to send them
