from django.urls import path
from .views import *

app_name = 'shows'

urlpatterns = [
    path('<str:pk>/', ShowDetailView.as_view()),
    path('scrapbook/', ScrapbookShowListView.as_view()),
]