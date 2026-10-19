"""Parsing DAP messages is bulky enough to merit its own file of utility functions."""
import json
import re
from typing import Iterator

from constants import Message

_CONTENT_TYPE_PARAM_RE = re.compile(r'(\w+)\s*=\s*(?:(?:"([^"]*)")|([^;,\s]*))')
DAP_SEPARATOR = b"\r\n\r\n"


def parse_content_type(header: str) -> tuple[str, dict[str, str]]:
    """Parse Content-Type header."""
    content_type, _, param_string = header.partition(";")
    content_type = content_type.strip().lower()
    metadata = {m.group(1).lower(): (m.group(2) or m.group(3)) for m in _CONTENT_TYPE_PARAM_RE.finditer(param_string)}
    return content_type, metadata


def parse_one_message(buffer: bytearray) -> list[Message] | None:
    """Parse a single DAP message from a bytearray, clearing the parsed message after parsing it."""

    if DAP_SEPARATOR not in buffer:
        return None

    header_lines, raw_content = bytes(buffer).split(DAP_SEPARATOR, 1)

    headers = {"content-type": "application/vscode-jsonrpc; charset=utf-8"}
    for header_line in header_lines.split(b"\r\n"):
        if b":" in header_line:
            key, value = header_line.decode("ascii").split(": ", 1)
            headers[key.lower()] = value

    assert "content-length" in headers

    # Content-Type and encoding (default if not provided)
    if "content-type" in headers:
        content_type, metadata = parse_content_type(headers["content-type"])
        assert content_type == "application/vscode-jsonrpc"
        encoding = metadata.get("charset", "utf-8")
    else:
        # Default to utf-8 if no content-type header
        encoding = "utf-8"

    content_length = int(headers["content-length"])
    if len(raw_content) < content_length:
        return None
    unused_bytes_count = len(raw_content) - content_length
    raw_content = raw_content[:content_length]
    if unused_bytes_count == 0:
        buffer.clear()
    else:
        del buffer[:-unused_bytes_count]

    try:
        content = json.loads(raw_content.decode(encoding))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON content: {e}")

    return content if isinstance(content, list) else [content]


def parse_messages(buffer: bytearray) -> Iterator[Message]:
    """Parse all complete DAP messages from the given buffer, removing them as they are parsed."""
    while True:
        parsed = parse_one_message(buffer)
        if parsed is None:
            break
        yield from parsed
