# Codex Import Guide

This repository contains a local Codex plugin at:

```text
plugins/knowledge-tool
```

The plugin is designed to be committed and shared. It contains only workflow instructions, helper scripts, and documentation. User learning folders are created outside the plugin source.

## Install Locally

For a personal Codex installation, add this plugin to a local marketplace or copy it into your existing plugin marketplace workflow. The plugin manifest is:

```text
plugins/knowledge-tool/.codex-plugin/plugin.json
```

After installing or reinstalling a local plugin, start a new Codex task so the new skill metadata is loaded.

## Trigger

Use the plugin by mentioning:

```text
@KnowledgeTool Android Compose
@KnowledgeTool 学习项目 C:\Ai\Project\App
@KnowledgeTool 继续Android Compose
```

## Configuration

KnowledgeTool reads user configuration from:

```text
~/.knowledge-tool/config.json
```

Create a default config with:

```text
python plugins/knowledge-tool/scripts/knowledge_tool.py config --init
```

Example:

```json
{
  "default_learning_root": "D:\\Learning",
  "recent_limit": 10,
  "assessment_difficulty": "adaptive",
  "language": "zh-CN",
  "project_scan_max_files": 200
}
```

If `default_learning_root` is null or missing, the default root is:

```text
<current workspace>/.knowledge-tool/learning
```

## Data Separation

Do not store generated learning content in `plugins/knowledge-tool`. The helper script refuses to use the plugin source directory as a learning root. Learning content belongs in a configured external root, with one directory per topic.
