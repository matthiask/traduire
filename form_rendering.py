from django import template
from django.forms.renderers import TemplatesSetting


register = template.Library()


class FormRendering(TemplatesSetting):
    form_template_name = "rendering/form_template.html"
    field_template_name = "rendering/field_template.html"


@register.filter
def adapt_rendering(form):
    form.required_css_class = "is-required"
    form.error_css_class = "has-error"
    form.label_suffix = ""
    return form
