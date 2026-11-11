import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

DB_PATH: Path = settings.DATA_RAW_DIR.parent / "faculty_reviews.db"
JSON_PATH: Path = settings.FACULTY_REVIEWS_PATH


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = _get_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS faculty_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                action TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                reviewer_notes TEXT,
                previous_value TEXT,
                new_value TEXT,
                modified_edit TEXT,
                custom_reply TEXT,
                status TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_report_id ON faculty_reviews(report_id);"
        )
    conn.close()


def save_review_action(
    report_id: str,
    action: str,
    reviewer_name: str,
    reviewer_notes: Optional[str] = None,
    previous_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    modified_edit: Optional[Dict[str, Any]] = None,
    custom_reply: Optional[str] = None,
    status: Optional[str] = None,
    db_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    
    if not status:
        if action == "approve":
            status = "approved_staged"
        elif action == "reject":
            status = "rejected"
        elif action == "modify":
            status = "modified_staged"
        else:
            status = action

    prev_val_str = json.dumps(previous_value) if previous_value is not None else None
    new_val_str = json.dumps(new_value) if new_value is not None else None
    edit_str = json.dumps(modified_edit) if modified_edit is not None else None

    conn = _get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO faculty_reviews (
                report_id, action, reviewer_name, reviewed_at,
                reviewer_notes, previous_value, new_value,
                modified_edit, custom_reply, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                action,
                reviewer_name,
                now_iso,
                reviewer_notes,
                prev_val_str,
                new_val_str,
                edit_str,
                custom_reply,
                status,
            ),
        )
        inserted_id = cursor.lastrowid
    conn.close()

    record = {
        "id": inserted_id,
        "report_id": report_id,
        "action": action,
        "reviewer_name": reviewer_name,
        "reviewed_at": now_iso,
        "reviewer_notes": reviewer_notes,
        "previous_value": previous_value,
        "new_value": new_value,
        "modified_edit": modified_edit,
        "custom_reply": custom_reply,
        "status": status,
    }

    # Mirror to JSON file for cross-compatibility
    _sync_json_storage(json_path, db_path)

    return record


def get_all_reviews(
    db_path: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    init_db(db_path)
    conn = _get_connection(db_path)
    cursor = conn.execute(
        """
        SELECT id, report_id, action, reviewer_name, reviewed_at,
               reviewer_notes, previous_value, new_value,
               modified_edit, custom_reply, status
        FROM faculty_reviews
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        prev_val = json.loads(r["previous_value"]) if r["previous_value"] else None
        new_val = json.loads(r["new_value"]) if r["new_value"] else None
        edit_val = json.loads(r["modified_edit"]) if r["modified_edit"] else None

        item = {
            "id": r["id"],
            "report_id": r["report_id"],
            "action": r["action"],
            "reviewer_name": r["reviewer_name"],
            "reviewed_at": r["reviewed_at"],
            "reviewer_notes": r["reviewer_notes"],
            "previous_value": prev_val,
            "new_value": new_val,
            "modified_edit": edit_val,
            "custom_reply": r["custom_reply"],
            "status": r["status"],
        }
        grouped.setdefault(r["report_id"], []).append(item)

    result: Dict[str, Dict[str, Any]] = {}
    for rep_id, history in grouped.items():
        latest = history[-1]
        result[rep_id] = {
            **latest,
            "history": history,
        }
    return result


def _sync_json_storage(
    json_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> None:
    target_path = json_path or JSON_PATH
    all_revs = get_all_reviews(db_path)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(all_revs, f, indent=2)

