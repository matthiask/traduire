import os
from pathlib import Path

import speckenv
from django.core.wsgi import get_wsgi_application


BASE_DIR = Path(__file__).resolve().parent

speckenv.read_speckenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
application = get_wsgi_application()
