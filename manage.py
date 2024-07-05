#!/usr/bin/env python
import os
import sys

import speckenv


if __name__ == "__main__":  # pragma: no branch
    speckenv.read_speckenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
