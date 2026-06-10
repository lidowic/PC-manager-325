from client.ui.terminal.ansi_renderer import AnsiTerminalBuffer


def test_ansi_buffer_consumes_escape_sequences() -> None:
    buffer = AnsiTerminalBuffer(columns=20, rows=5)
    rendered = buffer.feed(b"\x1b[31mhello\x1b[0m")
    assert "hello" in rendered
