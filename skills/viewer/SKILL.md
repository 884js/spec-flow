---
name: viewer
description: "Starts or stops the Annotation Viewer server. Use when managing the plan viewer server lifecycle."
allowed-tools: Bash
metadata:
  triggers: viewer, viewer start, viewer stop, サーバー起動, サーバー停止
---

# Annotation Viewer 管理

Annotation Viewer サーバーの起動・停止を行う。

入力: `$ARGUMENTS`（`start` または `stop`）

## start

1. ロックファイル `/tmp/annotation-viewer.lock` を確認
2. 存在しポートに疎通可能なら、そのポートでブラウザを開く
3. 存在しないか疎通不可なら、サーバーをバックグラウンド起動してブラウザを開く

```
Bash "
LOCK=/tmp/annotation-viewer.lock
SERVER=${CLAUDE_PLUGIN_ROOT}/scripts/annotation-viewer/server.py
PORT=''
if [ -f \"\$LOCK\" ]; then
  PORT=\$(python3 -c \"import json; print(json.load(open('\$LOCK')).get('port',''))\" 2>/dev/null)
  if [ -n \"\$PORT\" ] && curl -s -o /dev/null http://127.0.0.1:\$PORT/api/plans 2>/dev/null; then
    echo \"Server already running on port \$PORT\"
  else
    rm -f \"\$LOCK\"
    PORT=''
  fi
fi
if [ -z \"\$PORT\" ]; then
  python3 \"\$SERVER\" > /tmp/viewer-start.log 2>&1 &
  sleep 1
  PORT=\$(python3 -c \"import json; print(json.load(open('\$LOCK')).get('port',''))\" 2>/dev/null)
  echo \"Server started on port \$PORT\"
fi
open \"http://localhost:\$PORT\"
"
```

## stop

```
Bash "${CLAUDE_PLUGIN_ROOT}/scripts/annotation-cycle.sh --stop"
```
