from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

app_name = "accounts"

# Regular URL patterns
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('confirm/<uuid:token>/', views.confirm_email, name='confirm_email'),
    path('test-email/', views.test_email, name='test_email'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
]

# API URL patterns
api_urlpatterns = [
    path('api/users/', views.UserViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='user-list'),
    
    path('api/users/<int:pk>/', views.UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='user-detail'),
    
    path('api/users/profile/', views.UserViewSet.as_view({
        'get': 'profile',
        'put': 'profile'
    }), name='user-profile'),
]

# Add API URLs to urlpatterns
urlpatterns += format_suffix_patterns(api_urlpatterns)