# Claude Code 本地数据清理指南

> 基于 `~/.claude/` 目录结构分析，整理各部分职责及清理建议。

## 目录总览

| 路径 | 大小 | 类别 | 说明 |
|------|------|------|------|
| `settings.json` | 1KB | **保留** | 全局配置（API Key、权限、hooks 等） |
| `settings.json.bak` | 1KB | **保留** | 配置备份 |
| `CLAUDE.md` | 2KB | **保留** | 全局用户指令（你的工作流偏好） |
| `plugins/` | - | **保留** | 插件注册、市场缓存、已安装插件列表 |
| `projects/` | 56MB | **清理** | 按项目存储的会话记录 + 记忆文件 |
| `sessions/` | 8KB | **清理** | 当前活跃会话的元数据 |
| `history.jsonl` | 456KB | **清理** | 全局对话历史（`/history` 命令的数据源） |
| `tasks/` | 164KB | **清理** | 会话中的 todo/task 持久化 |
| `plans/` | 136KB | **清理** | 会话中的计划文件 |
| `todos/` | 236KB | **清理** | 旧版 todo 数据 |
| `file-history/` | 8MB | **清理** | 文件编辑快照（用于撤销） |
| `backups/` | 300KB | **清理** | 文件修改前的备份 |
| `session-env/` | 180KB | **清理** | 每个会话的环境变量快照 |
| `shell-snapshots/` | 12KB | **清理** | Shell 环境快照 |
| `paste-cache/` | 112KB | **清理** | 粘贴板缓存 |
| `debug/` | 5.2MB | **可清理** | 调试日志 |
| `telemetry/` | 2.4MB | **可清理** | 遥测数据 |
| `statsig/` | 36KB | **可清理** | 功能开关/实验数据 |
| `cache/` | 180KB | **可清理** | 通用缓存 |
| `stats-cache.json` | 3KB | **可清理** | 使用统计缓存 |
| `downloads/` | 140MB | **可清理** | 下载的文件（插件等） |
| `ide/` | 16KB | **自动管理** | IDE 集成锁文件 |
| `security_warnings_state_*.json` | - | **自动管理** | 安全警告确认状态 |

---

## 各部分详解

### 必须保留

#### `settings.json` / `settings.json.bak`
全局配置文件，包含 API 环境变量、权限设置、hooks 配置等。**绝对不能删。**

#### `CLAUDE.md`
你的全局指令文件，定义了 Claude Code 的工作习惯（用 uv、ruff、biome 等）。**不要删。**

#### `plugins/`
插件系统数据，包含：
- `installed_plugins.json` — 已安装插件列表
- `known_marketplaces.json` — 插件市场配置
- `blocklist.json` — 插件黑名单
- `cache/` / `data/` / `marketplaces/` — 插件运行数据

**保留，否则插件需要重新配置。**

---

### 会话与记忆（核心清理目标）

#### `projects/` (56MB) — 最重要的清理目标
按工作目录存储的项目级数据。每个子目录对应一个你用过 Claude Code 的项目路径：
```
projects/
├── -Users-jayncp-Desktop-jayncp-mac-darkjason-music-lib/
│   ├── <uuid>.jsonl          # 该项目的完整对话记录
│   └── <uuid>/               # 对话关联的任务数据
├── -Users-jayncp-Desktop-jayncp-mac-tools-workapace-overseas-IP0325/
│   └── memory/               # 项目级记忆文件（MEMORY.md + 记忆条目）
│       ├── MEMORY.md
│       └── *.md
└── ...共 15 个项目
```
**包含：对话历史、项目记忆、项目级 CLAUDE.md（如有）。** 这是你的"记忆"主要存储位置。

#### `sessions/` (8KB)
当前活跃会话元数据（如 PID 对应的会话 ID）。关闭 Claude Code 后可安全删除。

#### `history.jsonl` (456KB)
全局对话历史索引，`claude --resume` 和 `/history` 命令依赖此文件。

#### `tasks/` (164KB)
会话中的任务列表持久化。每个 UUID 子目录对应一个会话的 task 数据。

#### `plans/` (136KB)
会话中的实现计划文件。

#### `todos/` (236KB)
旧版 todo 数据。

---

### 编辑与缓存（可安全清理）

#### `file-history/` (8MB)
文件编辑历史快照，用于 Claude Code 的撤销功能。清理后失去撤销能力，但不影响正常使用。

#### `backups/` (300KB)
文件修改前的自动备份。

