from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import EmailConfirmation
from rest_framework import viewsets, permissions
from .serializers import UserSerializer, UserProfileSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from smtplib import SMTPException
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

logger = logging.getLogger(__name__)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                # Redirect to the page user came from, or home if no previous page
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('home')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Set to False if email confirmation is needed
            user.save()
            
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def confirm_email(request, token):
    confirmation = get_object_or_404(EmailConfirmation, token=token, is_confirmed=False)
    
    # Activate user
    user = confirmation.user
    user.is_active = True
    user.save()
    
    # Mark confirmation as complete
    confirmation.is_confirmed = True
    confirmation.save()
    
    messages.success(
        request,
        'Email confirmed! You can now login to your account.',
        extra_tags='alert alert-success alert-dismissible fade show'
    )
    return redirect('accounts:login')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out!")
    return redirect('home')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'put'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = UserProfileSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)


def test_email(request):
    try:
        send_mail(
            subject='Test Email',
            message='This is a test email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        return HttpResponse("Test email sent successfully!")
    except Exception as e:
        return HttpResponse(f"Failed to send email: {str(e)}")


@login_required
def profile_view(request):
    context = {
        'user': request.user,
        'polls_count': request.user.poll_set.count(),
        'votes_count': request.user.vote_set.count(),
        'quiz_count': request.user.quiz_set.count() if hasattr(request.user, 'quiz_set') else 0,
    }
    return render(request, 'accounts/profile.html', context)


def password_reset_view(request):
    # Add password reset functionality here
    return render(request, 'accounts/password_reset.html')
