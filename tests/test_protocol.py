from shared.protocol.codec import decode_message, encode_message
from shared.protocol.models import build_request


def test_protocol_roundtrip() -> None:
    request = build_request("ping").to_dict()
    raw = encode_message(request)
    decoded = decode_message(raw)
    assert decoded["action"] == "ping"
    assert decoded["type"] == "request"
