#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Omni Video - chế độ hàng tiệm (anh Kha nói "làm" 30/10/2026 qua Phân tích · Xưởng video).
Video Flow cho giày tiệm Hiệu giày Hải Nancy, theo mã tiệm (vd JH8918N):
1. Tạo Product_Assets/<mã>/: ảnh từ NAS /Volumes/Media/HNC_Master/<mã>/ (chỉ ảnh) → web giayhainancy.vn/img/<mã>/<n>-1000.webp
   (n = 1, 2… tới khi 404; đổi sang JPG cho Flow) → image_01… của tab SANPHAM.
2. info.json lấy tên / màu / chất liệu từ SANPHAM + cờ hang_tiem = true. KHÔNG tạo dòng src_omni (Video-Post nhận video qua SANPHAM).
   Kịch bản <mã>.txt ghép từ mẫu config/hang_tiem.json + info.json bằng code, 0 Gemini (anh Kha 30/10: dùng Flow
   trên trình duyệt, không qua API) + chép ảnh người mẫu Nam- / Nu- theo giới tính → mở Flow bấm Tạo video luôn.
3. Sau khi tải từ Flow, video để nguyên ~/Downloads/<mã>.mp4 cho luồng gom của HNC; thư mục tạm tự dọn khi video đã rời Downloads.

