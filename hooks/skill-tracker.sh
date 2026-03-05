#!/bin/bash
# skill-tracker.sh - スキル実行状態を追跡し、コンテキスト喪失を防ぐ
#
# hook_event_name で分岐:
#   PreToolUse (Skill)   → スキル名を /tmp/claude-skill-state/{session_id}.json に保存
#   UserPromptSubmit     → 保存済みのスキル情報を stdout に出力（Claudeに注入）
#   SessionEnd           → stateファイルを削除

STATE_DIR="/tmp/claude-skill-state"
INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty')

if [ -z "$SESSION_ID" ]; then
  exit 0
fi

STATE_FILE="$STATE_DIR/$SESSION_ID.json"

case "$EVENT" in
  PreToolUse)
    SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')
    if [ -z "$SKILL_NAME" ]; then
      exit 0
    fi

    PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty')
    PROJECT_NAME=$(basename "$PROJECT_DIR")
    STARTED_AT=$(date '+%H:%M')

    mkdir -p "$STATE_DIR"
    jq -n \
      --arg skill "$SKILL_NAME" \
      --arg started_at "$STARTED_AT" \
      --arg project_dir "$PROJECT_DIR" \
      --arg project_name "$PROJECT_NAME" \
      '{skill: $skill, started_at: $started_at, project_dir: $project_dir, project_name: $project_name}' \
      > "$STATE_FILE"
    ;;

  UserPromptSubmit)
    if [ -f "$STATE_FILE" ]; then
      SKILL=$(jq -r '.skill' "$STATE_FILE")
      PROJECT=$(jq -r '.project_name' "$STATE_FILE")
      STARTED=$(jq -r '.started_at' "$STATE_FILE")
      echo "Active Skill: $SKILL ($PROJECT) since $STARTED"
    fi
    ;;

  SessionEnd)
    rm -f "$STATE_FILE"
    ;;
esac

exit 0
