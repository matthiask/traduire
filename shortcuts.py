from functools import wraps

from django.template.response import TemplateResponse


def partial_if_htmx(partial):
    """
    Integrate htmx with django-template-partials

    Only return the named partial if current request uses htmx.
    """

    def decorator(fn):
        @wraps(fn)
        def inner(request, *args, **kwargs):
            response = fn(request, *args, **kwargs)

            if (
                request.htmx
                and isinstance(response, TemplateResponse)
                and isinstance(response.template_name, str)
            ):
                response.template_name += f"#{partial}"

            return response

        return inner

    return decorator
