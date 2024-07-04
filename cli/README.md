# Traduire CLI interface

First, install it:

    pipx install traduire-cli

You need a configuration file, `~/.config/traduire.toml` which contains one or
more records of the following form:

    [[project]]
    name = "..."
    token = "..."
    url = "https://traduire.example.com"
    path = "..."

The name, token, and URL are taken from your Traduire installation. The path is
the folder where your local checkout of the project resides.

Then, assuming you have your gettext `.po` files inside `project/locale` you
can do this to get the pofiles from remote or send your local pofiles to the
remote:

    trd get project/locale
    trd put project/locale
