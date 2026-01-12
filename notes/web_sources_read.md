# Web source reads

Commands used to confirm access and pull page titles:

```
curl -L -s https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | rg -n "<title>" -m1
curl -L -s https://www.anthropic.com/news/claude-opus-4-5 | rg -n "<title>" -m1
curl -L -s https://platform.claude.com/docs/en/build-with-claude/effort | rg -n "<title>" -m1
curl -L -s https://www.anthropic.com/engineering/advanced-tool-use | rg -n "<title>" -m1
curl -L -s https://platform.claude.com/docs/en/build-with-claude/context-editing#client-side-compaction-sdk | rg -n "<title>" -m1
curl -L -s https://platform.claude.com/docs/en/build-with-claude/context-editing#using-with-the-memory-tool | rg -n "<title>" -m1
curl -L -s https://www.anthropic.com/engineering/code-execution-with-mcp | rg -n "<title>" -m1
curl -L -s https://platform.claude.com/docs/en/agent-sdk/overview#agent-sdk-vs-claude-code-cli | rg -n "<title>" -m1
curl -L -s https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | rg -n "<title>" -m1
```

PDF retrieval check:

```
curl -L -s -o /tmp/claude_opus_4_5_system_card.pdf https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf
python - <<'PY'
from pathlib import Path
path = Path('/tmp/claude_opus_4_5_system_card.pdf')
print(path.exists())
if path.exists():
    with path.open('rb') as f:
        print(f.read(8))
PY
```
