from django.urls import path
from .views import *

app_name = 'shows'

urlpatterns = [
    path('', ShowListView.as_view()),
    path('<str:pk>/', ShowDetailView.as_view()),
    path('scrapbook/', ScrapbookShowListView.as_view()),
]