#### `session-env/` (180KB)
每个会话启动时的环境变量快照。

#### `shell-snapshots/` (12KB)
Shell 环境快照。

#### `paste-cache/` (112KB)
粘贴操作的临时缓存。

---

### 日志与遥测（可安全清理）

#### `debug/` (5.2MB)
调试日志文件，排查问题时有用，平时可清理。

#### `telemetry/` (2.4MB)
使用遥测数据。

#### `statsig/` (36KB)
功能开关和 A/B 实验状态。

#### `cache/` (180KB)
通用缓存。

#### `stats-cache.json` (3KB)
使用统计缓存。

#### `downloads/` (140MB)
下载的文件（主要是插件相关）。**注意：如果插件需要这些文件，清理后可能需要重新下载。**

---

## 清理命令

> **执行前请先关闭所有 Claude Code 会话。**

### 方案一：仅清理会话和记忆（推荐）

```bash
# 清理项目级会话历史和记忆
rm -rf ~/.claude/projects/*/

# 清理全局对话历史
rm -f ~/.claude/history.jsonl

# 清理会话数据
rm -rf ~/.claude/sessions/*
rm -rf ~/.claude/tasks/*/
rm -rf ~/.claude/plans/*
rm -rf ~/.claude/todos/*

# 清理编辑历史和缓存
rm -rf ~/.claude/file-history/*
rm -rf ~/.claude/backups/*
rm -rf ~/.claude/session-env/*
rm -rf ~/.claude/shell-snapshots/*
rm -rf ~/.claude/paste-cache/*

# 清理安全警告状态
rm -f ~/.claude/security_warnings_state_*.json
```

### 方案二：深度清理（加上日志和缓存）

```bash
# 先执行方案一的所有命令，然后：

# 清理调试日志
rm -rf ~/.claude/debug/*

# 清理遥测和统计
rm -rf ~/.claude/telemetry/*
rm -rf ~/.claude/statsig/*
rm -f ~/.claude/stats-cache.json
rm -rf ~/.claude/cache/*

# 清理下载缓存（140MB，插件可能需要重新下载）
rm -rf ~/.claude/downloads/*
```

### 方案三：一键脚本

```bash
#!/bin/bash
# clean_claude_memory.sh — 清理 Claude Code 会话和记忆，保留配置和插件

CLAUDE_DIR="$HOME/.claude"

echo "=== Claude Code 清理工具 ==="
echo "将清理: 会话记录、项目记忆、编辑历史、日志缓存"
echo "将保留: settings.json, CLAUDE.md, plugins/"
echo ""
read -p "确认清理？(y/N) " confirm
[[ "$confirm" != "y" && "$confirm" != "Y" ]] && echo "已取消" && exit 0

# 会话和记忆
rm -rf "$CLAUDE_DIR"/projects/*/
rm -f  "$CLAUDE_DIR"/history.jsonl
rm -rf "$CLAUDE_DIR"/sessions/*
rm -rf "$CLAUDE_DIR"/tasks/*/
rm -rf "$CLAUDE_DIR"/plans/*
rm -rf "$CLAUDE_DIR"/todos/*

# 编辑历史
rm -rf "$CLAUDE_DIR"/file-history/*
rm -rf "$CLAUDE_DIR"/backups/*
rm -rf "$CLAUDE_DIR"/session-env/*
rm -rf "$CLAUDE_DIR"/shell-snapshots/*
rm -rf "$CLAUDE_DIR"/paste-cache/*

# 日志和缓存
rm -rf "$CLAUDE_DIR"/debug/*
rm -rf "$CLAUDE_DIR"/telemetry/*
rm -rf "$CLAUDE_DIR"/statsig/*
rm -rf "$CLAUDE_DIR"/cache/*
rm -f  "$CLAUDE_DIR"/stats-cache.json
rm -f  "$CLAUDE_DIR"/security_warnings_state_*.json

# 可选：下载缓存（取消注释启用）
# rm -rf "$CLAUDE_DIR"/downloads/*

echo "清理完成！保留了 settings.json, CLAUDE.md, plugins/"
```

---

## 清理后的效果

| 功能 | 影响 |
|------|------|
| `/history` 恢复对话 | 不可用（历史已清除） |
| 项目级记忆 | 重置（Claude 不再记得之前的偏好） |
| 文件撤销 | 不可用（编辑快照已清除） |
| 插件 | 正常工作 |
| 配置/hooks | 正常工作 |
| 全局指令 CLAUDE.md | 正常工作 |
