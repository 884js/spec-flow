#!/usr/bin/env bash
set -euo pipefail

# spec-flow DB helper — CLI interface to ~/.claude/spec-flow.db
# Usage: db.sh <subcommand> [options]

DB_PATH="$HOME/.claude/spec-flow.db"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MIGRATIONS_DIR="$SCRIPT_DIR/../migrations"

# ─── Helpers ───

die() { echo "ERROR: $*" >&2; exit 1; }

sql_noheader() {
    sqlite3 "$DB_PATH" <<EOSQL
.separator "	"
.headers off
.output /dev/null
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
.output stdout
$*
EOSQL
}

ensure_db() {
    if [[ ! -f "$DB_PATH" ]]; then
        do_migrate
    fi
}

# Resolve project_id from --project option or auto-detect from cwd
resolve_project_id() {
    local project_name="${OPT_PROJECT:-}"
    if [[ -z "$project_name" ]]; then
        project_name="$(basename "$(pwd)")"
    fi

    local pid
    pid="$(sql_noheader "SELECT id FROM projects WHERE name = '$project_name';" 2>/dev/null || true)"

    if [[ -z "$pid" ]]; then
        # Auto-register
        local project_path
        if [[ -n "${OPT_PROJECT:-}" ]]; then
            die "Project '$project_name' not found. Register it first with: db.sh register-project --name $project_name --path /path/to/project"
        fi
        project_path="$(pwd)"
        pid="$(sql_noheader "INSERT INTO projects (name, path) VALUES ('$project_name', '$project_path') RETURNING id;")"
        echo "Auto-registered project: $project_name ($project_path)" >&2
    fi

    echo "$pid"
}

# Resolve plan_id from feature_name + project_id
resolve_plan_id() {
    local feature="$1"
    local project_id="$2"
    local pid
    pid="$(sql_noheader "SELECT id FROM plans WHERE feature_name = '$feature' AND project_id = $project_id;")"
    if [[ -z "$pid" ]]; then
        die "Plan '$feature' not found in this project"
    fi
    echo "$pid"
}

# Parse common options (--project, --feature, etc.)
OPT_PROJECT=""
OPT_FEATURE=""
OPT_TITLE=""
OPT_STATUS=""
OPT_NUMBER=""
OPT_DESC=""
OPT_JUDGMENT=""
OPT_TOPIC=""
OPT_TYPE=""
OPT_SOURCE=""
OPT_TARGET=""
OPT_RELATION_DESC=""
OPT_ALL=false
OPT_ID=""
OPT_MODE=""
OPT_SITUATION=""
OPT_NEXT=""
OPT_PR_GROUPS=""
OPT_REPOS=""
OPT_DOCS=""
OPT_NAME=""
OPT_PATH=""

parse_opts() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --project)   OPT_PROJECT="$2"; shift 2 ;;
            --feature)   OPT_FEATURE="$2"; shift 2 ;;
            --title)     OPT_TITLE="$2"; shift 2 ;;
            --status)    OPT_STATUS="$2"; shift 2 ;;
            --number)    OPT_NUMBER="$2"; shift 2 ;;
            --desc)      OPT_DESC="$2"; shift 2 ;;
            --judgment)  OPT_JUDGMENT="$2"; shift 2 ;;
            --topic)     OPT_TOPIC="$2"; shift 2 ;;
            --type)      OPT_TYPE="$2"; shift 2 ;;
            --source)    OPT_SOURCE="$2"; shift 2 ;;
            --target)    OPT_TARGET="$2"; shift 2 ;;
            --relation-desc) OPT_RELATION_DESC="$2"; shift 2 ;;
            --all)       OPT_ALL=true; shift ;;
            --id)        OPT_ID="$2"; shift 2 ;;
            --mode)      OPT_MODE="$2"; shift 2 ;;
            --situation) OPT_SITUATION="$2"; shift 2 ;;
            --next)      OPT_NEXT="$2"; shift 2 ;;
            --pr-groups) OPT_PR_GROUPS="$2"; shift 2 ;;
            --repos)     OPT_REPOS="$2"; shift 2 ;;
            --docs)      OPT_DOCS="$2"; shift 2 ;;
            --name)      OPT_NAME="$2"; shift 2 ;;
            --path)      OPT_PATH="$2"; shift 2 ;;
            *)           die "Unknown option: $1" ;;
        esac
    done
}

# Validate feature_name format: [a-z0-9-] only
validate_feature_name() {
    local name="$1"
    if [[ ! "$name" =~ ^[a-z0-9-]+$ ]]; then
        die "Invalid feature name '$name': only lowercase letters, digits, and hyphens are allowed"
    fi
}

