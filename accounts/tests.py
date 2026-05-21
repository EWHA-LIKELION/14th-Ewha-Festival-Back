from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class RefreshViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            kakao_id="test_kakao_123",
            nickname="testuser",
        )
        self.refresh_token = RefreshToken.for_user(self.user)
        self.url = "/accounts/refresh"

    def test_200_OK(self):
        self.client.cookies["refresh"] = str(self.refresh_token)
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["detail"], "토큰을 재발급했어요.")
        self.assertIn("access", res.cookies)
        self.assertIn("refresh", res.cookies)

    def test_401_no_refresh_token(self):
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, 401)

    def test_401_invalid_refresh_token(self):
        self.client.cookies["refresh"] = "invalid.token.value"
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data["detail"], "유효하지 않은 Refresh Token이에요.")

    def test_401_blacked_refresh_token(self):
        old_token = str(self.refresh_token)

        self.client.cookies["refresh"] = old_token
        res1 = self.client.post(self.url)

        self.client.cookies["refresh"] = old_token
        res2 = self.client.post(self.url)

        self.assertEqual(res2.status_code, 401)

    def test_404_user_not_found(self):
        self.user.delete()
        self.client.cookies["refresh"] = str(self.refresh_token)
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data["detail"], "존재하지 않는 사용자예요.")
