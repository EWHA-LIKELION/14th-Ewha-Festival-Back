from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('my-data/', MyDataView.as_view(), name='my-data'),
]
