import datetime as dt
import re
from urllib.parse import unquote

import time_machine
from authlib.email import (
    decode,
    get_confirmation_code,
    send_registration_mail,
)
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.test.client import RequestFactory

from accounts.models import User
from projects.models import Project


def _messages(response):
    return [m.message for m in response.context["messages"]]


class RegistrationTest(TestCase):
    def test_registration(self):
        p1 = Project.objects.create(slug="p1", _email_domains="example.com")
        p2 = Project.objects.create(slug="p2", _email_domains="example.org")

        client = Client()

        response = client.get("/accounts/register/")

        response = client.post(
            "/accounts/register/",
            {"email": "test@example.com"},
            headers={"accept-language": "en"},
        )
        self.assertRedirects(
            response, "/accounts/register/", fetch_redirect_response=False
        )
        response = client.get("/accounts/register/")
        self.assertEqual(_messages(response), ["Please check your mailbox."])

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = unquote(
            next(line for line in body.splitlines() if "testserver" in line)
        )  # pragma: no branch

        self.assertTrue(
            "http://testserver/accounts/register/dGVzdEBleGFtcGxlLmNvbTo:" in url
        )

        response = client.get(url.rstrip("/") + "0/")
        self.assertRedirects(
            response, "/accounts/login/", fetch_redirect_response=False
        )
        response = client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            _messages(response),
            ["Unable to verify the signature. Please request a new registration link."],
        )

        response = client.get(url)
        self.assertContains(response, "new_password1")

        response = client.post(
            url,
            {
                "full_name": "Max Muster",
                "new_password1": "alksjdlkj23lkrjwlkddlkfj",
                "new_password2": "alksjdlkj23lkrjwlkddlkfj",
            },
            headers={"accept-language": "en"},
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        # print(response, response.content.decode("utf-8"))

        response = client.get("/")
        # print(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_messages(response), ["Welcome, Max Muster!"])

        user = User.objects.get()
        self.assertEqual(user.full_name, "Max Muster")
        self.assertSequenceEqual(set(p1.users.all()), {user})
        self.assertSequenceEqual(set(p2.users.all()), set())

        response = client.post("/accounts/register/", {"email": "test2@example.com"})
        self.assertContains(response, "does not match the email of the account you")

        response = client.get("/accounts/logout/")
        self.assertRedirects(response, "/accounts/login/")

    def test_existing_user(self):
        User.objects.create(email="test@example.com")

        request = RequestFactory().get("/")
        send_registration_mail("test@example.com", request=request)

        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        url = unquote(
            next(line for line in body.splitlines() if "testserver" in line)
        )  # pragma: no branch

        self.assertTrue(
            re.match(
                r"http://testserver/accounts/register/dGVzdEBleGFtcGxlLmNvbTo:", url
            )
        )

        response = self.client.get(url)
        self.assertRedirects(
            response, "/accounts/login/", fetch_redirect_response=False
        )

        response = self.client.get("/accounts/login/")
        self.assertEqual(
            _messages(response),
            ["An account with the email address test@example.com exists already."],
        )

    def test_expiry(self):
        code = get_confirmation_code("test@example.com")
        self.assertTrue(code.startswith("dGVzdEBleGFtcGxlLmNvbTo:"))

        self.assertEqual(decode(code, max_age=5), ["test@example.com", ""])

        with (
            time_machine.travel(dt.timedelta(hours=24)),
            self.assertRaises(ValidationError) as cm,
        ):
            decode(code, max_age=1)

        self.assertEqual(
            cm.exception.messages,
            ["The link is expired. Please request another registration link."],
        )
