#!/usr/bin/env bash
# 开启 Codex.app 的 fast 功能 (macOS)
#
# 原理:
#   1) 解压 app.asar 到 app/ 目录,让 electron 优先加载源码而非 asar
#   2) 将 app.asar 重命名为 app.asar1 作为原始备份
#   3) 在 general-settings-*.js 中,通过特征匹配定位 fast-mode 判定函数,
#      将该函数结尾的 `,r}` 改为 `,true}`,使其恒返回 true
#   4) 关闭几个 electron fuses (尤其是 asar 完整性校验和仅从 asar 加载)
#   5) ad-hoc 重签名,避免 macOS 拒绝加载修改过的 app
#   6) 全部成功 -> 删除备份 app.asar1
#      中途失败 -> 自动回滚: 还原 app.asar + 删除 app/ + 重签名
#
# 用法:
#   sudo scripts/local/codex_fast.sh
#
# 环境变量:
#   CODEX_APP_PATH=/path/to/Codex.app   自定义 app 路径 (默认 /Applications/Codex.app)

set -euo pipefail

PATH="${PATH}:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin"

APP_PATH="${CODEX_APP_PATH:-/Applications/Codex.app}"
RESOURCES_DIR="${APP_PATH}/Contents/Resources"
ASAR_PATH="${RESOURCES_DIR}/app.asar"
ASAR_RENAMED_PATH="${RESOURCES_DIR}/app.asar1"
APP_DIR="${RESOURCES_DIR}/app"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m ✓\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[1;33mWarn:\033[0m %s\n' "$*" >&2; }

# ---------- 状态跟踪 (供 cleanup 判断回滚范围) ----------
EXTRACTED=0   # app/ 是本次脚本解压出来的
RENAMED=0     # app.asar 是本次脚本改名的
SUCCESS=0     # 全部步骤成功完成

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM  # 防止清理过程中再次触发

  if [[ $SUCCESS -eq 1 ]]; then
    # 成功路径: 清理备份
    if [[ -f "$ASAR_RENAMED_PATH" ]]; then
      log "清理备份 $(basename "$ASAR_RENAMED_PATH")"
      if ! rm -f "$ASAR_RENAMED_PATH"; then
        warn "备份清理失败,可手动删除: $ASAR_RENAMED_PATH"
      fi
    fi
    exit 0
  fi

  # 失败路径: 只回滚本次脚本做过的变更
  if [[ $EXTRACTED -eq 0 && $RENAMED -eq 0 ]]; then
    # 本次啥都没改,直接退出,不干扰已有状态
    exit $exit_code
  fi

  err "脚本失败,正在回滚..."
  local restore_failed=0

  # 1) 还原 app.asar
  if [[ $RENAMED -eq 1 && -f "$ASAR_RENAMED_PATH" ]]; then
    if [[ -e "$ASAR_PATH" ]]; then
      # 极端情况: 原位置已有同名文件 (不应该发生)
      warn "$ASAR_PATH 已存在,跳过 mv 回滚"
    elif mv "$ASAR_RENAMED_PATH" "$ASAR_PATH"; then
      log "已还原 app.asar"
    else
      restore_failed=1
      err "还原 app.asar 失败,请手动: mv \"$ASAR_RENAMED_PATH\" \"$ASAR_PATH\""
    fi
  fi

  # 2) 清理解压出来的 app/ 目录
  if [[ $EXTRACTED -eq 1 && -d "$APP_DIR" ]]; then
    if rm -rf "$APP_DIR"; then
      log "已清理 app/ 目录"
    else
      restore_failed=1
      err "清理 app/ 失败,请手动: rm -rf \"$APP_DIR\""
    fi
  fi

  # 3) 回滚后重签 (即便只动过 mv,签名布局也已失效)
  if [[ $restore_failed -eq 0 ]]; then
    if codesign --force --deep --sign - "$APP_PATH" 2>/dev/null; then
      log "已重签名"
    else
      warn "重签名失败,app 可能无法打开,请手动: codesign --force --deep --sign - \"$APP_PATH\""
    fi
  fi

  exit $exit_code
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# ---------- 0. 依赖与路径检查 ----------
for cmd in npx codesign perl grep find mv; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    err "缺少命令: $cmd"; exit 1
  fi
done

[[ -d "$APP_PATH" ]] || { err "Codex.app 不存在: $APP_PATH"; exit 1; }

if [[ ! -w "$RESOURCES_DIR" ]]; then
  err "$RESOURCES_DIR 无写权限,请用 sudo 运行本脚本"
  exit 1
fi

# ---------- 1. 解压 app.asar 并重命名 ----------
if [[ -d "$APP_DIR" ]]; then
  log "检测到 $APP_DIR 已存在,跳过解压"
else
  [[ -f "$ASAR_PATH" ]] || { err "未找到 $ASAR_PATH"; exit 1; }
  log "解压 app.asar -> app/"
  npx --yes @electron/asar extract "$ASAR_PATH" "$APP_DIR"
  EXTRACTED=1
  log "重命名 app.asar -> app.asar1"
  mv "$ASAR_PATH" "$ASAR_RENAMED_PATH"
  RENAMED=1
fi

# ---------- 2. 定位目标 JS 文件 (pattern 特征匹配,不依赖函数名) ----------
log "查找 fast-mode 判定所在的 js 文件"

target_file=""
# 优先在 general-settings-*.js 里找
while IFS= read -r f; do
  if grep -q 'statsig_default_enable_features' "$f" 2>/dev/null \
     && grep -q 'fast_mode===!0&&' "$f" 2>/dev/null; then
    target_file="$f"; break
  fi
done < <(find "$APP_DIR" -type f -name 'general-settings-*.js' 2>/dev/null)

# fallback: 不限文件名,只靠内容特征
if [[ -z "$target_file" ]]; then
  while IFS= read -r f; do
    if grep -q 'statsig_default_enable_features' "$f" 2>/dev/null \
       && grep -q 'fast_mode===!0&&' "$f" 2>/dev/null \
       && grep -q 'n?\.fast_mode,e\[2\]=r' "$f" 2>/dev/null; then
      target_file="$f"; break
    fi
  done < <(find "$APP_DIR" -type f -name '*.js' 2>/dev/null)
fi

[[ -n "$target_file" ]] || { err "未找到含 fast-mode 判定函数的 js 文件"; exit 1; }
ok "目标文件: ${target_file#$APP_DIR/}"

# ---------- 3. 打补丁: 将 ...e[2]=r):r=e[2],r} 改为 ...e[2]=r):r=e[2],true} ----------
if grep -qF 'e[2]=r):r=e[2],true}' "$target_file"; then
  log "已打过补丁,跳过修改"
else
  log "打补丁 (将 fast-mode 判定函数返回值改为 true)"

  # 匹配模式 (使用 /x 允许换行):
  #   fast_mode===!0 && <identifier>(t),
  #   e[0]=t, e[1]=n?.fast_mode, e[2]=r) :
  #   r=e[2], r }
  # 保留到最后一个逗号, 把末尾的 `r}` 替换成 `true}`
  perl -0777 -i -pe '
    s/
      (fast_mode===!0&&[A-Za-z_\$][A-Za-z0-9_\$]*\(t\)
       ,e\[0\]=t,e\[1\]=n\?\.fast_mode,e\[2\]=r\)
       :r=e\[2\],)
      r\}
    /${1}true}/gx
  ' "$target_file"

  if ! grep -qF 'e[2]=r):r=e[2],true}' "$target_file"; then
    err "补丁模式未匹配,函数结构可能已变化,请手动检查: $target_file"
    exit 1
  fi
  ok "补丁应用成功"
fi

# ---------- 4. 关闭 electron fuses ----------
log "关闭 electron fuses"
npx --yes @electron/fuses write --app "$APP_PATH" \
  GrantFileProtocolExtraPrivileges=off \
  EnableCookieEncryption=off \
  OnlyLoadAppFromAsar=off \
  EnableEmbeddedAsarIntegrityValidation=off

# ---------- 5. ad-hoc 重签名 ----------
log "ad-hoc 重签名 Codex.app"
codesign --force --deep --sign - "$APP_PATH"

# 全部成功,标记后让 trap 去做清理
SUCCESS=1
printf '\n\033[1;32m✅ 完成!\033[0m 请重新打开 Codex.app,在设置页即可看到 fast 选项\n'
