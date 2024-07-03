# Traduire

Somewhat working API for cURL.

Read pofile:

    curl -v http://127.0.0.1:8000/api/pofile/de/django/ --header "x-project-token: ..." | less

Write pofile:

    curl -v http://127.0.0.1:8000/api/pofile/fr/django/ --header "x-project-token: ..." --header "content-type: text/plain" -X PUT --data-binary @.../locale/fr/LC_MESSAGES/django.po