Dùng: python scripts/hang_tiem.py <mã> [<mã> …]    (HangTiem.command hỏi mã rồi chạy lệnh này)
"""

import glob
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(PROJECT_DIR, "Product_Assets")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
HNC_MEDIA_DIR = "/Volumes/Media/HNC_Master"

# Sheet HNC_Control_Center, tab SANPHAM: tên cột kỹ thuật ở HÀNG 2 (hàng 1 là tên nhóm) — luật chung 4
SANPHAM_SHEET_ID = "1U0b6_aVJJ93i5-V1RV1jUsQ9dhLYCY9BcJMI7R6J2C0"
SANPHAM_TAB = "SANPHAM"
SANPHAM_HEADER_ROW = 2
SANPHAM_IMAGE_COLUMNS = [f"image_{i:02d}" for i in range(1, 11)]
INFO_FIELDS = ("product_color", "chat_lieu", "chat_lieu_de", "kieu_giay_tay", "gioi_tinh")

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SHOP_IMAGE_URL = "https://giayhainancy.vn/img/{code}/{n}-1000.webp"  # ảnh anh đưa lên web; 0-400 là ảnh nhỏ, bỏ
SHOP_IMAGE_MAX = 20


def read_info(item_dir: str) -> Dict:
    try:
        with open(os.path.join(item_dir, "info.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_info(item_dir: str, info: Dict) -> None:
    with open(os.path.join(item_dir, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def is_hang_tiem(item_dir: str) -> bool:
    return bool(read_info(item_dir).get("hang_tiem"))


def sanpham_rows(values: List[List[str]], codes: List[str]) -> Dict[str, Dict[str, str]]:
    """Dòng SANPHAM theo product_code (tiêu đề ở hàng SANPHAM_HEADER_ROW)."""
    headers = [h.strip() for h in values[SANPHAM_HEADER_ROW - 1]]
    wanted = set(codes)
    found = {}
    for row in values[SANPHAM_HEADER_ROW:]:
        d = dict(zip(headers, row))
        code = d.get("product_code", "").strip()
        if code in wanted and code not in found:
            found[code] = d
    return found


def read_sanpham(codes: List[str]) -> Dict[str, Dict[str, str]]:
    from sheet_sync import get_gspread_client
    gc = get_gspread_client()
    if not gc:
        raise RuntimeError("Không kết nối được Google Sheets (Service Account).")
    values = gc.open_by_key(SANPHAM_SHEET_ID).worksheet(SANPHAM_TAB).get_all_values()
    return sanpham_rows(values, codes)


def nas_images(code: str, media_dir: str = HNC_MEDIA_DIR) -> List[str]:
    folder = os.path.join(media_dir, code)
    return sorted(f for f in glob.glob(os.path.join(folder, "*")) if f.lower().endswith(IMAGE_EXTS))


def _fetch_image(url: str) -> Optional[bytes]:
    """Tải 1 ảnh; 404 / không phải ảnh → None."""
    from omni_env import google_ssl_context
    try:
        # web của tiệm trả 403 cho User-Agent mặc định của Python → tự xưng tên công cụ
        req = urllib.request.Request(url, headers={"User-Agent": "OmniVideo/1.0 (Hieu giay Hai Nancy)"})
        with urllib.request.urlopen(req, timeout=30, context=google_ssl_context()) as resp:
            if not (resp.headers.get("Content-Type") or "").startswith("image/"):
                return None
            return resp.read()
    except urllib.error.HTTPError:
        return None


def _save_as_jpg(data: bytes, path: str) -> None:
    """Lưu ảnh dạng JPG (Flow không nhận webp khi dán) bằng `sips` có sẵn của macOS."""
    import subprocess
    import tempfile
    if data[:3] == b"\xff\xd8\xff":
        with open(path, "wb") as f:
            f.write(data)
        return
    with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
        tmp.write(data)
    try:
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", tmp.name, "--out", path],
                       check=True, capture_output=True)
    finally:
        os.remove(tmp.name)


def download_shop_web_images(code: str, item_dir: str, fetch=_fetch_image) -> List[str]:
    """Ảnh trên web giayhainancy.vn: <n>-1000.webp, n = 1, 2… tới khi 404."""
    saved = []
    for n in range(1, SHOP_IMAGE_MAX + 1):
        data = fetch(SHOP_IMAGE_URL.format(code=code, n=n))
        if not data:
            break
        path = os.path.join(item_dir, f"{code}_web_{n:02d}.jpg")
        _save_as_jpg(data, path)
        saved.append(path)
    return saved


def download_sanpham_images(code: str, row: Dict[str, str], item_dir: str, fetch=_fetch_image) -> List[str]:
    saved = []
    for i, col in enumerate(SANPHAM_IMAGE_COLUMNS, start=1):
        url = (row.get(col) or "").strip()
        if not url.startswith("http"):
            continue
        try:
            data = fetch(url)
        except Exception as e:
            print(f"  ⚠️ Không tải được {col}: {e}")
            continue
        if data:
            path = os.path.join(item_dir, f"{code}_sp_{i:02d}.jpg")
            _save_as_jpg(data, path)
            saved.append(path)
    return saved


def download_web_images(code: str, row: Dict[str, str], item_dir: str) -> List[str]:
    """Web giayhainancy.vn trước, trống thì image_01… của SANPHAM."""
    return download_shop_web_images(code, item_dir) or download_sanpham_images(code, row, item_dir)


def build_info(code: str, row: Dict[str, str], old: Optional[Dict] = None) -> Dict:
    info = dict(old or {})
    info.pop("da_tai", None)  # chạy lại = làm lại video → hiện lại trong popup
    info.update({"itemId": code, "productName": (row.get("product_name") or code).strip(), "hang_tiem": True})
    for field in INFO_FIELDS:
        info[field] = (row.get(field) or "").strip()
    return info


def prepare(code: str, row: Dict[str, str], assets_dir: str = ASSETS_DIR, media_dir: str = HNC_MEDIA_DIR,
            downloads_dir: str = DOWNLOADS_DIR, fetch_web=download_web_images) -> Optional[str]:
    """Tạo / làm mới Product_Assets/<mã>/. Trả đường dẫn thư mục, hoặc None nếu mã không có ảnh."""
    item_dir = os.path.join(assets_dir, code)
    existed = os.path.isdir(item_dir)
    os.makedirs(item_dir, exist_ok=True)
    have = [f for f in glob.glob(os.path.join(item_dir, "*")) if f.lower().endswith(IMAGE_EXTS)
            and not os.path.basename(f).lower().startswith(("nu-", "nam-"))]
    if not have:
        for src in nas_images(code, media_dir):
            shutil.copy2(src, os.path.join(item_dir, os.path.basename(src)))
            have.append(src)
        if not have:
            have = fetch_web(code, row, item_dir)
    if not have:
        if not existed:
            shutil.rmtree(item_dir, ignore_errors=True)
        return None
    write_info(item_dir, build_info(code, row, read_info(item_dir)))
    if os.path.exists(os.path.join(downloads_dir, f"{code}.mp4")):
        print(f"  ⚠️ ~/Downloads/{code}.mp4 đang có sẵn — video mới sẽ bị Chrome đặt tên khác. Chờ HNC gom xong rồi hãy Tạo video.")
    return item_dir


CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "hang_tiem.json")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
# thứ tự = ưu tiên: kiểu cụ thể ("xỏ chân") thắng "giày tây" chung (giày tây → "shoes", không ghi dress shoes vì Flow vẽ giày buộc dây)
SHOE_TYPES = ("xỏ chân", "giày lười", "giày mọi", "giày thể thao", "giày sandal", "giày cao gót", "giày búp bê",
              "sandal", "boot", "dép", "giày tây", "giày")


def load_config(path: str = CONFIG_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def translate(value: str, dich: Dict[str, str]) -> str:
    """Tiếng Việt → tiếng Anh theo bảng `dich`: khớp nguyên cụm, không có thì giữ nguyên chữ gốc."""
    key = value.strip().lower()
    return dich.get(key, value.strip())


def is_female(info: Dict) -> bool:
    return info.get("gioi_tinh", "").strip().lower() in ("nữ", "nu", "female")


def describe_shoe(info: Dict, cfg: Dict) -> Dict[str, str]:
    dich = cfg.get("dich", {})
    name = info.get("productName", "").lower()
    shoe_type = next((t for t in SHOE_TYPES if t in name), "giày")
    material = info.get("chat_lieu", "").strip()
    # tên SP thường rõ hơn cột chất liệu (vd "da bò hạt mềm") → lấy cụm dài nhất trong bảng dịch có trong tên
    longer = [k for k in dich if material and k.startswith(material.lower()) and k in name]
    material = max(longer, key=len) if longer else material
    parts = {
        "type": ("women's " if is_female(info) else "men's ") + translate(shoe_type, dich),
        "color": translate(info.get("product_color", ""), dich) or "the color shown in the images",
        "material": translate(material, dich) or "the material shown in the images",
        "sole": translate(info.get("chat_lieu_de", ""), dich) or "the sole shown in the images",
    }
    if info.get("kieu_giay_tay"):
        parts["type"] += f" ({translate(info['kieu_giay_tay'], dich)})"
    parts["shoe"] = cfg["shoe"].format(**parts)
    parts["shoe_short"] = f"{parts['color']} {translate(shoe_type, dich)}"
    return parts


def build_script(info: Dict, cfg: Dict) -> str:
    """Kịch bản Flow hàng tiệm, cùng khung [ASSETS] / [PROMPT] / [CONSTRAINTS] như kịch bản Omni."""
    p = describe_shoe(info, cfg)
    shots = " ".join(f"({i}) {shot.format(**p)}" for i, shot in enumerate(cfg["shots"], start=1))
    rules = "\n".join(f"- {rule}" for rule in cfg["fidelity_rules"])
    return f"""[ASSETS]:
