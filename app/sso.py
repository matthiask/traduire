from authlib.little_auth.models import User


def create_user_callback(request, user_mail):
    # SSO users automatically get superuser access
    user = User(email=user_mail, is_staff=True, is_superuser=True)
    user.set_unusable_password()
    user.save()
