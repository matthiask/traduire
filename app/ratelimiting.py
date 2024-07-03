from functools import partial

from django_ratelimit.decorators import ratelimit


def get_client_ip(request):
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


ip_ratelimit = partial(
    ratelimit,
    group="login",
    key=lambda group, request: get_client_ip(request),
    method=ratelimit.UNSAFE,
    block=True,
)

username_ratelimit = partial(
    ratelimit,
    group="login",
    key="post:username",
    method=ratelimit.UNSAFE,
    block=True,
)
