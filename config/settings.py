"""GrepDojo non-secret default paths and settings."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROGRESS_FILE = os.path.join(BASE_DIR, "grepdojo_progress.json")
LOG_FILE = os.path.join(BASE_DIR, "grepdojo.log")
LOCAL_SETTINGS_FILE = os.path.join(BASE_DIR, "config", "local_settings.json")
