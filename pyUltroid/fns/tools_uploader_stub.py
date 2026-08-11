# Sanitize uploader routines to avoid shell/curl usage in hosted builds
import os

HOSTED_SANITIZED = os.environ.get("HOSTED_SANITIZED", "1") == "1"

# existing imports
import json
import subprocess
import os

async def web_uploader_stub(*args, **kwargs):
    if HOSTED_SANITIZED:
        return "Uploader disabled in hosted build."
    # fallback path (not used in hosted mode)
    return None

# Replace dangerous parts in uploader function
# We'll add a simple wrapper that checks HOSTED_SANITIZED before using subprocess.

# The actual function in original file is complex; we add a safe early return by monkeypatching
