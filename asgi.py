import os
from pathlib import Path

import speckenv
from blacknoise import BlackNoise
from django.core.asgi import get_asgi_application


BASE_DIR = Path(__file__).resolve().parent


speckenv.read_speckenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = BlackNoise(
    get_asgi_application(),
    immutable_file_test=lambda *a: True,
)
application.add(BASE_DIR / "static", "/static/")
