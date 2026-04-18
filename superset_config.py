from superset.config import *

import logging

# =========================
# SECURITY (DEV ONLY)
# =========================
TALISMAN_ENABLED = False

SESSION_COOKIE_SECURE = False
WTF_CSRF_ENABLED = False

# =========================
# HTTP FIX (NO HTTPS REDIRECT)
# =========================
ENABLE_PROXY_FIX = True
PREFERRED_URL_SCHEME = "http"
SUPERSET_WEBSERVER_PROTOCOL = "http"

# =========================
# FEATURES
# =========================
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "ALLOW_FILE_UPLOAD": True,
}

# =========================
# CORS
# =========================
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": {"*": {"origins": "*"}},
}

# =========================
# IFRAME SUPPORT
# =========================
TALISMAN_CONFIG = {
    "content_security_policy": {
        "frame-ancestors": ["'self'", "http://localhost:3000", "http://localhost:8501"],
        "frame-src": ["'self'", "http://localhost:8088", "http://localhost:8501"],
    }
}

# =========================
# UPLOAD CSV FIX
# =========================
UPLOAD_FOLDER = "/app/superset_home/uploads"
UPLOAD_CHUNK_SIZE = 512 * 1024 * 1024

# =========================
# LOGGING
# =========================
LOG_LEVEL = "INFO"
logging.basicConfig(level=logging.INFO)