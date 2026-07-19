# KnowledgeTool

KnowledgeTool is a local Codex plugin for structured, resumable learning.

Plugin source lives in:

```text
plugins/knowledge-tool
```

User learning content is intentionally separate from the plugin. By default, generated study folders are written to:

```text
<current workspace>/.knowledge-tool/learning
```

You can configure another root in:

```text
~/.knowledge-tool/config.json
```

See:

- `plugins/knowledge-tool/docs/CODEX_IMPORT.md`
- `plugins/knowledge-tool/docs/USER_GUIDE.md`

Common prompts:

```text
@KnowledgeTool Android Compose
@KnowledgeTool 学习项目 C:\Ai\Project\App
@KnowledgeTool 继续Android Compose
```
