import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root and scripts/ directory to sys.path
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from drive_sync import (
    get_drive_session,
    search_files,
    find_file_id,
    read_drive_file,
    write_drive_file,
    append_to_anti_spark_log,
)


class TestDriveSync:
    @patch("drive_sync.SA_PATH")
    @patch("drive_sync.Credentials.from_service_account_file")
    @patch("drive_sync.AuthorizedSession")
    def test_get_drive_session_success(self, mock_auth_session, mock_creds, mock_sa_path):
        mock_sa_path.exists.return_value = True
        mock_creds.return_value = MagicMock()
        mock_auth_session.return_value = MagicMock()

        session = get_drive_session()
        assert session is not None
        mock_creds.assert_called_once()
        mock_auth_session.assert_called_once()

    @patch("drive_sync.SA_PATH")
    def test_get_drive_session_missing_sa(self, mock_sa_path):
        mock_sa_path.exists.return_value = False
        session = get_drive_session()
        assert session is None

    @patch("drive_sync.get_drive_session")
    def test_search_files_success(self, mock_get_session):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "files": [{"id": "123", "name": "anti-spark_omni.md", "mimeType": "text/markdown"}]
        }
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        results = search_files("name = 'anti-spark_omni.md'")
        assert len(results) == 1
        assert results[0]["id"] == "123"
        assert results[0]["name"] == "anti-spark_omni.md"

    @patch("drive_sync.search_files")
    def test_find_file_id_found(self, mock_search):
        mock_search.return_value = [{"id": "file_abc_123", "name": "IDEAS.md"}]
        file_id = find_file_id("IDEAS.md")
        assert file_id == "file_abc_123"

    @patch("drive_sync.search_files")
    def test_find_file_id_not_found(self, mock_search):
        mock_search.return_value = []
        file_id = find_file_id("non_existent.md")
        assert file_id is None

    @patch("drive_sync.find_file_id")
    @patch("drive_sync.get_drive_session")
    def test_read_drive_file_success(self, mock_get_session, mock_find_id):
        mock_find_id.return_value = "file_123"
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "# Anti-Spark Omni Content"
        mock_session.get.return_value = mock_resp
        mock_get_session.return_value = mock_session

        content = read_drive_file("anti-spark_omni.md")
        assert content == "# Anti-Spark Omni Content"

    @patch("drive_sync.find_file_id")
    def test_read_drive_file_not_found(self, mock_find_id):
        mock_find_id.return_value = None
        content = read_drive_file("missing.md")
        assert content is None

    @patch("drive_sync.find_file_id")
    @patch("drive_sync.get_drive_session")
    def test_write_drive_file_update_existing(self, mock_get_session, mock_find_id):
        mock_find_id.return_value = "existing_id_123"
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.patch.return_value = mock_resp
        mock_get_session.return_value = mock_session

        success = write_drive_file("test.md", "# New Content")
        assert success is True
        mock_session.patch.assert_called_once()

    @patch("drive_sync.find_file_id")
    @patch("drive_sync.get_drive_session")
    def test_write_drive_file_create_new(self, mock_get_session, mock_find_id):
        mock_find_id.return_value = None
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": "new_created_id_456"}
        mock_session.post.return_value = mock_resp
        mock_get_session.return_value = mock_session

        success = write_drive_file("new_file.md", "# Fresh File")
        assert success is True
        mock_session.post.assert_called_once()

    @patch("drive_sync.read_drive_file")
    @patch("drive_sync.write_drive_file")
    def test_append_to_anti_spark_log_success(self, mock_write, mock_read):
        mock_read.return_value = (
            "# Header\n"
            "### 📋 Nhật ký & Báo cáo từ Antigravity:\n```markdown\n"
            "[12/09/2026] Log 1\n"
            "```\n"
        )
        mock_write.return_value = True

        success = append_to_anti_spark_log("[15/09/2026] New Log from Antigravity")
        assert success is True
        mock_write.assert_called_once()
        written_content = mock_write.call_args[0][1]
        assert "[15/09/2026] New Log from Antigravity" in written_content
