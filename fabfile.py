import fh_fablib as fl


fl.require("1.0.20240527")
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


@fl.task(
    auto_shortflags=False,
    help={"force": "Force the git push"},
)
def deploy(ctx, force=False):
    fl._check_branch(ctx)
    fl._check_no_uncommitted_changes(ctx)
    fl.check(ctx)
    force = "--force-with-lease " if (force or fl.config.force) else ""
    fl.run_local(ctx, f"git push origin {force}{fl.config.branch}")
    fl.run_local(ctx, "yarn run rsbuild build")

    with fl.Connection(fl.config.host) as conn, conn.cd(fl.config.domain):
        fl._deploy_sync_origin_url(ctx, conn)
        fl._deploy_django(conn)
        fl.run(
            conn,
            "if [ -e static ]; then find static/ -type f -mtime +60 -delete;fi",
        )
        fl.run_local(
            ctx,
            f"rsync -pthrz --stats tmp/dist/static/ {fl.config.host}:{fl.config.domain}/static/",
        )
        fl._deploy_staticfiles(conn)
        fl._nine_restart(conn)

    fl.fetch(ctx)
    fl.progress(f"Successfully deployed the {fl.config.environment} environment.")


ns = fl.Collection(*fl.GENERAL, dev, deploy)