# ─── Subcommands ───

do_migrate() {
    mkdir -p "$(dirname "$DB_PATH")"
    # Set WAL mode (persistent, only needed once)
    sqlite3 "$DB_PATH" "PRAGMA journal_mode = WAL;" >/dev/null 2>&1
    for f in "$MIGRATIONS_DIR"/0*.sql; do
        [[ -f "$f" ]] || continue
        local ver
        ver="$(basename "$f" | sed 's/^0*\([0-9]*\)_.*/\1/')"
        local applied
        applied="$(sqlite3 "$DB_PATH" "SELECT 1 FROM schema_version WHERE version = $ver;" 2>/dev/null || true)"
        if [[ -z "$applied" ]]; then
            sqlite3 "$DB_PATH" < "$f"
            echo "Applied migration: $(basename "$f")"
        fi
    done
    echo "Database is up to date."
}

do_register_project() {
    [[ -n "$OPT_NAME" ]] || die "--name is required"
    [[ -n "$OPT_PATH" ]] || die "--path is required"

    local existing
    existing="$(sql_noheader "SELECT path FROM projects WHERE name = '$OPT_NAME';" 2>/dev/null || true)"
    if [[ -n "$existing" ]]; then
        die "Project '$OPT_NAME' already exists at: $existing"
    fi

    local pid
    pid="$(sql_noheader "INSERT INTO projects (name, path) VALUES ('$OPT_NAME', '$OPT_PATH') RETURNING id;")"
    echo "$pid"
}

do_list_projects() {
    echo -e "id\tname\tpath\tcreated_at"
    sql_noheader "SELECT id, name, path, created_at FROM projects ORDER BY name;"
}

do_create_plan() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"
    [[ -n "$OPT_TITLE" ]] || die "--title is required"
    validate_feature_name "$OPT_FEATURE"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local pid
    pid="$(sql_noheader "INSERT INTO plans (project_id, feature_name, title) VALUES ($project_id, '$OPT_FEATURE', '$(echo "$OPT_TITLE" | sed "s/'/''/g")') RETURNING id;" 2>/dev/null)" \
        || die "Plan '$OPT_FEATURE' already exists in this project"
    echo "$pid"
}

do_get_plan() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    echo -e "id\tfeature_name\ttitle\tstatus\tmode\tcreated_at\tupdated_at"
    sql_noheader "SELECT id, feature_name, title, status, mode, created_at, updated_at FROM plans WHERE feature_name = '$OPT_FEATURE' AND project_id = $project_id;"
}

do_list_plans() {
    ensure_db

    local where_clause=""
    if [[ "$OPT_ALL" == true ]]; then
        where_clause=""
    else
        local project_id
        project_id="$(resolve_project_id)"
        where_clause="WHERE p.project_id = $project_id"
    fi

    echo -e "feature_name\ttitle\tstatus"
    sql_noheader "
        SELECT
            p.feature_name,
            p.title,
            CASE
                WHEN r.judgment = 'NEEDS_FIX' THEN '要修正'
                WHEN r.judgment = 'PARTIAL' THEN '部分合格'
                WHEN r.judgment = 'PASS' THEN '検証済み'
                WHEN COUNT(CASE WHEN t.status = 'done' THEN 1 END) = COUNT(t.id) AND COUNT(t.id) > 0 THEN '実装完了'
                WHEN COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) > 0 THEN '実装中'
                WHEN COUNT(t.id) > 0 THEN '未着手'
                ELSE '仕様作成済み'
            END AS computed_status
        FROM plans p
        LEFT JOIN tasks t ON t.plan_id = p.id
        LEFT JOIN (
            SELECT plan_id, judgment,
                ROW_NUMBER() OVER (PARTITION BY plan_id ORDER BY created_at DESC) as rn
            FROM results
        ) r ON r.plan_id = p.id AND r.rn = 1
        $where_clause
        GROUP BY p.id
        ORDER BY p.feature_name;
    "
}

do_update_plan() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"
    [[ -n "$OPT_STATUS" ]] || die "--status is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    sql_noheader "UPDATE plans SET status = '$OPT_STATUS', updated_at = datetime('now') WHERE feature_name = '$OPT_FEATURE' AND project_id = $project_id;"
    echo "Updated plan '$OPT_FEATURE' status to '$OPT_STATUS'"
}

do_get_body() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local encoded
    encoded="$(sql_noheader "SELECT body FROM plans WHERE feature_name = '$OPT_FEATURE' AND project_id = $project_id;")"
    if [[ -z "$encoded" ]]; then
        die "Plan '$OPT_FEATURE' not found or has no body"
    fi
    echo "$encoded" | base64 -d
}

