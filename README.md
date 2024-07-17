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
  [traduire-cli](https://github.com/matthiask/traduire/tree/main/cli).

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

## Development

Right now, the fabfile uses [fh-fablib](https://github.com/feinheit/fh-fablib);
if you have fh-fablib installed (preferrably using pipx) you can run:

    fl local
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser
    fl dev

And then access the development server at `http://127.0.0.1:8000/`. The
prerequisites are Python 3.12 or better, yarn, and a local PostgreSQL database
where you can connect without any authentication whatsoever.

The code is formatted using [pre-commit](https://pre-commit.com/) and I welcome
all sorts of contributions. Please open an issue first if you have big ideas.

## Deployment

I'm deploying a container image built using [podman](https://podman.io/) in a
Kubernetes cluster. The `Containerfile` doesn't use a multi-stage build because
it was annoying to set up. Instead, the frontend code is bundled outside the
container, and only the Python image is used. (Contributions to improve this
are welcome as long as they don't slow the development side of things.) You
don't have to deploy it in such an environment however, any Django hosting is
fine.

Traduire needs a few environment variables to be set. The following list should
get you started. All variables are parsed by
[speckenv](https://github.com/matthiask/speckenv/), check it out if you're
unsure about the `*_URL` variables.

    ADMINS="[('Developers', 'dev@example.com')]"
    ALLOWED_HOSTS="['.example.com']"
    DEBUG="False"
    SECRET_KEY="insert-something-secure-here!"
    # I like PostgreSQL, everything should also work fine with other database
    # engines, we're not doing anything exotic.
    DATABASE_URL="postgres://dbuser:dbpass@dbhost/dbname"

    # Using SSL is always a good idea:
    SECURE_SSL_HOST="traduire.example.com"
    SECURE_SSL_REDIRECT="True"

    # You probably want to specify your email settings here:
    EMAIL_URL="smtp://docker-postfix-mail:587?_default_from_email=no-reply@example.com"

    # Optional:
    DEEPL_AUTH_KEY="..."

    # If you want SSO sign ins into the admin panel and elsewhere:
    GOOGLE_CLIENT_ID="..."
    GOOGLE_CLIENT_SECRET="..."
    STAFF_EMAIL_DOMAINS="['example.com']"

    # Sentry is always a good idea:
    SENTRY_DSN="..."
    SENTRY_ENVIRONMENT="production"

Environment variables are automatically read from the `.env` file if it exists.
