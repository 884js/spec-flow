#!/usr/bin/env bash
set -euo pipefail

# Migrate existing md-based plans to SQLite DB
# Usage: migrate-md-to-db.sh [docs/plans directory]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_SH="$SCRIPT_DIR/db.sh"
PLANS_DIR="${1:-docs/plans}"

if [[ ! -d "$PLANS_DIR" ]]; then
    echo "ERROR: Plans directory not found: $PLANS_DIR" >&2
    exit 1
fi

# Ensure DB exists
"$DB_SH" migrate

echo "Migrating plans from $PLANS_DIR ..."
echo

success=0
failed=0
failed_list=()

for plan_dir in "$PLANS_DIR"/*/; do
    [[ -f "$plan_dir/plan.md" ]] || continue

    feature="$(basename "$plan_dir")"
    echo "--- $feature ---"

    # Parse frontmatter from plan.md
    title=""
    status="draft"
    in_frontmatter=false
    frontmatter_done=false
    body_lines=()

    while IFS= read -r line; do
        if [[ "$frontmatter_done" == false ]]; then
            if [[ "$line" == "---" ]]; then
                if [[ "$in_frontmatter" == true ]]; then
                    frontmatter_done=true
                    continue
                else
                    in_frontmatter=true
                    continue
                fi
            fi
            if [[ "$in_frontmatter" == true ]]; then
                case "$line" in
                    title:*)
                        title="$(echo "$line" | sed 's/^title:[[:space:]]*//' | sed 's/^["'"'"']//' | sed 's/["'"'"']$//')"
                        ;;
                    status:*)
                        status="$(echo "$line" | sed 's/^status:[[:space:]]*//')"
                        ;;
                esac
            fi
        else
            body_lines+=("$line")
        fi
    done < "$plan_dir/plan.md"

    if [[ -z "$title" ]]; then
        title="$feature"
    fi

    # Create plan in DB
    if ! plan_id="$("$DB_SH" create-plan --feature "$feature" --title "$title" 2>/dev/null)"; then
        echo "  SKIP: Plan '$feature' already exists in DB"
        ((failed++)) || true
        failed_list+=("$feature (already exists)")
        echo
        continue
    fi

    # Set status
    if [[ "$status" != "draft" ]]; then
        "$DB_SH" update-plan --feature "$feature" --status "$status" 2>/dev/null || true
    fi

    # Set body (everything after frontmatter)
    body="$(printf '%s\n' "${body_lines[@]}")"
    echo "$body" | "$DB_SH" set-body --feature "$feature" 2>/dev/null

    echo "  Plan created (id=$plan_id, title=$title)"

    # Parse tasks from progress.md
    if [[ -f "$plan_dir/progress.md" ]]; then
        task_count=0
        # Parse progress.md frontmatter for mode
        mode="single"
        situation=""
        next_action=""
        in_fm=false
        fm_done=false
        in_task_table=false
        in_situation=false
        in_next=false

        while IFS= read -r line; do
            # Frontmatter parsing
            if [[ "$fm_done" == false ]]; then
                if [[ "$line" == "---" ]]; then
                    if [[ "$in_fm" == true ]]; then
                        fm_done=true
                        continue
                    else
                        in_fm=true
                        continue
                    fi
                fi
                if [[ "$in_fm" == true ]]; then
                    case "$line" in
                        mode:*) mode="$(echo "$line" | sed 's/^mode:[[:space:]]*//')" ;;
                    esac
                fi
                continue
            fi

            # Detect situation/next sections
            if [[ "$line" == "## 現在の状況" ]]; then
                in_situation=true
                in_next=false
                in_task_table=false
                continue
            elif [[ "$line" == "## 次にやること" ]]; then
                in_next=true
                in_situation=false
                in_task_table=false
                continue
            elif [[ "$line" == "## タスク進捗" ]]; then
                in_task_table=true
                in_situation=false
                in_next=false
                continue
            elif [[ "$line" =~ ^##\  ]]; then
                in_situation=false
                in_next=false
                in_task_table=false
            fi

            if [[ "$in_situation" == true && -n "$line" ]]; then
                situation="$line"
                in_situation=false
            fi
            if [[ "$in_next" == true && -n "$line" ]]; then
                next_action="$line"
                in_next=false
            fi

            # Parse task table rows: | # | タスク | ... | 状態 |
            if [[ "$in_task_table" == true ]]; then
                if [[ "$line" =~ ^\|[[:space:]]*([0-9]+)[[:space:]]*\| ]]; then
                    task_num="${BASH_REMATCH[1]}"
                    # Extract description (2nd column)
                    task_desc="$(echo "$line" | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3}')"
                    # Extract status (last column before trailing |)
                    task_status_char="$(echo "$line" | awk -F'|' '{n=NF-1; gsub(/^[[:space:]]+|[[:space:]]+$/, "", $n); print $n}')"

                    db_status="pending"
                    case "$task_status_char" in
                        "✓") db_status="done" ;;
                        "→") db_status="in_progress" ;;
                        "-") db_status="pending" ;;
                    esac

                    if "$DB_SH" create-task --feature "$feature" --number "$task_num" --desc "$task_desc" >/dev/null 2>&1; then
                        if [[ "$db_status" != "pending" ]]; then
                            "$DB_SH" update-task-status --feature "$feature" --number "$task_num" --status "$db_status" >/dev/null 2>&1
                        fi
                        ((task_count++)) || true
                    fi
                fi
            fi
        done < "$plan_dir/progress.md"

        # Update progress info
        progress_args=(--feature "$feature")
        [[ -n "$mode" ]] && progress_args+=(--mode "$mode")
        [[ -n "$situation" ]] && progress_args+=(--situation "$situation")
        [[ -n "$next_action" ]] && progress_args+=(--next "$next_action")

        if [[ ${#progress_args[@]} -gt 2 ]]; then
            "$DB_SH" update-progress "${progress_args[@]}" >/dev/null 2>&1 || true
        fi

        echo "  Tasks imported: $task_count"
    fi

    # Parse result.md if exists
    if [[ -f "$plan_dir/result.md" ]]; then
        judgment=""
        result_in_fm=false
        result_fm_done=false
        result_body_lines=()

        while IFS= read -r line; do
            if [[ "$result_fm_done" == false ]]; then
                if [[ "$line" == "---" ]]; then
                    if [[ "$result_in_fm" == true ]]; then
                        result_fm_done=true
                        continue
                    else
                        result_in_fm=true
                        continue
                    fi
                fi
                if [[ "$result_in_fm" == true ]]; then
                    case "$line" in
                        judgment:*) judgment="$(echo "$line" | sed 's/^judgment:[[:space:]]*//')" ;;
                    esac
                fi
            else
                result_body_lines+=("$line")
            fi
        done < "$plan_dir/result.md"

        if [[ -n "$judgment" ]]; then
            result_body="$(printf '%s\n' "${result_body_lines[@]}")"
            echo "$result_body" | "$DB_SH" create-result --feature "$feature" --judgment "$judgment" >/dev/null 2>&1
            echo "  Result imported: $judgment"
        fi
    fi

    # Import research files
    for research_file in "$plan_dir"/research-*.md; do
        [[ -f "$research_file" ]] || continue
        research_basename="$(basename "$research_file" .md)"
        # Extract topic from filename: research-YYYY-MM-DD-topic or research-topic
        topic="$(echo "$research_basename" | sed 's/^research-[0-9]*-[0-9]*-[0-9]*-//' | sed 's/^research-//')"
        if [[ -z "$topic" ]]; then
            topic="$research_basename"
        fi

        research_body="$(cat "$research_file")"
        echo "$research_body" | "$DB_SH" create-research --feature "$feature" --topic "$topic" >/dev/null 2>&1
        echo "  Research imported: $topic"
    done

    ((success++)) || true
    echo
done

echo "=== Migration Summary ==="
echo "Success: $success"
echo "Failed: $failed"
if [[ ${#failed_list[@]} -gt 0 ]]; then
    echo "Failed plans:"
    for f in "${failed_list[@]}"; do
        echo "  - $f"
    done
fi
