from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from .forms import (
    CustomerRegistrationForm,
    LoginForm,
    UserProfileUpdateForm,
    PreferencesForm,
    PasswordResetRequestForm,
    SetNewPasswordForm
)
from .models import Notification

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Create a welcome in-app notification
            Notification.objects.create(
                user=user,
                title="Welcome to CineReserve!",
                message=f"Hello {user.first_name}, thank you for joining CineReserve. Enjoy smooth ticket reservations, exclusive coupons like WELCOME100, and AI-powered recommendations!",
                notification_type=Notification.TYPE_SUCCESS
            )
            try:
                send_mail(
                    subject="Welcome to CineReserve",
                    message=(
                        f"Hello {user.first_name or user.username},\n\n"
                        "Your CineReserve account is ready. Browse movies, lock seats in real time, "
                        "and get AI recommendations tailored to you.\n\n"
                        "Coupon to try: WELCOME100\n"
                    ),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cinereserve.local'),
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, f"Registration successful, {user.first_name}! Please log in with your credentials.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            login_id = form.cleaned_data['login_id'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']

            # Resolve user by username OR email
            user_obj = None
            if '@' in login_id:
                try:
                    user_obj = User.objects.get(email__iexact=login_id)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    user_obj = None
            else:
                try:
                    user_obj = User.objects.get(username__iexact=login_id)
                except User.DoesNotExist:
                    user_obj = None

            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
            else:
                user = None

            if user is not None:
                if not user.is_active:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
                    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})

                login(request, user)

                # Set session expiry for Remember Me
                if remember_me:
                    request.session.set_expiry(1209600)  # 2 weeks
                else:
                    request.session.set_expiry(0)  # Browser close

                messages.success(request, f"Welcome back, {user.first_name or user.username}!")

                # Role-based redirection
                if next_url:
                    return redirect(next_url)
                if user.is_admin_user:
                    return redirect('dashboard:admin_dashboard')
                elif user.is_cinema_manager:
                    return redirect('dashboard:manager_dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user
    profile, _ = getattr(user, 'profile', (None, None)), None
    if not hasattr(user, 'profile'):
        from .models import UserProfile
        profile = UserProfile.objects.create(user=user)
    else:
        profile = user.profile

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            p_form = UserProfileUpdateForm(request.POST, request.FILES, instance=user)
            pref_form = PreferencesForm(instance=profile)
            if p_form.is_valid():
                p_form.save()
                messages.success(request, "Your profile information was updated successfully!")
                return redirect('accounts:profile')
        elif 'update_preferences' in request.POST:
            p_form = UserProfileUpdateForm(instance=user)
            pref_form = PreferencesForm(request.POST, instance=profile)
            if pref_form.is_valid():
                pref_form.save()
                messages.success(request, "Your cinema preferences were updated successfully!")
                return redirect('accounts:profile')
    else:
        p_form = UserProfileUpdateForm(instance=user)
        pref_form = PreferencesForm(instance=profile)

    # User statistics
    total_bookings = user.bookings.count()
    confirmed_bookings = user.bookings.filter(booking_status='CONFIRMED').count()
    wishlist_count = user.wishlist_items.count()
    reviews_count = user.reviews.count()

    context = {
        'user_form': p_form,
        'pref_form': pref_form,
        'profile': profile,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'wishlist_count': wishlist_count,
        'reviews_count': reviews_count,
    }
    return render(request, 'accounts/profile.html', context)


def forgot_password_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email__iexact=email)
            if associated_users.exists():
                for user in associated_users:
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_url = request.build_absolute_uri(
                        reverse('accounts:reset_password', kwargs={'uidb64': uid, 'token': token})
                    )
                    # For academic / local demonstration, display a direct reset link
                    request.session['demo_reset_link'] = reset_url
                    messages.success(
                        request,
                        f"Password reset link generated for {email}! (See demo link below)"
                    )
                    return render(request, 'accounts/forgot_password_done.html', {'reset_url': reset_url, 'email': email})
            else:
                messages.warning(request, "No account was found with that email address.")
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password']
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password has been successfully reset! You can now log in.")
                return redirect('accounts:login')
        else:
            form = SetNewPasswordForm()
        return render(request, 'accounts/reset_password.html', {'form': form, 'validlink': True})
    else:
        return render(request, 'accounts/reset_password.html', {'validlink': False})


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    # Mark all as read when viewed
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'accounts/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    if request.method == 'POST':
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
