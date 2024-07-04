import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
import tomllib


def _terminate(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def _progress(msg):
    print(msg)


def current_project():
    config = Path.home() / ".config" / "traduire.toml"
    if not config.exists():
        _terminate(f"Config file {config} doesn't exist.")

    data = tomllib.loads(config.read_text())
    cwd = str(Path.cwd()).rstrip("/")

    for project in data.get("project", ()):
        if project["path"].rstrip("/") == cwd:
            return project

    _terminate(f"Couldn't find a project for the current working directory {cwd}")  # noqa: RET503


def find_pofiles(root):
    def _generate():
        path = Path(root).resolve()
        for dirpath, _dirnames, filenames in path.walk():
            for filename in filenames:
                if filename.endswith(".po"):
                    yield dirpath / filename

    return list(_generate())


def url_from_pofile(project, pofile):
    return urljoin(
        project["url"],
        f"/api/pofile/{pofile.parts[-3]}/{pofile.parts[-1].removesuffix('.po')}/",
    )


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {"get", "put"}:
        _terminate(f"Usage: {sys.argv[0]} [get,put] path")

    project = current_project()
    session = requests.Session()
    session.headers = {"x-project-token": project["token"]}

    if sys.argv[1] == "get":
        pofiles = find_pofiles(sys.argv[2])
        for pofile in pofiles:
            url = url_from_pofile(project, pofile)
            r = session.get(url, timeout=10)
            if r.ok:
                pofile.write_text(r.content.decode("utf-8"))
                _progress(f"Updated {pofile}")

    elif sys.argv[1] == "put":
        pofiles = find_pofiles(sys.argv[2])
        for pofile in pofiles:
            url = url_from_pofile(project, pofile)
            r = session.put(url, data=pofile.read_bytes())
            if r.ok:
                _progress(f"Submitted {pofile}")


if __name__ == "__main__":
    main()
