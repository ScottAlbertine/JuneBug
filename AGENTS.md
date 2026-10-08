# JuneBug — Agent Notes

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
