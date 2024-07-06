# Traduire CLI interface

First, install the client program. The `trd` program is contained in the
`traduire-cli` package. I recommend using [pipx](https://pipx.pypa.io/stable/)
or something comparable:

    pipx install traduire-cli

You need a configuration file, `~/.config/traduire.toml` which contains one or
more records of the following form:

    [[project]]
    name = "Project name"
    token = "asdf...-1"
    url = "https://traduire.example.com/api/pofile/project-name/"
    path = "..."

The name, token, and URL are taken from your Traduire installation. The path is
the folder where your local checkout of the project resides. The `trd` client
uses the configured path to automatically find the correct settings. Right now
there's no support forspecifying the necessary token and URL parameters
directly. (Contributions would be very welcome for this! I think the CLI should
be rewritten to use [Click](https://click.palletsprojects.com/) under the
hood.)

Then, assuming you have your gettext `.po` files inside `project/locale` you
you should first ensure that they are up-to-date:

    python manage.py makemigrations -a

Next, you can upload the pofiles to the Traduire server. All `trd` invocations
automatically find all `*.po` files in the provided folder and act on all of
them.

    trd submit project/locale

After translating everything you can fetch all updates from the server:

    trd get project/locale

You probably want to compile the catalogs now:

    python manage.py compilemessages

Submitting pofiles only uses the `msgid` values (it does the same thing
`msgmerge` does by default). Also, it doesn't delete obsolete strings. If you
know what you're doing you can replace the `.po` files on the server:

    trd replace project/locale
