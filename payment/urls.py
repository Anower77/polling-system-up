from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('pricing/', views.pricing, name='pricing'),
    path('checkout/<str:plan>/', views.checkout, name='checkout'),
    path('initiate/<str:plan>/', views.initiate_payment, name='initiate'),
    path('success/', views.payment_success, name='success'),
    path('cancel/', views.payment_cancel, name='cancel'),
    path('contact-sales/', views.contact_sales, name='contact_sales'),
] 