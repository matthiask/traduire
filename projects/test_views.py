from unittest.mock import Mock, patch

from authlib.little_auth.models import User
from django.test import Client, TestCase
from django.test.utils import override_settings

from projects.models import Catalog, Project
from projects.translators import TranslationError, fix_nls


class ProjectsTest(TestCase):
    def test_smoke(self):
        superuser = User.objects.create_superuser("admin@example.com", "admin")
        su_client = Client()
        su_client.force_login(superuser)

        p2 = Project.objects.create(name="test2", slug="test2")
        user = User.objects.create_user("user@example.com", "user")
        user.projects.add(p2)
        u_client = Client()
        u_client.force_login(user)

        p = Project.objects.create(name="test", slug="test")
        c = p.catalogs.create(
            language_code="fr",
            domain="djangojs",
            pofile="""\
#: conf/strings.js frontend/intro/intro.js frontend/people/person.js
msgid "Continue"
msgstr "Continuer"

#: conf/strings.js
msgid "Copied code!"
msgstr "Code copié !"

#: fmw/dashboard/classes/forms.py
#, python-format
msgid "Successfully reset the password of %(count)s student."
msgid_plural "Successfully reset passwords of %(count)s students."
msgstr[0] "Réinitialisation du mot de passe de %(count)s élève."
msgstr[1] "Réinitialisation des mots de passe de %(count)s élèves ."
""",
        )

        r = su_client.get("/", headers={"accept-language": "en"})
        self.assertContains(r, '<a href="/project/test/">test</a>')
        self.assertContains(r, '<a href="/project/test2/">test2</a>')

        r = u_client.get("/", headers={"accept-language": "en"})
        self.assertNotContains(r, '<a href="/project/test/">test</a>')
        self.assertContains(r, '<a href="/project/test2/">test2</a>')

        r = su_client.get(p.get_absolute_url(), headers={"accept-language": "en"})
        self.assertContains(r, p.token)
        self.assertContains(
            r,
            '<a href="/project/test/catalog/fr/djangojs/">French, djangojs (100%)</a>',
        )

        r = u_client.get(p.get_absolute_url(), headers={"accept-language": "en"})
        self.assertEqual(r.status_code, 404)

        r = u_client.get(p2.get_absolute_url(), headers={"accept-language": "en"})
        self.assertEqual(r.status_code, 200)

        r = su_client.get(c.get_absolute_url(), headers={"accept-language": "en"})
        self.assertContains(
            r,
            '<input type="hidden" name="msgid_1" value="Copied code!" id="id_msgid_1">',
        )

        # API test
        r = su_client.get("/api/pofile/fr/djangojs/")
        self.assertEqual(r.status_code, 403)

        r = su_client.get(
            "/api/pofile/fr/djangojs/", headers={"x-project-token": p.token}
        )
        self.assertEqual(r.content.decode("utf-8"), c.pofile)

        r = su_client.post(
            "/api/pofile/fr/djangojs/", headers={"x-project-token": p.token}
        )
        self.assertEqual(r.status_code, 405)

        r = su_client.get(
            "/api/pofile/de/djangojs/", headers={"x-project-token": p.token}
        )
        self.assertEqual(r.status_code, 404)

        r = su_client.put(
            "/api/pofile/fr/djangojs/",
            headers={"x-project-token": p.token},
            data=b"""\
#: conf/strings.js frontend/intro/intro.js frontend/people/person.js
msgid "Continue"
msgstr "Blub"

#: conf/strings.js
msgid "Copied code!"
msgstr ""

msgid "Hello World"
msgstr "Blab"
""",
        )

        c.refresh_from_db()

        self.assertIn(
            """\
msgid "Continue"
msgstr "Continuer"
""",
            c.pofile,
        )

        self.assertIn(
            """\
msgid "Hello World"
msgstr ""
""",
            c.pofile,
        )

        # Different language!
        r = su_client.put(
            "/api/pofile/de/djangojs/",
            headers={"x-project-token": p.token},
            data=b"""\
#: conf/strings.js frontend/intro/intro.js frontend/people/person.js
msgid "Continue"
msgstr "Blub"

#: conf/strings.js
msgid "Copied code!"
msgstr ""

msgid "Hello World"
msgstr "Blab"
""",
        )

        c = p.catalogs.order_by("id").last()

        self.assertIn(
            """\
msgid "Continue"
msgstr "Blub"
""",
            c.pofile,
        )

        self.assertIn(
            """\
msgid "Hello World"
msgstr "Blab"
""",
            c.pofile,
        )

        # print(c.pofile)
        # print(list(c.po))
        # print(r, r.content.decode("utf-8"))

        with override_settings(DEBUG=True):  # Disable ManifestStaticFilesStorage
            r = su_client.get("/admin/projects/project/")

        self.assertContains(r, '<td class="field-explicit_users">-</td>')
        self.assertContains(r, '<td class="field-explicit_users">use***@***.com</td>')

    def test_suggest(self):
        c = Client()

        r = c.get("/suggest/")
        self.assertEqual(r.status_code, 405)

        r = c.post("/suggest/")
        self.assertEqual(r.status_code, 403)

        user = User.objects.create_user("user@example.com", "user")
        c.force_login(user)

        r = c.post("/suggest/")
        self.assertEqual(r.status_code, 400)

        with patch(
            "projects.views.translators.translate_by_deepl", lambda *a: "Bonjour"
        ):
            r = c.post("/suggest/", {"language_code": "fr", "msgid": "Anything"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), {"msgstr": "Bonjour"})

        mock = Mock()
        mock.side_effect = TranslationError("Oops")
        with patch("projects.views.translators.translate_by_deepl", mock):
            r = c.post("/suggest/", {"language_code": "fr", "msgid": "Anything"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), {"error": "Oops"})

    def test_invalid_catalog(self):
        c = Catalog(language_code="it", domain="django", pofile="blub")
        self.assertEqual(str(c), "Italian, django (Invalid)")

    def test_fix_nls(self):
        for test in [
            ("", "", ""),
            ("a\nb", "a\r\nb", "a\nb"),
            ("\na", "a", "\na"),
            ("a\n", "a", "a\n"),
            ("a", "\na\n", "a"),
            ("a", "\n", ""),
        ]:
            with self.subTest(test=test):
                self.assertEqual(fix_nls(test[0], test[1]), test[2])
