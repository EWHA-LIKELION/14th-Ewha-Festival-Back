from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('login/kakao/', KakaoLoginView.as_view(), name="kakao_login"),
    path("login/kakao/callback/", KakaoCallbackView.as_view(), name="kakao_callback"),
    path("logout/kakao/", KakaoLogoutView.as_view(), name="kakao_logout"),
    path('my-data/', MyDataView.as_view(), name='my-data'),
    path('my-scrap/', MyScrapView.as_view(), name='my-scrap'),
    path('permission/', Permission.as_view(), name='permission'),
]
