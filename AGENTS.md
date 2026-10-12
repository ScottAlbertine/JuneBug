# JuneBug — Agent Notes

## Python Toolchain

This is a `direnv` project (`.envrc` uses `layout python3`). The Python virtual environment lives at `.direnv/python-3.14/`.

## PyCharm Attached File Truncation

When a file is attached to the issue from PyCharm (via `<attached_files_content>`), long lines exceeding **~2048 characters** are truncated with `... (truncated)` appended. This affects any file with very long lines, such as:
- Long string literals or docstrings
- Inline JSON/schema comments
- Auto-generated code with wide lines

**Workaround:** When you need to see the full content of a long line, open the file directly from disk using the `open` tool instead of relying on the attached file view. The actual file on disk has the complete, untruncated content.

## create Payload Size Limit

The `create` tool has **two** hidden input size limits that cause **silent truncation** — it reports success even though content was lost:

1. **Per-line limit**: Lines exceeding approximately **~4500 characters** are truncated mid-character.
2. **Total payload limit**: The `content` parameter is truncated at approximately **~7000 bytes**. Content beyond this is silently dropped — subsequent lines are lost entirely.

### Workaround

- **Keep lines under ~4000 characters** and **total content under ~6000 bytes** to stay safely within limits.
- For large files (500+ lines or 6KB+ content), **use `bash` to generate the file** instead of `create`:
  ```bash
  python3 -c "
  with open('large_file.txt', 'w') as f:
      for i in range(1000):
          f.write(f'Line {i}: content\n')
  "
  ```
- For very large files, prefer `bash` with heredocs or Python scripts over `create`.
