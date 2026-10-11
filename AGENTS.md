# AGENTS.md — Omni-Video Architecture & Guidelines

> **Last Updated:** 17/08/2026

## 1. Project Overview
Omni-Video automates the generation of UGC (User Generated Content) video scripts, product asset curation from Shopee/TikTok/Douyin, and automated Video QA.

## 2. Core Integrations
- **Google Sheets API v4:** Direct integration via `gspread` and `config/service_account.json`. Spreadsheet ID: `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`.
- **Google Drive API v3:** Direct Two-Way Cloud Sync with Spark (`scripts/drive_sync.py` and `config/service_account.json`). Zero dependency on macOS local sync paths.
- **Zero Apps Script:** Google Apps Script webhooks have been 100% eliminated.
- **AI Models:** Priority list for prompts: `["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]`.

## 3. Mandatory AI Rules
- **Rule 1:** Always consult and obtain explicit user approval before editing code (`.agents/rules/always_consult_user_first.md`).
- **Rule 2:** Push only to a feature branch + Pull Request; never push `main` directly (Kha merges on GitHub). No `git commit -am` / `git add -A` / `git add .`; only the "Thực thi – Omni-Video" session commits/pushes (`.agents/rules/git_branch_pr_only.md`).
- **Rule 3:** Never use `-preview` models.
- **Rule 4:** Always communicate with Spark 100% via Google Drive API v3 (`.agents/rules/always_use_drive_api_for_spark.md`).

