from django.urls import path
from . import views 
from django.conf import settings

urlpatterns=[
    path('', views.home, name='home'), 
    path("OTPVerification/", views.OTPVerification, name="OTPVerification"),
]