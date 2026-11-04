# Junie Harness Bugs And Workarounds

## File Reading Tool Line Truncation

Several file-reading tools truncate long lines. This can cause you to miss content when reading files with long lines (e.g., minified code, base64-encoded strings, long log entries, or generated data).

### Truncation Behavior by Tool

| Tool | Truncates? | Threshold | Behavior |
|------|------------|-----------|----------|
| File attachment (PyCharm) | Yes | ~500 chars | Appends `... (truncated)` |
| `open` | Yes | ~2048 chars | Shows first ~30 chars + `...(N characters truncated, it's impossible to view or edit this line)` |
| `open_entire_file` | Yes | ~2048 chars | Identical to `open` |
| `mcp_pycharm_read_file` | **No** | None | Returns full untruncated content |
| `cat` (via bash) | **No** | None | Returns full untruncated content |

### Workaround

- **Always use `mcp_pycharm_read_file`** when you need to see the full untruncated content of files.
- **Be watchful for `... (truncated)` markers on attached files**. That string is incredibly rare in real files, it's safe to assume that there's more content there.
- **`open` and `open_entire_file` are fine** for normal code files with lines under ~2048 characters, as they provide good context. Just be aware they won't show longer lines in full.
- **If `mcp_pycharm_read_file` is unavailable** or you need to verify content, fall back to `bash` with `cat` to get untruncated output.

## multi_edit Payload Size Limit

The `multi_edit` tool has a hidden input size limit. When the total JSON payload (all search/replace blocks combined) exceeds approximately **3500–4500 bytes**, the tool fails with the misleading error:

> "Missing or invalid edits parameter"

The parameter is not actually missing — the payload is being truncated or rejected upstream. The limit is based on **total payload size**, not the number of edits.

### Workaround

For large files (500+ lines) or edits with long search/replace blocks (10+ lines each):

- **Use multiple `search_replace` calls** instead of a single `multi_edit` call
- `search_replace` (single edit) does not have this limit and works with large blocks
- Keep individual `multi_edit` payloads under ~3500 bytes when possible
- Split large multi-edit operations into 2–3 smaller calls, each under the threshold

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