do_set_body() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local encoded
    encoded="$(base64)"
    sql_noheader "UPDATE plans SET body = '$encoded', updated_at = datetime('now') WHERE feature_name = '$OPT_FEATURE' AND project_id = $project_id;"
    echo "Body set for plan '$OPT_FEATURE'"
}

do_create_task() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"
    [[ -n "$OPT_NUMBER" ]] || die "--number is required"
    [[ -n "$OPT_DESC" ]] || die "--desc is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    local tid
    tid="$(sql_noheader "INSERT INTO tasks (plan_id, task_number, description) VALUES ($plan_id, $OPT_NUMBER, '$(echo "$OPT_DESC" | sed "s/'/''/g")') RETURNING id;" 2>/dev/null)" \
        || die "Task #$OPT_NUMBER already exists for plan '$OPT_FEATURE'"
    echo "$tid"
}

do_update_task_status() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"
    [[ -n "$OPT_NUMBER" ]] || die "--number is required"
    [[ -n "$OPT_STATUS" ]] || die "--status is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    sql_noheader "UPDATE tasks SET status = '$OPT_STATUS' WHERE plan_id = $plan_id AND task_number = $OPT_NUMBER;"
    echo "Task #$OPT_NUMBER status updated to '$OPT_STATUS'"
}

do_delete_task() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"
    [[ -n "$OPT_NUMBER" ]] || die "--number is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    local before after
    before="$(sql_noheader "SELECT COUNT(*) FROM tasks WHERE plan_id = $plan_id AND task_number = $OPT_NUMBER;")"
    if [[ "$before" -eq 0 ]]; then
        die "Task #$OPT_NUMBER not found for plan '$OPT_FEATURE'"
    fi
    sql_noheader "DELETE FROM tasks WHERE plan_id = $plan_id AND task_number = $OPT_NUMBER;"
    echo "Task #$OPT_NUMBER deleted"
}

do_list_tasks() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    echo -e "task_number\tdescription\tstatus"
    sql_noheader "SELECT task_number, description, status FROM tasks WHERE plan_id = $plan_id ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'in_progress' THEN 1 WHEN 'done' THEN 2 ELSE 3 END, task_number;"
}

do_create_result() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"
    [[ -n "$OPT_JUDGMENT" ]] || die "--judgment is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    local encoded=""
    if ! [ -t 0 ]; then
        encoded="$(base64)"
    fi

    local rid
    rid="$(sql_noheader "INSERT INTO results (plan_id, judgment, body) VALUES ($plan_id, '$OPT_JUDGMENT', '$encoded') RETURNING id;")"
    echo "$rid"
}

do_get_result() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    local row
    row="$(sql_noheader "SELECT judgment, body FROM results WHERE plan_id = $plan_id ORDER BY created_at DESC LIMIT 1;")"
    if [[ -z "$row" ]]; then
        die "No results found for plan '$OPT_FEATURE'"
    fi

    local judgment body
    judgment="$(echo "$row" | cut -f1)"
    body="$(echo "$row" | cut -f2)"

    echo "judgment: $judgment"
    if [[ -n "$body" ]]; then
        echo "---"
        echo "$body" | base64 -d
    fi
}

do_create_research() {
    [[ -n "$OPT_TOPIC" ]] || die "--topic is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local plan_id="NULL"
    if [[ -n "$OPT_FEATURE" ]]; then
        plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"
    fi

    local encoded=""
    if ! [ -t 0 ]; then
        encoded="$(base64)"
    fi

    local rtype="NULL"
    if [[ -n "$OPT_TYPE" ]]; then
        rtype="'$OPT_TYPE'"
    fi

    local rid
    rid="$(sql_noheader "INSERT INTO research (project_id, plan_id, topic, research_type, body) VALUES ($project_id, $plan_id, '$(echo "$OPT_TOPIC" | sed "s/'/''/g")', $rtype, '$encoded') RETURNING id;")"
    echo "$rid"
}

do_list_research() {
    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local where="project_id = $project_id"
    if [[ -n "$OPT_FEATURE" ]]; then
        local plan_id
        plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"
        where="$where AND plan_id = $plan_id"
    fi

    echo -e "id\ttopic\tresearch_type\tcreated_at"
    sql_noheader "SELECT id, topic, research_type, created_at FROM research WHERE $where ORDER BY created_at DESC;"
}

