# Traduire

Traduire (french for «translate») is a web-based platform for editing
[gettext](https://www.gnu.org/software/gettext/gettext.html) translations.

It is intended as a replacement for [Transifex](https://www.transifex.com/),
[Weblate](https://weblate.org/en/) and comparable products. It is geared
towards small teams or agencies which want to allow their customers and their
less technical team members to update translations.

Traduire profits from the great work done on
[django-rosetta](https://github.com/mbi/django-rosetta/). I would still be
using Rosetta if it would work when used with a container orchestator such as
Kubernetes. Since all application storage is ephemeral that doesn't work,
translation editing and deployment have to be separated.

It is built using [Django](https://www.djangoproject.com/) and relies on
[polib](https://pypi.org/project/polib/) to do the heavy lifting.

![Traduire screenshot](./images/traduire.png)

## Features

- Supports several projects.
- Multi user support, projects can only be seen by explicitly selected users
  (and staff members).
- Integrates [DeepL](https://www.deepl.com/) for translation suggestions
- Has a CLI interface for uploading and downloading translation files, see
  [traduire-cli](https://pypi.org/project/traduire-cli/).

## Non-goals

- I'm not interested in review processes.
- I don't intend to implement any sort of automatic SCM integration. It sounds
  great in theory but I'm sceptical.

## What's missing?

- More documentation.
- An easy way to get this thing up and running. All it needs is a Django
  hosting environment and a database. It shouldn't be too hard to throw
  together a Docker compose file or something. I'm deploying it in my
  Kubernetes cluster though, so it's not really my itch to scratch.

More issues on [GitHub](https://github.com/matthiask/traduire/issues).
