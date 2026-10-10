"""Google Drive API v3 Two-Way Synchronizer for Omni-Video & Spark.
100% Direct Cloud-First Sync via Service Account (Zero Local CloudStorage path dependency).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger("drive_sync")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

PROJECT_DIR = Path(__file__).resolve().parent.parent
SA_PATH = PROJECT_DIR / "config" / "service_account.json"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
UPLOAD_API_BASE = "https://www.googleapis.com/upload/drive/v3"


def get_drive_session() -> Optional[AuthorizedSession]:
    """Authenticates and returns an authorized HTTP session using service account credentials."""
    if not SA_PATH.exists():
        logger.error(f"Service Account not found at {SA_PATH}")
        return None
    try:
        creds = Credentials.from_service_account_file(str(SA_PATH), scopes=SCOPES)
        return AuthorizedSession(creds)
    except Exception as e:
        logger.error(f"Failed to create Drive AuthorizedSession: {e}")
        return None


def search_files(
    query: str, fields: str = "files(id, name, mimeType, parents, modifiedTime)"
) -> List[Dict[str, Any]]:
    """Searches files in Google Drive matching the query."""
    session = get_drive_session()
    if not session:
        return []

    url = f"{DRIVE_API_BASE}/files"
    params = {
        "q": query,
        "fields": fields,
        "spaces": "drive",
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }
    try:
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("files", [])
        logger.error(f"Drive search failed ({resp.status_code}): {resp.text}")
        return []
    except Exception as e:
        logger.error(f"Exception during Drive search: {e}")
        return []


FILE_ALIASES = {
    "ideas.md": ["ideas_omni", "IDEAS.md", "ideas"],
    "ideas_omni": ["ideas_omni", "IDEAS.md", "ideas"],
    "anti-spark_omni.md": ["tasks_anti", "anti-spark_omni.md", "anti-spark", "tasks_anti.md"],
    "tasks_anti": ["tasks_anti", "anti-spark_omni.md", "tasks_anti.md"],
}


def find_file_info(filename: str, parent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Finds file metadata (id, name, mimeType) for a filename or its known aliases."""
    search_names = [filename]
    norm = filename.lower().strip()
    if norm in FILE_ALIASES:
        search_names.extend(FILE_ALIASES[norm])

    for name_candidate in search_names:
        q_parts = [f"name = '{name_candidate}'", "trashed = false"]
        if parent_id:
            q_parts.append(f"'{parent_id}' in parents")
        query = " and ".join(q_parts)

        files = search_files(query)
        if files:
            return files[0]

    # Fallback search without parent
    for name_candidate in search_names:
        files = search_files(f"name contains '{name_candidate}' and trashed = false")
        if files:
            return files[0]

    return None


def find_file_id(filename: str, parent_id: Optional[str] = None) -> Optional[str]:
    """Finds the file ID for a given filename, optionally restricted to a parent folder."""
    info = find_file_info(filename, parent_id=parent_id)
    return info["id"] if info else None


def read_drive_file(filename: str, parent_id: Optional[str] = None) -> Optional[str]:
    """Reads and returns the string content of a file or Google Doc from Google Drive via API v3."""
    file_info = find_file_info(filename, parent_id=parent_id)
    if not file_info:
        logger.warning(f"File '{filename}' not found on Google Drive.")
        return None

    file_id = file_info["id"]
    mime_type = file_info.get("mimeType", "")

    session = get_drive_session()
    if not session:
        return None

    try:
        if mime_type == "application/vnd.google-apps.document":
            # Export Google Doc as plain text
            url = f"{DRIVE_API_BASE}/files/{file_id}/export"
            params = {"mimeType": "text/plain"}
            resp = session.get(url, params=params, timeout=30)
        else:
            # Download regular binary / text file
            url = f"{DRIVE_API_BASE}/files/{file_id}"
            params = {"alt": "media"}
            resp = session.get(url, params=params, timeout=30)

        if resp.status_code == 200:
            return resp.text
        logger.error(f"Failed to read file '{filename}' ({resp.status_code}): {resp.text}")
        return None
    except Exception as e:
        logger.error(f"Exception reading file '{filename}' from Drive: {e}")
        return None


