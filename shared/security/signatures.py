from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def canonical_payload(action: str, payload: dict[str, Any], timestamp: int) -> bytes:
    return json.dumps(
        {"action": action, "payload": payload, "timestamp": timestamp},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_private_key(pem_text: str) -> Ed25519PrivateKey:
    return serialization.load_ssh_private_key(pem_text.encode("utf-8"), password=None)


def load_public_key(ssh_public_key: str) -> Ed25519PublicKey:
    key = serialization.load_ssh_public_key(ssh_public_key.encode("utf-8"))
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("Only Ed25519 public keys are supported")
    return key


def sign_request(private_key_text: str, action: str, payload: dict[str, Any], timestamp: int) -> str:
    private_key = load_private_key(private_key_text)
    signature = private_key.sign(canonical_payload(action, payload, timestamp))
    return base64.b64encode(signature).decode("ascii")


def verify_request_signature(
    public_key_text: str,
    signature_b64: str,
    action: str,
    payload: dict[str, Any],
    timestamp: int,
) -> bool:
    public_key = load_public_key(public_key_text)
    signature = base64.b64decode(signature_b64.encode("ascii"))
    try:
        public_key.verify(signature, canonical_payload(action, payload, timestamp))
        return True
    except InvalidSignature:
        return False
