import fh_fablib as fl


fl.require("1.0.20240904")
fl.config.update(
    domain="traduire.feinheit.dev",
    branch="main",
    remote="production",
)


@fl.task(auto_shortflags=False)
def dev(ctx, host="127.0.0.1", port=8000):
    fl._concurrently(
        ctx,
        [
            f".venv/bin/python manage.py runserver 0.0.0.0:{port}",
            f"yarn run rsbuild dev --host {host}",
        ],
    )


ns = fl.Collection(*fl.GENERAL, dev)
