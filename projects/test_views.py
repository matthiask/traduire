from authlib.little_auth.models import User
from django.test import TestCase

from projects.models import Project


class ProjectsTest(TestCase):
    def test_smoke(self):
        user = User.objects.create_superuser("admin@example.com", "admin")
        self.client.force_login(user)

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

        r = self.client.get("/", headers={"accept-language": "en"})

        self.assertContains(r, '<a href="/project/test/">test</a>')

        r = self.client.get(p.get_absolute_url(), headers={"accept-language": "en"})
        self.assertContains(r, p.token)
        self.assertContains(
            r,
            '<a href="/project/test/catalog/fr/djangojs/">French, djangojs (100%)</a>',
        )

        r = self.client.get(c.get_absolute_url(), headers={"accept-language": "en"})
        self.assertContains(
            r,
            '<input type="hidden" name="msgid_1" value="Copied code!" id="id_msgid_1">',
        )

        # API test
        r = self.client.get("/api/pofile/fr/djangojs/")
        self.assertEqual(r.status_code, 403)

        r = self.client.get(
            "/api/pofile/fr/djangojs/", headers={"x-project-token": p.token}
        )
        self.assertEqual(r.content.decode("utf-8"), c.pofile)

        r = self.client.get(
            "/api/pofile/de/djangojs/", headers={"x-project-token": p.token}
        )
        self.assertEqual(r.status_code, 404)

        # print(r, r.content.decode("utf-8"))
