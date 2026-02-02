from django.urls import path
from .views import *

app_name = 'booths'

urlpatterns = [
    path('<str:pk>/', BoothDetailView.as_view()),
]