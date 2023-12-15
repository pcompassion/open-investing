#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv
from pathlib import Path


def main():
    """Run administrative tasks."""
    load_dotenv()
    django_env = os.getenv("DJANGO_ENV", "base")  # use django_env as default if present
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"dashboard.settings.{django_env}")
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
