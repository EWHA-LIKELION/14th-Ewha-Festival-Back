from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def make_token_response(ok=True):
    mock = MagicMock()
    mock.status_code = 200 if ok else 400
    mock.json.return_value = {"access_token": "fake_access_token"} if ok else {"error": "bad_request"}
    return mock

def make_profile_response(kakao_id=12345, ok=True):
    mock = MagicMock()
    mock.status_code = 200 if ok else 401
    mock.json.return_value = {
        "id": kakao_id,
        "properties": {"nickname": "테스트유저"},
    } if ok else {}
    return mock

@patch("accounts.views.requests.get")
@patch("accounts.views.requests.post")
class KakaoCallbackViewTest(APITestCase):
    def setUp(self):
        self.url = "/accounts/login/kakao/callback/"

    # ── 성공 ──────────────────────────────────────────────────────────────────

    def test_200_redirects_with_jwt_cookies(self, mock_post, mock_get):
        mock_post.return_value = make_token_response(ok=True)
        mock_get.return_value = make_profile_response(ok=True)

        res = self.client.get(self.url, {"code": "valid_code", "state": "prod"})

        self.assertEqual(res.status_code, 302)
        self.assertIn("access", res.cookies)
        self.assertIn("refresh", res.cookies)

    def test_creates_user_on_first_login(self, mock_post, mock_get):
        mock_post.return_value = make_token_response(ok=True)
        mock_get.return_value = make_profile_response(kakao_id=99999, ok=True)

        self.client.get(self.url, {"code": "valid_code", "state": "prod"})

        self.assertTrue(User.objects.filter(kakao_id="99999").exists())

    def test_does_not_duplicate_user_on_second_login(self, mock_post, mock_get):
        User.objects.create_user(kakao_id="99999", nickname="기존유저")
        mock_post.return_value = make_token_response(ok=True)
        mock_get.return_value = make_profile_response(kakao_id=99999, ok=True)

        self.client.get(self.url, {"code": "valid_code", "state": "prod"})

        self.assertEqual(User.objects.filter(kakao_id="99999").count(), 1)

    # ── 실패 ──────────────────────────────────────────────────────────────────

    def test_400_no_code(self, mock_post, mock_get):
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, 400)
        mock_post.assert_not_called()

    def test_401_token_request_fails(self, mock_post, mock_get):
        mock_post.return_value = make_token_response(ok=False)

        res = self.client.get(self.url, {"code": "bad_code"})

        self.assertEqual(res.status_code, 401)
        mock_get.assert_not_called()

    def test_401_no_access_token_in_response(self, mock_post, mock_get):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {}
        mock_post.return_value = mock

        res = self.client.get(self.url, {"code": "valid_code"})

        self.assertEqual(res.status_code, 401)

    def test_401_profile_request_fails(self, mock_post, mock_get):
        mock_post.return_value = make_token_response(ok=True)
        mock_get.return_value = make_profile_response(ok=False)

        res = self.client.get(self.url, {"code": "valid_code"})

        self.assertEqual(res.status_code, 401)

    def test_401_no_kakao_id_in_profile(self, mock_post, mock_get):
        mock_post.return_value = make_token_response(ok=True)
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"properties": {"nickname": "유저"}}
        mock_get.return_value = mock

        res = self.client.get(self.url, {"code": "valid_code"})

        self.assertEqual(res.status_code, 401)

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
