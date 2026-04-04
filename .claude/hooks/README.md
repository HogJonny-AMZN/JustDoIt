# .claude/hooks/

Claude Code hooks for JustDoIt.

## post-edit-test.sh

Runs the test suite after edits to `justdoit/` or `tests/`.

Configure in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-edit-test.sh $CLAUDE_TOOL_INPUT_PATH"
          }
        ]
      }
    ]
  }
}
```

## Philosophy

Hooks encode the things that must always happen — so Claude doesn't have to remember.
Formatters, test runners, and guardrails belong here.
