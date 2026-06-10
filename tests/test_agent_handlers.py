import asyncio

from agent.handlers.ping import handle_ping


def test_ping_handler() -> None:
    result = asyncio.run(handle_ping())
    assert result["message"] == "pong"
