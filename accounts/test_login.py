from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.utils.translation import deactivate_all

from accounts import views
from accounts.models import User


def messages(response):
    return [m.message for m in get_messages(response.wsgi_request)]


class FakeFlow:
    EMAIL = "user@example.com"
    RAISE_EXCEPTION = False

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_authentication_url(self):
        auth_params = self.kwargs["authorization_params"]
        return f"http://example.com/auth/?prompt={auth_params.get('prompt', '')}"

    def get_user_data(self):
        if self.RAISE_EXCEPTION:
            raise Exception("Email not verified")
        return {"email": self.EMAIL}


views.GoogleOAuth2Client = FakeFlow


@override_settings(SSO_DOMAINS=r"^.*@example.com$")
class LoginTestCase(TestCase):
    def tearDown(self):
        deactivate_all()

    def test_login(self):
        """Basic login and logout redirects"""
        user = User.objects.create_user("user@example.com", "password")

        self.assertRedirects(self.client.get("/"), "/accounts/login/?next=%2F")

        self.client.login(email=user.email)

        self.assertContains(
            self.client.get("/"), 'action="/accounts/logout/"', 1, status_code=200
        )
        # self.assertRedirects(self.client.get("/accounts/login/"), "/")

    def test_login_hint_removal_on_logout(self):
        """The login_hint cookie is removed when logging out explicitly"""
        user = User.objects.create_user("user@example.com", "password")

        self.client.login(email=user.email)
        self.client.cookies.load({"login_hint": "test@example.com"})

        self.assertEqual(
            self.client.cookies.get("login_hint").value, "test@example.com"
        )
        response = self.client.get("/accounts/logout/")
        self.assertRedirects(response, "/accounts/login/")

        self.assertEqual(self.client.cookies.get("login_hint").value, "")

    def test_server_flow(self):
        """Exercise the OAuth2 webserver flow implementation"""
        FakeFlow.EMAIL = "user@example.org"
        FakeFlow.RAISE_EXCEPTION = False

        client = Client()

        response = client.get("/accounts/login/")
        self.assertNotContains(response, "select=1")

        response = client.get("/accounts/google-sso/")
        self.assertRedirects(
            response, "http://example.com/auth/?prompt=", fetch_redirect_response=False
        )

        response = client.get("/accounts/google-sso/?code=x", HTTP_ACCEPT_LANGUAGE="en")
        self.assertRedirects(response, "/accounts/login/?error=1")
        self.assertEqual(
            messages(response),
            [
                "No user with email address user@example.org found and email address isn't automatically allowed."
            ],
        )

        response = client.get("/accounts/login/?error=1")
        self.assertContains(response, "select=1")

        response = client.get("/accounts/google-sso/?select=1")
        self.assertRedirects(
            response,
            "http://example.com/auth/?prompt=consent select_account",
            fetch_redirect_response=False,
        )

        FakeFlow.EMAIL = "user@example.com"
        response = client.get("/accounts/google-sso/?code=x", HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(messages(response), ["Welcome, user@example.com!"])
        self.assertRedirects(response, "/")
        response = client.post(
            "/accounts/update/",
            {
                "full_name": "Test",
            },
        )
        self.assertEqual(client.cookies.get("login_hint").value, FakeFlow.EMAIL)

        client = Client()
        response = client.get("/accounts/google-sso/?code=x")
        self.assertRedirects(response, "/")
        self.assertEqual(messages(response), [])
        self.assertEqual(client.cookies.get("login_hint").value, FakeFlow.EMAIL)

        # Disabled user
        User.objects.update(is_active=False)
        client = Client()
        FakeFlow.EMAIL = "user@example.com"
        response = client.get("/accounts/google-sso/?code=x", HTTP_ACCEPT_LANGUAGE="en")
        self.assertRedirects(response, "/accounts/login/?error=1")
        self.assertEqual(
            messages(response),
            ["The user with email address user@example.com is inactive."],
        )

        client = Client()
        client.cookies.load({"login_hint": FakeFlow.EMAIL})

        FakeFlow.EMAIL = "user@example.org"
        response = client.get("/accounts/google-sso/?code=x", HTTP_ACCEPT_LANGUAGE="en")
        self.assertRedirects(response, "/accounts/login/?error=1")
        self.assertEqual(
            messages(response),
            [
                "No user with email address user@example.org found and email address isn't automatically allowed."
            ],
        )
        # Login hint cookie has been removed when login fails
        self.assertEqual(client.cookies.get("login_hint").value, "")

    def test_server_flow_user_data_failure(self):
        """Failing to fetch user data shouldn't produce an internal server error"""
        FakeFlow.EMAIL = "user@example.com"
        FakeFlow.RAISE_EXCEPTION = True

        response = self.client.get("/accounts/google-sso/?code=x")
        self.assertRedirects(response, "/accounts/login/")
        self.assertEqual(
            messages(response),
            ["Fehler beim Abrufen von Benutzerdaten. Bitte versuchen Sie es erneut."],
        )

    def test_accounts_update_404(self):
        """No authentication and no saved email address --> 404"""
        response = self.client.get("/accounts/update/")
        self.assertEqual(response.status_code, 404)
