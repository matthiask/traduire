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

    # Find local pofiles, and fetch updates from the server for each of them:
    trd get project/locale
    # Submit all local pofiles to the server so that new strings can be translated:
    trd submit project/locale
    # Replace pofiles on the server:
    trd replace project/locale