do_get_research_body() {
    [[ -n "$OPT_ID" ]] || die "--id is required"

    ensure_db

    local encoded
    encoded="$(sql_noheader "SELECT body FROM research WHERE id = $OPT_ID;")"
    if [[ -z "$encoded" ]]; then
        die "Research #$OPT_ID not found"
    fi
    echo "$encoded" | base64 -d
}

do_create_debug() {
    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local plan_id="NULL"
    if [[ -n "$OPT_FEATURE" ]]; then
        plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"
    fi

    local encoded=""
    if ! [ -t 0 ]; then
        encoded="$(base64)"
    fi

    local did
    did="$(sql_noheader "INSERT INTO debug_logs (project_id, plan_id, body) VALUES ($project_id, $plan_id, '$encoded') RETURNING id;")"
    echo "$did"
}

do_list_debug() {
    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local where="project_id = $project_id"
    if [[ -n "$OPT_FEATURE" ]]; then
        local plan_id
        plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"
        where="$where AND plan_id = $plan_id"
    fi

    echo -e "id\tplan_id\tcreated_at"
    sql_noheader "SELECT id, plan_id, created_at FROM debug_logs WHERE $where ORDER BY created_at DESC;"
}

do_add_relation() {
    [[ -n "$OPT_SOURCE" ]] || die "--source is required"
    [[ -n "$OPT_TARGET" ]] || die "--target is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local source_id target_id
    source_id="$(resolve_plan_id "$OPT_SOURCE" "$project_id")"
    target_id="$(resolve_plan_id "$OPT_TARGET" "$project_id")"

    local rtype="${OPT_TYPE:-related}"
    local rdesc="NULL"
    if [[ -n "$OPT_RELATION_DESC" ]]; then
        rdesc="'$(echo "$OPT_RELATION_DESC" | sed "s/'/''/g")'"
    fi

    local rid
    rid="$(sql_noheader "INSERT INTO plan_relations (source_plan_id, target_plan_id, relation_type, description) VALUES ($source_id, $target_id, '$rtype', $rdesc) RETURNING id;" 2>/dev/null)" \
        || die "Relation already exists between '$OPT_SOURCE' and '$OPT_TARGET'"
    echo "$rid"
}

do_get_relations() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    echo -e "direction\tfeature_name\trelation_type\tdescription"
    sql_noheader "
        SELECT 'outgoing', p.feature_name, r.relation_type, COALESCE(r.description, '')
        FROM plan_relations r
        JOIN plans p ON p.id = r.target_plan_id
        WHERE r.source_plan_id = $plan_id
        UNION ALL
        SELECT 'incoming', p.feature_name, r.relation_type, COALESCE(r.description, '')
        FROM plan_relations r
        JOIN plans p ON p.id = r.source_plan_id
        WHERE r.target_plan_id = $plan_id
        ORDER BY 1, 2;
    "
}

do_update_progress() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local sets=()
    if [[ -n "$OPT_MODE" ]]; then
        sets+=("mode = '$OPT_MODE'")
    fi
    if [[ -n "$OPT_SITUATION" ]]; then
        local encoded
        encoded="$(echo -n "$OPT_SITUATION" | base64)"
        sets+=("current_situation = '$encoded'")
    fi
    if [[ -n "$OPT_NEXT" ]]; then
        local encoded
        encoded="$(echo -n "$OPT_NEXT" | base64)"
        sets+=("next_action = '$encoded'")
    fi
    if [[ -n "$OPT_PR_GROUPS" ]]; then
        sets+=("pr_groups = '$OPT_PR_GROUPS'")
    fi
    if [[ -n "$OPT_REPOS" ]]; then
        sets+=("repositories = '$OPT_REPOS'")
    fi
    if [[ -n "$OPT_DOCS" ]]; then
        sets+=("docs = '$OPT_DOCS'")
    fi

    if [[ ${#sets[@]} -eq 0 ]]; then
        die "No fields to update. Use --mode, --situation, --next, --pr-groups, --repos, or --docs"
    fi

    sets+=("updated_at = datetime('now')")
    local set_clause
    set_clause="$(IFS=', '; echo "${sets[*]}")"

    sql_noheader "UPDATE plans SET $set_clause WHERE feature_name = '$OPT_FEATURE' AND project_id = $project_id;"
    echo "Progress updated for plan '$OPT_FEATURE'"
}

do_get_progress() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"

    local row
    row="$(sql_noheader "SELECT mode, current_situation, next_action, pr_groups, repositories, docs FROM plans WHERE feature_name = '$OPT_FEATURE' AND project_id = $project_id;")"
    if [[ -z "$row" ]]; then
        die "Plan '$OPT_FEATURE' not found"
    fi

    local mode situation next pr_groups repos docs_val
    mode="$(echo "$row" | cut -f1)"
    situation="$(echo "$row" | cut -f2)"
    next="$(echo "$row" | cut -f3)"
    pr_groups="$(echo "$row" | cut -f4)"
    repos="$(echo "$row" | cut -f5)"
    docs_val="$(echo "$row" | cut -f6)"

    echo "mode: $mode"
    if [[ -n "$situation" ]]; then
        echo -n "current_situation: "
        echo "$situation" | base64 -d
        echo
    fi
    if [[ -n "$next" ]]; then
        echo -n "next_action: "
        echo "$next" | base64 -d
        echo
    fi
    if [[ -n "$pr_groups" ]]; then
        echo "pr_groups: $pr_groups"
    fi
    if [[ -n "$repos" ]]; then
        echo "repositories: $repos"
    fi
    if [[ -n "$docs_val" ]]; then
        echo "docs: $docs_val"
    fi
}

do_get_comments() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    sql_noheader "
        SELECT json_group_array(json_object(
            'id', id,
            'section_heading', section_heading,
            'selected_text', selected_text,
            'comment', comment,
            'created_at', created_at
        ))
        FROM comments
        WHERE plan_id = $plan_id;
    "
}

