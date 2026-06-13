import os


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
LOG_DIR = os.path.join(ROOT_DIR, "logs")
UPLOADS_DIR = os.getenv("FORMS_UPLOAD_DIR") or os.path.join(ROOT_DIR, "uploads")
VOICE_REGISTRY_PATH = os.getenv("VOICE_REGISTRY_PATH") or os.path.join(
    BACKEND_DIR, "voice", "voice-registry.json"
)
