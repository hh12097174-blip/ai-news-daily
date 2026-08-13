#!/usr/bin/env bash
# danger-guard.sh — pre_tool_call hook
# Blocks dangerous terminal commands before execution (defense in depth,
# second layer behind the Docker backend).
# Hermes pipes the tool-call JSON into stdin; reply with {"action":"allow"}
# or {"action":"block","reason":"..."}.

PAYLOAD=$(cat)

TOOL_NAME=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name',''))" 2>/dev/null)

# Only guard the terminal tool
if [ "$TOOL_NAME" != "terminal" ]; then
  printf '{"action":"allow"}\n'
  exit 0
fi

CMD=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('parameters',{}).get('command',''))" 2>/dev/null)

# Destructive / risky command blacklist
if echo "$CMD" | grep -qiE "rm\s+-rf\s+[/*]|mkfs\.|shutdown|reboot|dd\s+if=.*of=/dev/|>?\s*/dev/sd|chmod\s+-R\s+777\s+/|DROP\s+TABLE|DROP\s+DATABASE|git\s+push\s+--force|curl[^\n]*\|\s*(sh|bash|sudo)"; then
  printf '{"action":"block","reason":"Dangerous command blocked by danger-guard hook"}\n'
  exit 0
fi

# Block attempts to exfiltrate credentials
if echo "$CMD" | grep -qiE "cat\s+~?/\.env|cat\s+.*(credentials|\.pem|id_rsa|auth\.json)|API_KEY|SECRET.*echo|curl.*\$\{?[A-Z_]*KEY"; then
  printf '{"action":"block","reason":"Credential exfiltration attempt blocked by danger-guard hook"}\n'
  exit 0
fi

printf '{"action":"allow"}\n'