do_clear_comments() {
    [[ -n "$OPT_FEATURE" ]] || die "--feature is required"

    ensure_db
    local project_id
    project_id="$(resolve_project_id)"
    local plan_id
    plan_id="$(resolve_plan_id "$OPT_FEATURE" "$project_id")"

    sql_noheader "DELETE FROM comments WHERE plan_id = $plan_id;"
    echo "Comments cleared for plan '$OPT_FEATURE'"
}

# ─── Main ───

main() {
    if [[ $# -lt 1 || "$1" == "--help" || "$1" == "-h" ]]; then
        cat >&2 <<'USAGE'
Usage: db.sh <subcommand> [options]

Subcommands:
  migrate              Run schema migrations
  register-project     Register a project (--name, --path)
  list-projects        List all projects
  create-plan          Create a plan (--feature, --title)
  get-plan             Get plan info (--feature)
  list-plans           List plans with status (--all for cross-project)
  update-plan          Update plan status (--feature, --status)
  get-body             Get plan body as Markdown (--feature)
  set-body             Set plan body from stdin (--feature)
  create-task          Create a task (--feature, --number, --desc)
  update-task-status   Update task status (--feature, --number, --status)
  delete-task          Delete a task (--feature, --number)
  list-tasks           List tasks (--feature)
  create-result        Create check result (--feature, --judgment, stdin)
  get-result           Get latest result (--feature)
  create-research      Create research (--topic, --feature optional, stdin)
  list-research        List research (--feature optional)
  get-research-body    Get research body (--id)
  create-debug         Create debug log (--feature optional, stdin)
  list-debug           List debug logs (--feature optional)
  add-relation         Add plan relation (--source, --target, --type)
  get-relations        Get plan relations (--feature)
  update-progress      Update progress info (--feature, --mode/--situation/--next)
  get-progress         Get progress info (--feature)
  get-comments         Get review comments as JSON (--feature)
  clear-comments       Clear review comments (--feature)

Common options:
  --project <name>     Project name (default: auto-detect from cwd)
USAGE
        exit 1
    fi

    local cmd="$1"
    shift
    parse_opts "$@"

    case "$cmd" in
        migrate)             do_migrate ;;
        register-project)    ensure_db; do_register_project ;;
        list-projects)       ensure_db; do_list_projects ;;
        create-plan)         do_create_plan ;;
        get-plan)            do_get_plan ;;
        list-plans)          do_list_plans ;;
        update-plan)         do_update_plan ;;
        get-body)            do_get_body ;;
        set-body)            do_set_body ;;
        create-task)         do_create_task ;;
        update-task-status)  do_update_task_status ;;
        delete-task)         do_delete_task ;;
        list-tasks)          do_list_tasks ;;
        create-result)       do_create_result ;;
        get-result)          do_get_result ;;
        create-research)     do_create_research ;;
        list-research)       do_list_research ;;
        get-research-body)   do_get_research_body ;;
        create-debug)        do_create_debug ;;
        list-debug)          do_list_debug ;;
        add-relation)        do_add_relation ;;
        get-relations)       do_get_relations ;;
        update-progress)     do_update_progress ;;
        get-progress)        do_get_progress ;;
        get-comments)        do_get_comments ;;
        clear-comments)      do_clear_comments ;;
        *)                   die "Unknown subcommand: $cmd" ;;
    esac
}

main "$@"
