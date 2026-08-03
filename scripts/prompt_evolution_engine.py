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

def evolve_prompt_from_qa(item_dir, qa_report):
    """
    Dựa vào báo cáo QA để tự động học và bổ sung Negative Constraints vào Master Prompt
    """
    prompt_file = os.path.join(item_dir, "master_prompt.txt")
    if not os.path.exists(prompt_file) or not qa_report:
        return False

    recommendations = qa_report.get("recommendations_for_prompt", [])
    flaws = qa_report.get("detected_flaws", [])
    score = qa_report.get("total_score", 100)

    # Đầu tiên lưu bản Backup hiện tại trước khi nâng cấp
    backup_current_prompt(item_dir, score=score)

    if not recommendations and not flaws:
        print("ℹ️ Video không có lỗi lớn, giữ nguyên cấu trúc Master Prompt hiện tại.")
        return False

    # Đọc nội dung Master Prompt hiện tại
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_content = f.read()
    except Exception as e:
        print(f"⚠️ Lỗi đọc master_prompt.txt: {e}")
        return False

    # Bổ sung các quy tắc né lỗi mới vào mục STYLE / NEGATIVE GUIDELINES
    added_rules = []
    for rec in recommendations:
        rule_str = f"- AI EVOLVED RULE: {rec}"
        if rule_str not in prompt_content:
            added_rules.append(rule_str)

    for fl in flaws:
        rule_str = f"- AVOID DETECTED FLAW: {fl}"
        if rule_str not in prompt_content:
            added_rules.append(rule_str)

    if not added_rules:
        return False

    evolution_block = "\n" + "\n".join(added_rules) + "\n"

    # Chèn bài học tiến hóa vào trước phần kết thúc
    if "STYLE GUIDELINES:" in prompt_content:
        updated_content = prompt_content.replace("STYLE GUIDELINES:", "STYLE GUIDELINES:" + evolution_block)
    else:
        updated_content = prompt_content + "\n\n# AI EVOLUTION CONSTRAINTS:" + evolution_block

    try:
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"🧬 Đã tự động nâng cấp Master Prompt với {len(added_rules)} quy tắc bài học mới từ QA!")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi ghi Master Prompt nâng cấp: {e}")
        return False

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
