from django.core.management import BaseCommand


# from agenda.tasks import generate_events, import_events_for_all_verowa_credentials


class Command(BaseCommand):
    help = "Fairy tasks"

    def handle(self, **options):
        pass
        # import_events_for_all_verowa_credentials()
        # generate_events()
