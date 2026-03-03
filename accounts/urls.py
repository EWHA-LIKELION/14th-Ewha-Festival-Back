from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('login/kakao/', KakaoLoginView.as_view(), name="kakao_login"),
    path("login/kakao/callback/", KakaoCallbackView.as_view(), name="kakao_callback"),
]
