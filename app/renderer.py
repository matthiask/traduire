from django.utils.html import mark_safe
from feincms3.renderer import RegionRenderer, render_in_context, template_renderer
from feincms3_cookiecontrol.embedding import embed, oembed


render_richtext = template_renderer("plugins/richtext.html")
render_image = template_renderer("plugins/image.html")


def render_html(plugin, context):
    return mark_safe(plugin.html)


def render_download(plugin, context):
    type = ""
    if plugin.download.name.endswith((".wav", ".ogg", ".mp3", ".aac")):
        type = "audio"
    return render_in_context(
        context, "plugins/download.html", {"plugin": plugin, "type": type}
    )


def render_external(plugin, context):
    return render_in_context(
        context,
        "plugins/external.html",
        {
            "plugin": plugin,
            "html": embed(plugin.url) or oembed(plugin.url),
        },
    )


class ForumRenderer(RegionRenderer):
    def handle_default(self, plugins, context):
        output = (
            self.render_plugin(plugin, context)
            for plugin in self.takewhile_subregion(plugins, "default")
        )
        yield render_in_context(
            context,
            "subregions/default.html",
            {"content": mark_safe("".join(output))},
        )

    def handle_article_bricks(self, plugins, context):
        output = (
            self.render_plugin(plugin, context)
            for plugin in self.takewhile_subregion(plugins, "article_bricks")
        )
        yield render_in_context(
            context,
            "subregions/article_bricks.html",
            {"content": mark_safe("".join(output))},
        )
