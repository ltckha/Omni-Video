# AGENTS.md — Omni-Video Architecture & Guidelines

> **Last Updated:** 15/10/2026

## 1. Project Overview
Omni-Video automates the generation of UGC (User Generated Content) video scripts, product asset curation from Shopee/TikTok/Douyin, and automated Video QA.

## 2. Core Integrations
- **Google Sheets API v4:** Direct integration via `gspread` and `config/service_account.json`. Spreadsheet ID: `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`.
- **Google Drive API v3:** Direct Two-Way Cloud Sync with Spark (`scripts/drive_sync.py` and `config/service_account.json`). Zero dependency on macOS local sync paths.
- **Zero Apps Script:** Google Apps Script webhooks have been 100% eliminated.
- **AI Models:** Priority list for prompts: `["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]` (no `gemini-3.5-flash`: counted against 3.6 quota).

## 3. Mandatory AI Rules
- **Rule 1:** Always consult and obtain explicit user approval before editing code or running project-changing commands (`.agents/rules/always_consult_user_first.md`).
- **Rule 2:** Commit locally on `main` only — no feature branches / PRs, never push yourself; Kha pushes at 21:00 via `push_all.command` or by saying "đẩy". No `git commit -am` / `git add -A` / `git add .`; only the "Thực thi – Omni-Video" session commits (`.agents/rules/git_push_rule.md`, shared rule LUAT_CHUNG #1).
- **Rule 3:** Never use `-preview` models.
- **Rule 4:** Always communicate with Spark 100% via Google Drive API v3 (`.agents/rules/always_use_drive_api_for_spark.md`).

