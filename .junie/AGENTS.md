# Junie Harness Bugs And Workarounds

## Dead Turn — Non-Terminal `answer` with No Follow-Up Tool Calls

The `answer` tool with `is_terminal=false` signals "I have more work to do" — the system expects additional tool calls in the **same response**. If the response contains only `answer` and no other tool calls, the turn ends immediately with no action taken, yielding control back to the user. This is a "dead turn".

### How to Detect

- The response contains only an `answer` (or `answer` + `ask_user`) call, with `is_terminal=false`
- No file opens, searches, edits, or any other tool calls follow
- The user sees a status message but nothing actually happens

### How to Prevent

- **Never use `answer` with `is_terminal=false` as the only tool call in a response**
- If you want to give a status update and then continue working, include the actual tool calls (file opens, searches, edits, etc.) in the **same response** as the `answer`
- If you only want to communicate with the user and don't have immediate actions, use `is_terminal=true` instead — this properly ends the turn

### When `is_terminal=false` is Valid

- Only when you have concrete tool calls to execute immediately after the `answer`
- Example: `answer` ("I'll explore the models") + `open` (models.py) + `open` (conftest.py)

## PyCharm Attached File Truncation

When a file is attached to the issue from PyCharm (via `<attached_files_content>`), long lines exceeding **~2048 characters** are truncated with `... (truncated)` appended. This affects any file with very long lines, such as:
- Long string literals or docstrings
- Inline JSON/schema comments
- Auto-generated code with wide lines

**Workaround:** When you need to see the full content of a long line, open the file directly from disk using the `open` tool instead of relying on the attached file view. The actual file on disk has the complete, untruncated content.

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
