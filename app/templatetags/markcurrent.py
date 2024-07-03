import re

from django import template


register = template.Library()


class_matcher = re.compile('(class="[^"]+)(")')
tag_matcher = re.compile(r"<([a-z0-9]+)([ >])")


def markcurrent(navigation, *, current, base=None):
    """
    searches for links and marks the links 'active' (add the class "active")
    depending on the request.path.

    usage::

        {% markcurrent request.path %}
          <li><a href="/">Home</a></li>
          <li><a href="/products/">Products</a></li>
        {% endmarkcurrent %}

    resulting in (assuming request.path == '/products/')::

        <li><a href="/">Home</a></li>
        <li class="active"><a class="active" href="/products/">Products</a>\
            </li>

    .. note::

        This tag works line by line. so if <li> and <a ..> are on the same
        line, both get marked.
    """

    lines = navigation.splitlines()
    out = []
    for line in lines:
        if match := re.search(r'href="([^"]+)"', line):
            href = match.groups()[0]
            # The href must be:
            # - a prefix of the current path
            # - either we have an exact match (then it's obviously the current URL)
            #   or the link doesn't point to the current base
            if current.startswith(href) and (href == current or href != base):
                if class_matcher.search(line):
                    out.append(class_matcher.sub(r"\1 active\2", line))
                else:
                    out.append(tag_matcher.sub(r'<\1 class="active"\2', line))
                continue
        out.append(line)

    return "\n".join(out)


def do_markcurrent(parser, token):
    contents = token.split_contents()
    kwargs = {"base": template.Variable('"/"')}
    if 2 <= len(contents) <= 3:
        kwargs["current"] = template.Variable(contents[1])
        if len(contents) == 3:
            kwargs["base"] = template.Variable(contents[2])
    else:
        raise template.TemplateSyntaxError(
            f"{token.contents.split()[0]!r} tag requires one or two arguments"
        )

    nodelist = parser.parse(("endmarkcurrent",))
    parser.delete_first_token()
    return MarkCurrentNode(nodelist, **kwargs)


class MarkCurrentNode(template.Node):
    def __init__(self, nodelist, current, base):
        self.nodelist = nodelist
        self.current = current
        self.base = base

    def render(self, context):
        output = self.nodelist.render(context)
        return markcurrent(
            output,
            current=self.current.resolve(context),
            base=self.base.resolve(context) if self.base else None,
        )


register.tag("markcurrent", do_markcurrent)
