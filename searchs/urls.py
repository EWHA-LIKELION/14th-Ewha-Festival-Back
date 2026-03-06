from django.urls import path
from .views import *

app_name = 'searchs'

urlpatterns = [
    path('', SearchView.as_view()),
]