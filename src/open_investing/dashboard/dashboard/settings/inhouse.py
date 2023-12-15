#!/usr/bin/env python3
import os
from dotenv import load_dotenv

from .base import *


dotenv_path = BASE_DIR / ".env.inhouse"
load_dotenv(dotenv_path)


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "risk_glass",
        "USER": "risk_glass",
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": "5435",
    }
}
