# Rule: Always Map Columns by Header Name (Dynamic Header Mapping)

## Core Requirement
When reading, writing, or upserting data to Google Sheets:
1. **NEVER use hardcoded column indexes** (e.g. `row[0]`, `row[1]`).
2. **ALWAYS read Row 1 headers dynamically** and map product/video data fields to matching column header names or aliases.
3. **Resilience Guarantee**: If columns are reordered, inserted, or removed in Google Sheets, the integration must NEVER shift data or overwrite wrong columns.
