# AGENTS.md — Omni-Video Architecture & Guidelines

> **Last Updated:** 17/08/2026

## 1. Project Overview
Omni-Video automates the generation of UGC (User Generated Content) video scripts, product asset curation from Shopee/TikTok/Douyin, and automated Video QA.

## 2. Core Integrations
- **Google Sheets API v4:** Direct integration via `gspread` and `config/service_account.json`. Spreadsheet ID: `1Xg67qhp1J_Izt7v5uDKRgKjdEZapX9giKJ_ym0OMJN4`.
- **Zero Apps Script:** Google Apps Script webhooks have been 100% eliminated.
- **AI Models:** Priority list for prompts: `["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]`.

## 3. Mandatory AI Rules
- **Rule 1:** Always consult and obtain explicit user approval before editing code (`.agents/rules/always_consult_user_first.md`).
- **Rule 2:** Never push to Git automatically.
- **Rule 3:** Never use `-preview` models.
