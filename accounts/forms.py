from django import forms
from django.contrib.auth.forms import SetPasswordMixin
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class UserForm(SetPasswordMixin, forms.ModelForm):
    new_password1, new_password2 = SetPasswordMixin.create_password_fields(
        label1=_("New password"), label2=_("New password confirmation")
    )

    class Meta:
        model = User
        fields = ["email", "full_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].disabled = True

    def clean(self):
        self.validate_passwords("new_password1", "new_password2")
        self.validate_password_for_user(self.instance, "new_password2")
        return super().clean()

    def save(self):
        return self.set_password_and_save(self.instance, "new_password1", commit=True)
