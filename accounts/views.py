import re

from authlib.email import decode
from authlib.google import GoogleOAuth2Client
from authlib.views import EmailRegistrationForm, retrieve_next, set_next_cookie
from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache

from accounts.forms import UserForm
from accounts.models import User


def logout(request):
    auth.logout(request)
    messages.success(request, _("You have been signed out."))
    response = redirect("login")
    response.delete_cookie("login_hint")
    return response


@never_cache
@set_next_cookie
def google_sso(request):
    auth_params = request.GET.dict()
    auth_params.setdefault("login_hint", request.COOKIES.get("login_hint", ""))
    if request.GET.get("select"):
        auth_params["prompt"] = "consent select_account"
    client = GoogleOAuth2Client(request, authorization_params=auth_params)

    if not request.GET.get("code"):
        return redirect(client.get_authentication_url())

    try:
        user_data = client.get_user_data()
    except Exception:
        messages.error(request, _("Error while fetching user data. Please try again."))
        return redirect("login")

    email = user_data.get("email")
    user = auth.authenticate(request, email=email)
    if user and user.is_active:
        auth.login(request, user)
        next = request.get_signed_cookie("next", default=None, salt="next")
        response = redirect(next if next else "/")
        response.delete_cookie("next")
        response.set_cookie("login_hint", user.email, expires=180 * 86400)
        return response

    if User.objects.filter(email=email).exists():
        messages.error(
            request, _("The user with email address %s is inactive.") % email
        )
        response = HttpResponseRedirect("{}?error=1".format(reverse("login")))
        response.delete_cookie("login_hint")
        return response

    if re.search(settings.SSO_DOMAINS, email):
        user = User(
            email=email, full_name=user_data.get("full_name", ""), role="manager"
        )
        user.set_unusable_password()
        user.save()

        auth.login(request, auth.authenticate(request, email=email))
        messages.info(request, _("Welcome, {}!").format(user.get_full_name()))

        response = redirect(retrieve_next(request) or "/")
        response.set_cookie("login_hint", user.email, expires=180 * 86400)
        return response

    messages.error(
        request,
        _(
            "No user with email address {email} found and email address isn't automatically allowed."
        ).format(email=email),
    )
    response = HttpResponseRedirect("{}?error=1".format(reverse("login")))
    response.delete_cookie("login_hint")
    return response


def register(request, *, code=None):
    if code is None:
        args = [request.POST] if request.method == "POST" else []
        form = EmailRegistrationForm(*args, request=request)
        if form.is_valid():
            form.send_mail()
            messages.success(request, _("Please check your mailbox."))
            return redirect(".")
        return render(request, "registration/register.html", {"form": form})

    try:
        email, _payload = decode(code, max_age=3600)
    except ValidationError as exc:
        [messages.error(request, msg) for msg in exc.messages]
        return redirect("login")

    if User.objects.filter(email=email).exists():
        messages.error(
            request,
            _("An account with the email address {email} exists already.").format(
                email=email
            ),
        )
        return redirect("login")

    args = [request.POST] if request.method == "POST" else []
    user = User(email=email)
    form = UserForm(*args, instance=user)
    if form.is_valid():
        form.save()

        auth.login(request, auth.authenticate(request, email=email))
        messages.info(request, _("Welcome, {}!").format(user.get_full_name()))
        return HttpResponseRedirect("/")

    return render(request, "registration/register.html", {"form": form})
