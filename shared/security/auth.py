from __future__ import annotations

import time

from shared.security.signatures import verify_request_signature


def validate_auth_envelope(
    message: dict,
    allowed_public_keys: list[str],
    allow_insecure: bool,
    max_skew_seconds: int = 60,
) -> tuple[bool, str | None]:
    auth = message.get("auth")
    if not auth:
        return (allow_insecure, None if allow_insecure else "Missing auth envelope")

    timestamp = int(auth.get("timestamp", 0))
    if abs(int(time.time()) - timestamp) > max_skew_seconds:
        return (False, "Auth timestamp is outside the allowed skew")

    if allow_insecure and not auth.get("signature"):
        return (True, None)

    public_key = auth.get("public_key")
    signature = auth.get("signature")
    if not public_key or not signature:
        return (False, "Missing public key or signature")

    if allowed_public_keys and public_key not in allowed_public_keys:
        return (False, "Public key is not allowed")

    if not verify_request_signature(
        public_key,
        signature,
        message.get("action", ""),
        message.get("payload", {}),
        timestamp,
    ):
        return (False, "Invalid signature")

    return (True, None)
