from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from polling.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('polls/', include('polls.urls')),
    path('quiz/', include('quiz.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'polling.views.handler404'
handler500 = 'polling.views.handler500'
handler403 = 'polling.views.handler403'
handler400 = 'polling.views.handler400' 