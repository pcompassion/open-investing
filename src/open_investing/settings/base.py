#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import pendulum
import django

import pytz

load_dotenv()

local_timezone = pytz.timezone("Asia/Seoul")  # Replace with your desired timezone

pendulum.set_local_timezone(local_timezone)


django_env = os.getenv("DJANGO_ENV", "base")  # use django_env as default if present
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"open_investing.dashboard.dashboard.settings.{django_env}",
)
django.setup()
