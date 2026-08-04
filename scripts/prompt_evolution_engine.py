#!/usr/bin/env python3
"""
Omni Video - Prompt Evolution & Version Control Backup Engine
Quản lý sao lưu (Backup), khôi phục (Rollback) và tự động tiến hóa (Self-Evolution) cho Master Prompt:
1. Tự động lưu bản backup vào Product_Assets/<Mã_SP>/prompt_backups/master_prompt_v{N}.txt
2. Tự động đúc kết kinh nghiệm từ báo cáo QA để học và nâng cấp Master Prompt
3. Tự động Rollback về bản Backup tốt nhất nếu điểm số QA suy giảm
"""

import os
import sys
import glob
import json
import shutil
from datetime import datetime

def get_backups_dir(item_dir):
    backups_dir = os.path.join(item_dir, "prompt_backups")
    os.makedirs(backups_dir, exist_ok=True)
    return backups_dir

def backup_current_prompt(item_dir, score=None):
    """
    Tự động lưu bản backup của master_prompt.txt hiện tại
    """
    prompt_file = os.path.join(item_dir, "master_prompt.txt")
    if not os.path.exists(prompt_file):
        return None

    backups_dir = get_backups_dir(item_dir)
    existing_backups = glob.glob(os.path.join(backups_dir, "master_prompt_v*.txt"))
    
    version_num = len(existing_backups) + 1
    backup_file = os.path.join(backups_dir, f"master_prompt_v{version_num}.txt")

    try:
        shutil.copy2(prompt_file, backup_file)
        
        # Lưu file metadata đi kèm
        meta_file = os.path.join(backups_dir, f"master_prompt_v{version_num}.json")
        meta_data = {
            "version": version_num,
            "created_at": datetime.now().isoformat(),
            "score": score
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

        print(f"📦 Đã tạo bản Backup Prompt v{version_num} tại: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"⚠️ Lỗi tạo Backup Prompt: {e}")
        return None

def update_global_learned_rules(added_rules):
    """
    Lưu trữ các bài học QA vào file hệ thống chung scripts/global_learned_rules.json
    để tất cả các sản phẩm mới sau này tự động kế thừa.
    """
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    global_file = os.path.join(project_dir, "scripts", "global_learned_rules.json")
    
    rules_data = []
    if os.path.exists(global_file):
        try:
            with open(global_file, "r", encoding="utf-8") as f:
                rules_data = json.load(f)
        except Exception:
            rules_data = []

    existing_set = set(rules_data)
    new_count = 0
    for r in added_rules:
        clean_r = r.replace("- AI EVOLVED RULE: ", "").replace("- AVOID DETECTED FLAW: ", "").strip()
        if clean_r and clean_r not in existing_set:
            rules_data.append(clean_r)
            existing_set.add(clean_r)
            new_count += 1

    if new_count > 0:
        try:
            with open(global_file, "w", encoding="utf-8") as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            print(f"🌐 Đã cập nhật {new_count} bài học mới vào Hồ sơ Hệ thống chung (global_learned_rules.json)!")
        except Exception as e:
            print(f"⚠️ Lỗi cập nhật global_learned_rules.json: {e}")

def evolve_prompt_from_qa(item_dir, qa_report, create_backup=False):
    """
    Dựa vào báo cáo QA để tự động học và bổ sung Negative Constraints vào Master Prompt.
    Chỉ tạo backup nếu create_backup=True (khi video không đạt chuẩn cần sửa lại).
    """
    prompt_file = os.path.join(item_dir, "master_prompt.txt")
    if not os.path.exists(prompt_file) or not qa_report:
        return False

    recommendations = qa_report.get("recommendations_for_prompt", [])
    flaws = qa_report.get("detected_flaws", [])
    score = qa_report.get("total_score", 100)

    # Chỉ tạo bản Backup khi video lỗi/cần sửa
    if create_backup:
        backup_current_prompt(item_dir, score=score)

    if not recommendations and not flaws:
        return False

    # Cập nhật bài học vào Hồ sơ Hệ thống chung (Global System Memory)
    added_rules = recommendations + flaws
    update_global_learned_rules(added_rules)

    return True

def rollback_to_best_prompt(item_dir):
    """
    Tự động tìm và khôi phục bản Backup Prompt có điểm số QA cao nhất
    """
    backups_dir = os.path.join(item_dir, "prompt_backups")
    if not os.path.exists(backups_dir):
        return False

    meta_files = glob.glob(os.path.join(backups_dir, "master_prompt_v*.json"))
    if not meta_files:
        return False

    best_v = None
    best_score = -1

    for mf in meta_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                mdata = json.load(f)
                score = mdata.get("score") or 0
                version = mdata.get("version")
                if score > best_score:
                    best_score = score
                    best_v = version
        except Exception:
            pass

    if best_v is not None:
        best_txt = os.path.join(backups_dir, f"master_prompt_v{best_v}.txt")
        target_txt = os.path.join(item_dir, "master_prompt.txt")
        if os.path.exists(best_txt):
            try:
                shutil.copy2(best_txt, target_txt)
                print(f"🔄 Đã tự động Khôi Phục (Rollback) Master Prompt về bản Backup tốt nhất v{best_v} (Điểm QA: {best_score}/100)")
                return True
            except Exception as e:
                print(f"⚠️ Lỗi Rollback Prompt: {e}")

    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        backup_current_prompt(target_dir)
    else:
        print("Cách dùng: python3 scripts/prompt_evolution_engine.py <đường_dẫn_thư_mục_sản_phẩm>")