def write_drive_file(
    filename: str,
    content: str,
    parent_id: Optional[str] = None,
    mime_type: str = "text/markdown",
) -> bool:
    """Creates or updates a text/markdown file on Google Drive via API v3."""
    session = get_drive_session()
    if not session:
        return False

    file_id = find_file_id(filename, parent_id=parent_id)
    data_bytes = content.encode("utf-8")

    try:
        if file_id:
            # Update existing file
            url = f"{UPLOAD_API_BASE}/files/{file_id}?uploadType=media"
            headers = {"Content-Type": f"{mime_type}; charset=UTF-8"}
            resp = session.patch(url, data=data_bytes, headers=headers, timeout=30)
            if resp.status_code in [200, 201]:
                logger.info(f"Successfully updated '{filename}' (ID: {file_id}) on Google Drive.")
                return True
            logger.error(f"Failed to update '{filename}' ({resp.status_code}): {resp.text}")
            return False
        else:
            # Create new file with multipart upload
            url = f"{UPLOAD_API_BASE}/files?uploadType=multipart"
            metadata: Dict[str, Any] = {"name": filename, "mimeType": mime_type}
            if parent_id:
                metadata["parents"] = [parent_id]

            boundary = "==============drive_sync_boundary=="
            headers = {"Content-Type": f"multipart/related; boundary={boundary}"}

            body = (
                f"--{boundary}\r\n"
                f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
                f"{json.dumps(metadata)}\r\n"
                f"--{boundary}\r\n"
                f"Content-Type: {mime_type}; charset=UTF-8\r\n\r\n"
                f"{content}\r\n"
                f"--{boundary}--\r\n"
            ).encode("utf-8")

            resp = session.post(url, data=body, headers=headers, timeout=30)
            if resp.status_code in [200, 201]:
                created_id = resp.json().get("id")
                logger.info(f"Successfully created '{filename}' (ID: {created_id}) on Google Drive.")
                return True
            logger.error(f"Failed to create '{filename}' ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Exception writing file '{filename}' to Drive: {e}")
        return False


def append_to_anti_spark_log(log_entry: str, file_name: str = "anti-spark_omni.md") -> bool:
    """Appends a new log block into anti-spark_omni.md under Antigravity's log section."""
    content = read_drive_file(file_name)
    if not content:
        logger.error(f"Cannot read '{file_name}' from Drive to append log.")
        return False

    target_header = "### 📋 Nhật ký & Báo cáo từ Antigravity:\n```markdown"
    if target_header in content:
        parts = content.split(target_header, 1)
        updated_content = (
            parts[0]
            + target_header
            + "\n"
            + log_entry.strip()
            + "\n"
            + parts[1]
        )
    else:
        # Fallback: append at the end of Section 2
        updated_content = content + f"\n\n```markdown\n{log_entry}\n```\n"

    return write_drive_file(file_name, updated_content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 drive_sync.py [read|write|append|test] [args...]")
        print("Examples:")
        print("  python3 drive_sync.py read anti-spark_omni.md")
        print("  python3 drive_sync.py read IDEAS.md")
        print("  python3 drive_sync.py write test.txt 'Hello World'")
        print("  python3 drive_sync.py test")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "test":
        print("Testing Google Drive API v3 Connection...")
        session = get_drive_session()
        if not session:
            print("❌ Authentication failed.")
            sys.exit(1)
        files = search_files("trashed = false", fields="files(id, name, mimeType)")
        print(f"✅ Connection successful! Found {len(files)} files accessible by Service Account:")
        for f in files[:10]:
            print(f" - [{f.get('mimeType')}] {f.get('name')} (ID: {f.get('id')})")

    elif command == "read":
        if len(sys.argv) < 3:
            print("Error: Missing filename to read.")
            sys.exit(1)
        fname = sys.argv[2]
        content = read_drive_file(fname)
        if content is not None:
            print(f"=== CONTENT OF {fname} ===")
            print(content)
        else:
            print(f"❌ Failed to read '{fname}' from Google Drive.")
            sys.exit(1)

    elif command == "write":
        if len(sys.argv) < 4:
            print("Error: Usage: python3 drive_sync.py write <filename> <content_or_filepath>")
            sys.exit(1)
        fname = sys.argv[2]
        raw_input = sys.argv[3]
        if os.path.exists(raw_input):
            with open(raw_input, "r", encoding="utf-8") as f:
                content_to_write = f.read()
        else:
            content_to_write = raw_input
        success = write_drive_file(fname, content_to_write)
        if success:
            print(f"✅ Successfully written to '{fname}' on Google Drive.")
        else:
            print(f"❌ Failed to write to '{fname}' on Google Drive.")
            sys.exit(1)

    elif command == "append":
        if len(sys.argv) < 3:
            print("Error: Usage: python3 drive_sync.py append <log_message>")
            sys.exit(1)
        msg = sys.argv[2]
        success = append_to_anti_spark_log(msg)
        if success:
            print("✅ Log entry successfully appended to anti-spark_omni.md on Google Drive.")
        else:
            print("❌ Failed to append log to anti-spark_omni.md.")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
