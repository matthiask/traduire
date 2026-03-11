import datetime as dt
from dataclasses import dataclass, field

from django.contrib.syndication.views import Feed
from django.http import Http404
from django.utils.timezone import localdate

from accounts.models import User
from projects.models import Event, Project


DIGEST_ACTIONS = frozenset({
    Event.Action.CATALOG_CREATED,
    Event.Action.CATALOG_UPDATED,
    Event.Action.CATALOG_SUBMITTED,
    Event.Action.CATALOG_REPLACED,
    Event.Action.CATALOG_DELETED,
    Event.Action.PROJECT_CREATED,
})


@dataclass
class DigestItem:
    project: Project
    date: dt.date
    events: list = field(default_factory=list)

    @property
    def pub_date(self):
        return self.events[0].created_at if self.events else None

    def description(self):
        lines = []
        for event in reversed(self.events):
            user = str(event.user or event.user_string)
            action = event.get_action_display()
            catalog = event.catalog_string
            if catalog:
                lines.append(f"<li>{user} {action}: {catalog}</li>")
            else:
                lines.append(f"<li>{user} {action}</li>")
        return f"<ul>{''.join(lines)}</ul>"


def _get_user_from_token(request):
    token = request.GET.get("token")
    if not token:
        return None
    return User.objects.filter(token=token, is_active=True).first()


def _events_to_digests(events, max_items=30):
    """Group events by (project, date) into DigestItems, newest first."""
    digests = {}
    for event in events:
        if not event.project_id:
            continue
        date = localdate(event.created_at)
        key = (event.project_id, date)
        if key not in digests:
            digests[key] = DigestItem(project=event.project, date=date)
        digests[key].events.append(event)
    items = sorted(digests.values(), key=lambda d: d.date, reverse=True)
    return items[:max_items]


class AllProjectsFeed(Feed):
    title = "Traduire – All projects"
    description = "Recent activity across all accessible projects"

    def get_object(self, request):
        user = _get_user_from_token(request)
        if not user:
            raise Http404
        return user

    def link(self, user):
        return "/"

    def items(self, user):
        projects = Project.objects.for_user(user)
        events = Event.objects.filter(
            project__in=projects,
            action__in=DIGEST_ACTIONS,
        ).select_related("user", "project")[:500]
        return _events_to_digests(events)

    def item_title(self, item):
        return f"{item.project.name} – {item.date}"

    def item_description(self, item):
        return item.description()

    def item_pubdate(self, item):
        return item.pub_date

    def item_link(self, item):
        return item.project.get_absolute_url()

    def item_guid(self, item):
        return f"{item.project.slug}-{item.date}"

    item_guid_is_permalink = False


class ProjectFeed(Feed):
    def get_object(self, request, slug):
        user = _get_user_from_token(request)
        if not user:
            raise Http404
        project = Project.objects.for_user(user).filter(slug=slug).first()
        if not project:
            raise Http404
        return project

    def title(self, project):
        return f"{project.name} – Traduire"

    def link(self, project):
        return project.get_absolute_url()

    def description(self, project):
        return f"Recent activity in {project.name}"

    def items(self, project):
        events = Event.objects.filter(
            project=project,
            action__in=DIGEST_ACTIONS,
        ).select_related("user")[:500]
        return _events_to_digests(events)

    def item_title(self, item):
        return f"{item.project.name} – {item.date}"

    def item_description(self, item):
        return item.description()

    def item_pubdate(self, item):
        return item.pub_date

    def item_link(self, item):
        return item.project.get_absolute_url()

    def item_guid(self, item):
        return f"{item.project.slug}-{item.date}"

    item_guid_is_permalink = False
