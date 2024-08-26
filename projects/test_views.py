from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.test.utils import override_settings

from accounts.models import User
from projects.models import Catalog, Event, Project
from projects.translators import TranslationError, fix_nls


def messages(response):
    return [m.message for m in get_messages(response.wsgi_request)]


class ProjectsTest(TestCase):
    def create_project_and_catalog(self):
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
        return p, c

    def test_project_access(self):
        superuser = User.objects.create_superuser("admin@example.com", "admin")
        su_client = Client()
        su_client.force_login(superuser)

        p, _c = self.create_project_and_catalog()

        p2 = Project.objects.create(name="test2", slug="test2")
        user = User.objects.create_user("user@example.com", "user")
        user.projects.add(p2)
        u_client = Client()
        u_client.force_login(user)

        r = su_client.get("/", headers={"accept-language": "en"})
        self.assertContains(r, '<a href="/test/">test</a>')
        self.assertContains(r, '<a href="/test2/">test2</a>')

        r = u_client.get("/", headers={"accept-language": "en"})
        self.assertNotContains(r, '<a href="/test/">test</a>')
        self.assertContains(r, '<a href="/test2/">test2</a>')

        r = su_client.get(p.get_absolute_url(), headers={"accept-language": "en"})
        self.assertContains(r, f"token = &quot;{superuser.token}&quot;")
        self.assertContains(
            r,
            '<a href="/test/fr/djangojs/">French, djangojs (100%)</a>',
        )

        r = su_client.get("/traduire.toml")
        self.assertContains(r, f'token = "{superuser.token}"')

        r = su_client.get("/test/messages.csv")
        self.assertContains(r, ",Continue,")

        r = u_client.get(p.get_absolute_url(), headers={"accept-language": "en"})
        self.assertEqual(r.status_code, 404)

        r = u_client.get(p2.get_absolute_url(), headers={"accept-language": "en"})
        self.assertEqual(r.status_code, 200)

    def test_filtering(self):
        superuser = User.objects.create_superuser("admin@example.com", "admin")
        su_client = Client()
        su_client.force_login(superuser)

        _p, c = self.create_project_and_catalog()

        r = su_client.get(c.get_absolute_url(), headers={"accept-language": "en"})
        self.assertContains(r, "msgid_0")
        self.assertContains(
            r,
            '<input type="hidden" name="msgid_1" value="Copied code!" id="id_msgid_1">',
        )

        r = su_client.get(
            c.get_absolute_url() + "?start=1000", headers={"accept-language": "en"}
        )
        self.assertContains(r, "msgid_0")
        self.assertContains(
            r,
            '<input type="hidden" name="msgid_1" value="Copied code!" id="id_msgid_1">',
        )

        r = su_client.get(
            c.get_absolute_url() + "?start=1", headers={"accept-language": "en"}
        )
        self.assertContains(r, "msgid_0")
        self.assertContains(
            r,
            '<input type="hidden" name="msgid_0" value="Copied code!" id="id_msgid_0">',
        )

        r = su_client.get(
            c.get_absolute_url() + "?pending=on", headers={"accept-language": "en"}
        )
        self.assertNotContains(r, "msgid_0")

        r = su_client.get(
            c.get_absolute_url() + "?query=bla", headers={"accept-language": "en"}
        )
        self.assertNotContains(r, "msgid_0")

        r = su_client.get(
            c.get_absolute_url() + "?start=a", headers={"accept-language": "en"}
        )
        self.assertRedirects(r, c.get_absolute_url())

    def test_api(self):
        superuser = User.objects.create_superuser("admin@example.com", "admin")
        su_client = Client()
        su_client.force_login(superuser)

        p, c = self.create_project_and_catalog()

        # API test
        r = su_client.get(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-cli-api": "anything"},
        )
        self.assertEqual(r.status_code, 400)

        r = su_client.get(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 403)

        r = su_client.get(
            "/api/pofile/not-exists/fr/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 404)

        r = su_client.get(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content.decode("utf-8"), c.pofile)

        r = su_client.patch(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 405)

        r = su_client.get(
            "/api/pofile/test/de/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 404)

        r = su_client.post(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
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
            content_type="text/plain",
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
            "/api/pofile/test/de/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
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
#: conf/strings.js frontend/intro/intro.js frontend/people/person.js
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

        # Delete catalogs through the API. Not currently exposed in the CLI.
        r = su_client.delete(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 204)

        r = su_client.delete(
            "/api/pofile/test/fr/djangojs/",
            headers={"x-token": superuser.token, "x-cli-api": settings.CLI_API},
        )
        self.assertEqual(r.status_code, 404)

    def test_updating(self):
        superuser = User.objects.create_superuser("admin@example.com", "admin")
        su_client = Client()
        su_client.force_login(superuser)

        p, c = self.create_project_and_catalog()

        with override_settings(DEEPL_AUTH_KEY="hello"):
            r = su_client.get(
                c.get_absolute_url(),
                headers={"accept-language": "en"},
            )
            self.assertContains(r, "data-suggest")

        with override_settings(DEEPL_AUTH_KEY=""):
            r = su_client.get(
                c.get_absolute_url(),
                headers={"accept-language": "en"},
            )
            self.assertNotContains(r, "data-suggest")

        r = su_client.post(
            c.get_absolute_url(),
            {
                "msgid_0": "Continue",
                "msgstr_0": "Onward!",  # Obviously incorrect.
                "fuzzy_0": "on",
                "msgid_1": "not exists",
                "msgstr_1": "not exists",
                "fuzzy_1": "",
            },
            headers={"accept-language": "en"},
        )
        self.assertRedirects(r, c.get_absolute_url() + "?start=0")

        c.refresh_from_db()
        self.assertIn(
            """\
#: conf/strings.js frontend/intro/intro.js frontend/people/person.js
#, fuzzy
msgid "Continue"
msgstr "Onward!"
""",
            c.pofile,
        )

        # Didn't exist, is ignored
        self.assertNotIn("not exists", c.pofile)

        r = su_client.post(
            c.get_absolute_url() + "?query=continue",
            {
                "msgid_0": "Continue",
                "msgstr_0": "Onward!",  # Obviously incorrect.
                "fuzzy_0": "",
            },
            headers={"accept-language": "en"},
        )
        self.assertRedirects(r, c.get_absolute_url() + "?query=continue&start=0")

        c.refresh_from_db()
        self.assertIn(
            """\
#: conf/strings.js frontend/intro/intro.js frontend/people/person.js
msgid "Continue"
msgstr "Onward!"
""",
            c.pofile,
        )

        r = su_client.post(
            c.get_absolute_url() + "?query=continue",
            {
                "msgid_0": "Continue",
                "msgstr_0": "Onward!",  # Obviously incorrect.
                "fuzzy_0": "",
            },
            headers={"accept-language": "en"},
        )
        self.assertRedirects(
            r,
            c.get_absolute_url() + "?query=continue&start=0",
            fetch_redirect_response=False,
        )

        response = su_client.get(c.get_absolute_url())
        self.assertEqual(messages(response), ["No changes detected."])

        c = p.catalogs.create(
            language_code="es",
            domain="djangojs",
            pofile="""\
#: fmw/dashboard/classes/forms.py
#, python-format
msgid "Successfully reset the password of %(count)s student."
msgid_plural "Successfully reset passwords of %(count)s students."
msgstr[0] "Réinitialisation du mot de passe de %(count)s élève."
msgstr[1] "Réinitialisation des mots de passe de %(count)s élèves ."
""",
        )
        r = su_client.post(
            c.get_absolute_url(),
            {
                "msgid_0": "Successfully reset the password of %(count)s student.",
                "msgstr_0:0": "Blub %(count)s",
                "msgstr_0:1": "Blab %(count)s",
            },
            headers={"accept-language": "en"},
        )

        c.refresh_from_db()
        self.assertIn(
            """\
#: fmw/dashboard/classes/forms.py
#, python-format
msgid "Successfully reset the password of %(count)s student."
msgid_plural "Successfully reset passwords of %(count)s students."
msgstr[0] "Blub %(count)s"
msgstr[1] "Blab %(count)s"
""",
            c.pofile,
        )

        # print(c.pofile)
        # print(list(c.po))
        # print(r, r.content.decode("utf-8"))

    def test_admin(self):
        superuser = User.objects.create_superuser("admin@example.com", "admin")
        su_client = Client()
        su_client.force_login(superuser)

        self.create_project_and_catalog()

        p2 = Project.objects.create(name="test2", slug="test2")
        user = User.objects.create_user("user@example.com", "user")
        user.projects.add(p2)

        with override_settings(DEBUG=True):  # Disable ManifestStaticFilesStorage
            r = su_client.get("/admin/projects/project/")

        self.assertContains(r, '<td class="field-explicit_users">-</td>')
        self.assertContains(
            r, '<td class="field-explicit_users"> &lt;user@example.com&gt;</td>'
        )

    def test_suggest(self):
        c = Client()

        r = c.get("/api/suggest/")
        self.assertEqual(r.status_code, 405)

        r = c.post("/api/suggest/")
        self.assertEqual(r.status_code, 403)

        user = User.objects.create_user("user@example.com", "user")
        c.force_login(user)

        r = c.post("/api/suggest/")
        self.assertEqual(r.status_code, 400)

        with patch(
            "projects.views.translators.translate_by_deepl", lambda *a: "Bonjour"
        ):
            r = c.post("/api/suggest/", {"language_code": "fr", "msgid": "Anything"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), {"msgstr": "Bonjour"})

        mock = Mock()
        mock.side_effect = TranslationError("Oops")
        with patch("projects.views.translators.translate_by_deepl", mock):
            r = c.post("/api/suggest/", {"language_code": "fr", "msgid": "Anything"})
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

    def test_event_save(self):
        user = User.objects.create_superuser("admin@example.com", "admin")
        p, c = self.create_project_and_catalog()

        p2 = Project.objects.create(name="test2", slug="test2")

        e = Event.objects.create(
            user=user,
            action=Event.Action.CATALOG_CREATED,
            catalog=c,
        )
        self.assertEqual(str(e), "created catalog")
        self.assertEqual(e.project, p)

        e = Event.objects.create(
            user=user,
            action=Event.Action.CATALOG_CREATED,
            catalog=c,
            project=p2,  # Makes no sense but is allowed
        )
        self.assertEqual(str(e), "created catalog")
        self.assertEqual(e.project, p2)

        e = Event.objects.create(
            action=Event.Action.CATALOG_CREATED,
        )
        self.assertEqual(str(e), "created catalog")

        e = Event.objects.create(
            user=user,
            action=Event.Action.CATALOG_CREATED,
            project=p2,
        )
        self.assertEqual(str(e), "created catalog")

        self.assertEqual(
            list(Event.objects.values_list("action", flat=True)),
            [
                "catalog-created",
                "catalog-created",
                "catalog-created",
                "catalog-created",
                "project-created",
                "project-created",
                "user-created",
            ],
        )

    def test_event_log(self):
        self.create_project_and_catalog()

        self.assertEqual(
            list(Event.objects.values_list("action", flat=True)),
            ["project-created"],
        )
