# Traduire

Traduire (french for «translate») is a web-based platform for editing
[gettext](https://www.gnu.org/software/gettext/gettext.html) translations.

It is intended as a replacement for [Transifex](https://www.transifex.com/),
[Weblate](https://weblate.org/en/) and comparable products. It is geared
towards small teams or agencies which want to allow their customers or their
less technical team members to update translations.

It is built using [Django](https://www.djangoproject.com/), heavily relies on
[polib](https://pypi.org/project/polib/) and profits from the great work done
on [django-rosetta](https://github.com/mbi/django-rosetta/).

![Traduire screenshot](./images/traduire.png)

## Features

- Supports several projects out of the box
- Multi user support, projects can only be seen by explicitly selected users
  (and superusers)
- Integrates [DeepL](https://www.deepl.com/) for translation suggestions
- Has a CLI interface for uploading and downloading translation files, see
  [traduire-cli](https://pypi.org/project/traduire-cli/).

## Non-goals

- I'm not interested in review processes.
- I don't intend to implement any sort of automatic SCM integration. It sounds
  great in theory but I'm sceptical.

## What's missing?

- More documentation
- An easy way to get this thing up and running. All it needs is a Django
  hosting environment and a database. It shouldn't be too hard to throw
  together a Docker compose file or something. I'm deploying it in my
  Kubernetes cluster though, so it's not really my itch to scratch.

More issues on [GitHub](https://github.com/matthiask/traduire/issues).
