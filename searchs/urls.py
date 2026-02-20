from django.urls import path
from .views import *

app_name = 'searchs'

urlpatterns = [
<<<<<<< Updated upstream
=======
    path('', SearchView.as_view()),
    path('scrapbook/', ScrapbookSearchView.as_view()),
>>>>>>> Stashed changes
]