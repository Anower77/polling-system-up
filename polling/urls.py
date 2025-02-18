from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('polls/', include('polls.urls', namespace='polls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('quiz/', include('quiz.urls', namespace='quiz')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('payment/', include('payment.urls')),
]

# Error handlers
handler404 = 'polling.views.handler404'
handler500 = 'polling.views.handler500'
handler403 = 'polling.views.handler403'
handler400 = 'polling.views.handler400' 