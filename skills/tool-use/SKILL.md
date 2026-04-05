---
name: tool-use
description: Efficient shell tool usage patterns for benchmark tasks
tools: [bash]
---

# Tool Use

## File operations

- **Read before edit.** Always `cat` a file before modifying it.
- **Use `sed -i` for targeted replacements.** For complex edits, write the whole file.
- **Check file existence** with `[ -f path ]` before reading.
- **Use `tee`** when you need to both see output and write to a file.

## Environment detection

```bash
# Package manager
if command -v apt-get &>/dev/null; then
  apt-get update && apt-get install -y PACKAGE
elif command -v apk &>/dev/null; then
  apk add --no-cache PACKAGE
elif command -v yum &>/dev/null; then
  yum install -y PACKAGE
fi

# Python
python3 --version 2>/dev/null || python --version 2>/dev/null

# Node
node --version 2>/dev/null
```

## Networking

- Use `curl -fsSL` for downloads (fail silently on HTTP errors, follow redirects)
- Check connectivity with `curl -s -o /dev/null -w '%{http_code}' URL`
- Use `wget` as fallback if curl is not available

## Process management

- Use `&&` to chain dependent commands
- Use `||` only for intentional fallbacks, not to hide errors
- Background processes: `command &` then `wait` when needed