- Product (Primary Subject - Input Image 1; other product images are extra angles of the same shoe): {p["shoe"]}. Must keep 100% visual fidelity to the product images; the product images are the only source of truth for shape and details, the text is only a hint.
- Model (Input Image 2): {cfg["model"]["nu" if is_female(info) else "nam"]} {cfg["outfit"]}

[PROMPT]:
- Setting: {cfg["setting"]}
- Visual: A 10-second vertical product film of the {p["shoe_short"]}. {cfg["framing"]} Shots in order: {shots}
- Camera: {cfg["camera"]}
- Audio: {cfg["audio"]}

[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic, no text/logos/watermarks.
{rules}
"""


def write_script(code: str, item_dir: str, cfg: Optional[Dict] = None, characters_dir: str = CHARACTERS_DIR) -> str:
    """Ghi <mã>.txt + chép ảnh người mẫu theo giới tính vào thư mục. 0 Gemini."""
    info = read_info(item_dir)
    cfg = cfg or load_config()
    path = os.path.join(item_dir, f"{code}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_script(info, cfg))
    prefix = "nu-" if is_female(info) else "nam-"
    chars = sorted(f for f in glob.glob(os.path.join(characters_dir, "*")) if os.path.basename(f).lower().startswith(prefix))
    have = [f for f in os.listdir(item_dir) if f.lower().startswith(("nu-", "nam-"))]
    if chars and not have:  # Nu-25t / Nam-25t (bản 25 tuổi đứng sau khi sắp xếp), giống kịch bản Omni
        shutil.copy2(chars[-1], os.path.join(item_dir, os.path.basename(chars[-1])))
    return path


def mark_downloaded(item_dir: str) -> None:
    info = read_info(item_dir)
    info["da_tai"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    write_info(item_dir, info)


def cleanup(assets_dir: str = ASSETS_DIR, downloads_dir: str = DOWNLOADS_DIR) -> List[str]:
    """Xoá thư mục hàng tiệm đã tải video và video đã rời ~/Downloads (HNC đã gom)."""
    removed = []
    if not os.path.isdir(assets_dir):
        return removed
    for code in sorted(os.listdir(assets_dir)):
        item_dir = os.path.join(assets_dir, code)
        info = read_info(item_dir) if os.path.isdir(item_dir) else {}
        if info.get("hang_tiem") and info.get("da_tai") and not os.path.exists(os.path.join(downloads_dir, f"{code}.mp4")):
            shutil.rmtree(item_dir, ignore_errors=True)
            removed.append(code)
    return removed


def main(argv: List[str]) -> int:
    codes = list(dict.fromkeys(c.strip().upper() for c in argv if c.strip() and not c.startswith("-")))
    for code in cleanup():
        print(f"🧹 Đã dọn Product_Assets/{code}/ (video đã được HNC gom).")
    if not codes:
        print(__doc__)
        return 1
    rows = read_sanpham(codes)
    ok = []
    for code in codes:
        row = rows.get(code)
        if not row:
            print(f"❌ {code}: không có trong tab SANPHAM — bỏ qua.")
            continue
        item_dir = prepare(code, row)
        if item_dir:
            write_script(code, item_dir)
            ok.append(code)
            n_img = len([f for f in os.listdir(os.path.join(ASSETS_DIR, code)) if f.lower().endswith(IMAGE_EXTS)])
            print(f"✅ {code}: {row.get('product_name', '').strip()} — {n_img} ảnh")
        else:
            print(f"❌ {code}: chưa có ảnh (NAS HNC_Master / web / image_01… đều trống) — bỏ qua.")
    print(f"\n📦 Sẵn sàng {len(ok)}/{len(codes)} mã. Đã có kịch bản — mở Flow, bấm extension → Tạo video.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
