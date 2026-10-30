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

Kiểu dựng (anh Kha 30/10): mặc định "liền" = 1 cảnh liền 10 giây (máy lùi dần từ giày ra người mẫu),
tối đa 6 ảnh giày đủ góc (thẳng → 3/4 → góc khác → đế, xem pick_lien_images) + ảnh người mẫu cắt từ thắt lưng trở lên.

--4-canh = kiểu 4 cảnh + ảnh người mẫu. Bối cảnh xoay vòng theo loại giày (config/hang_tiem.json "boi_canh").

Kiểu chuyển động (kiểu liền) xoay vòng cùng bối cảnh; --chuyen-dong=<tên> chọn tay 1 kiểu (kể cả mang_giay đang tắt).

Dùng: python scripts/hang_tiem.py [--4-canh | --chuyen-dong=<tên>] <mã> [<mã> …]    (HangTiem.command hỏi mã + kiểu rồi chạy lệnh này)
"""

import glob
import json
import os
import re
import shutil
import subprocess
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


def read_sanpham_values() -> List[List[str]]:
    from sheet_sync import get_gspread_client
    gc = get_gspread_client()
    if not gc:
        raise RuntimeError("Không kết nối được Google Sheets (Service Account).")
    return gc.open_by_key(SANPHAM_SHEET_ID).worksheet(SANPHAM_TAB).get_all_values()


def read_sanpham(codes: List[str]) -> Dict[str, Dict[str, str]]:
    return sanpham_rows(read_sanpham_values(), codes)


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


def video_name(code: str, media_dir: str = HNC_MEDIA_DIR, downloads_dir: str = DOWNLOADS_DIR) -> str:
    """Tên file video đầu ra (anh Kha 30/10): số = số video mã đang có (video trong NAS HNC_Master/<mã>/ + ~/Downloads)
    + 1, luôn có hậu tố (anh Kha 30/10): <MÃ>_1.mp4, <MÃ>_2.mp4… (<MÃ>.mp4 cũ tính là 1 video). Trùng tên có sẵn → tăng số.
    Mỗi mã chỉ 1 thư mục Product_Assets nên không có mục chờ khác cùng mã."""
    pattern = re.compile(rf"^{re.escape(code)}(?:_(\d+))?\.(mp4|mov)$", re.IGNORECASE)
    names = set()
    for folder in (os.path.join(media_dir, code), downloads_dir):
        try:
            names |= {f.lower() for f in os.listdir(folder) if pattern.match(f)}
        except OSError:
            pass
    n = len(names) + 1
    while True:
        name = f"{code}_{n}.mp4"
        if name.lower() not in names and name.lower().replace(".mp4", ".mov") not in names:
            return name
        n += 1


def output_name(info: Dict, item_id: str) -> str:
    return info.get("ten_video") or f"{item_id}.mp4"


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
    info = build_info(code, row, read_info(item_dir))
    info["ten_video"] = video_name(code, media_dir, downloads_dir)
    write_info(item_dir, info)
    return item_dir


SCENE_STATE = os.path.join(PROJECT_DIR, "data", ".hang_tiem_boi_canh.json")  # chỉ số bối cảnh kế tiếp theo nhóm
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "hang_tiem.json")
CHARACTERS_DIR = os.path.join(PROJECT_DIR, "characters")
# thứ tự = ưu tiên: kiểu cụ thể ("xỏ chân") thắng "giày tây" chung (giày tây → "shoes", không ghi dress shoes vì Flow vẽ giày buộc dây)
SHOE_TYPES = ("xỏ chân", "giày lười", "giày mọi", "cột dây", "giày thể thao", "giày sandal", "giày cao gót", "giày búp bê",
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


def shoe_kind(info: Dict) -> str:
    name = info.get("productName", "").lower()
    return next((t for t in SHOE_TYPES if t in name), "giày")


def scene_group(info: Dict, cfg: Dict) -> str:
    bc = cfg["boi_canh"]
    group = bc["theo_loai"].get(shoe_kind(info))
    return group or (bc["giay_nu"] if is_female(info) else bc["mac_dinh"])


def pick_scene(info: Dict, cfg: Dict, state_path: Optional[str] = None) -> str:
    """Xoay vòng bối cảnh trong nhóm của mã (2 mã liền nhau không trùng); chỉ số kế tiếp lưu ở file trạng thái nhỏ."""
    state_path = state_path or SCENE_STATE
    group = scene_group(info, cfg)
    scenes = cfg["boi_canh"]["nhom"][group]
    state = _load_state(state_path)
    i = int(state.get(group, 0)) % len(scenes)
    state[group] = (i + 1) % len(scenes)
    _save_state(state, state_path)
    return scenes[i]["ten"]


def _load_state(state_path: str) -> Dict:
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(state: Dict, state_path: str) -> None:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def motions_for(info: Dict, cfg: Dict) -> List[str]:
    """Kiểu chuyển động xoay vòng tự động cho mã (bỏ kiểu "bat": false; mang_giay chỉ cho giày xỏ chân / lười…)."""
    kind = shoe_kind(info)
    return [name for name, m in cfg["lien"]["chuyen_dong"].items()
            if not name.startswith("_") and m.get("bat", True) and (not m.get("chi_cho") or kind in m["chi_cho"])]


def combos_for(info: Dict, cfg: Dict) -> List[tuple]:
    scenes = [sc["ten"] for sc in cfg["boi_canh"]["nhom"][scene_group(info, cfg)]]
    return [(m, sc) for m in motions_for(info, cfg) for sc in scenes]


def pick_combo(info: Dict, cfg: Dict, used=(), state_path: Optional[str] = None) -> Optional[tuple]:
    """(kiểu chuyển động, bối cảnh) chưa dùng cho mã này; kiểu và bối cảnh cùng xoay vòng (file trạng thái) để 2 mã
    liền nhau khác nhau. Hết tổ hợp → None."""
    state_path = state_path or SCENE_STATE
    group = scene_group(info, cfg)
    motions = motions_for(info, cfg)
    scenes = [sc["ten"] for sc in cfg["boi_canh"]["nhom"][group]]
    state = _load_state(state_path)
    mi, si = int(state.get("chuyen_dong", 0)), int(state.get(group, 0))
    used = {tuple(u) for u in used}
    for dm in range(len(motions)):
        for ds in range(len(scenes)):
            combo = (motions[(mi + dm) % len(motions)], scenes[(si + ds) % len(scenes)])
            if combo not in used:
                state["chuyen_dong"] = (mi + dm + 1) % len(motions)
                state[group] = (si + ds + 1) % len(scenes)
                _save_state(state, state_path)
                return combo
    return None


def scene_for(info: Dict, cfg: Dict) -> Dict[str, str]:
    """Bối cảnh đã chọn (info["boi_canh"]); chưa chọn thì cảnh đầu của nhóm."""
    scenes = cfg["boi_canh"]["nhom"][scene_group(info, cfg)]
    return next((sc for sc in scenes if sc["ten"] == info.get("boi_canh")), scenes[0])


def describe_shoe(info: Dict, cfg: Dict) -> Dict[str, str]:
    dich = cfg.get("dich", {})
    name = info.get("productName", "").lower()
    shoe_type = shoe_kind(info)
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
        # cột kieu_giay_tay: "Derby (buộc dây hở), đục lỗ (brogue)" → "Derby, brogue"
        styles = [translate(k, dich) for k in info["kieu_giay_tay"].split(",") if k.strip()]
        styles = [k for k in styles if k.lower() not in parts["type"].lower()]  # bỏ lặp: "slip-on loafers (slip-on)"
        if styles:
            parts["type"] += f" ({', '.join(styles)})"
    parts["shoe"] = cfg["shoe"].format(**parts)
    parts["shoe_short"] = f"{parts['color']} {translate(shoe_type, dich)}"
    return parts


def image_shape(path: str, width: int = 160) -> tuple:
    """(rộng/cao, độ đặc) của khung bao quanh giày: ffmpeg thu ảnh xám nhỏ, điểm khác màu nền (góc ảnh) > 35 là giày."""
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", path, "-vf", f"scale={width}:-2,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    height = len(raw) // width
    bg = sorted([raw[0], raw[width - 1], raw[(height - 1) * width], raw[height * width - 1]])[1]
    xs, ys = [], []
    for i, v in enumerate(raw[:height * width]):
        if abs(v - bg) > 35:
            xs.append(i % width)
            ys.append(i // width)
    if not xs:
        return 1.0, 1.0
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    return bw / bh, len(xs) / (bw * bh)


def _number_order(path: str) -> list:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", os.path.basename(path).lower())]


LIEN_MAX_SHOES = 6  # Flow nhận tối đa 7 ảnh (flow_helper.MAX_FLOW_IMAGES) = 6 ảnh giày + 1 ảnh người mẫu


def pick_lien_images(item_dir: str, shape=image_shape, max_shoes: int = LIEN_MAX_SHOES) -> List[str]:
    """Ảnh giày cho kiểu liền, đủ góc (anh Kha 30/10): cặp nhìn thẳng → chéo 3/4 → các góc còn lại (theo số) → đế cuối.
    - đế = ảnh số cuối (ảnh tiệm luôn chụp đế sau cùng: JH8918N_9, 32837N web 8);
    - nhìn thẳng = khung giày cao hơn rộng nhất (rộng/cao < 1,1);
    - chéo 3/4 = trong ảnh rộng/cao 1,3–1,9 lấy ảnh độ đặc thấp nhất (1 chiếc đứng chéo);
    - quá max_shoes thì bỏ dần ảnh ở giữa có tỉ lệ khung gần ảnh khác nhất (góc gần trùng)."""
    images = sorted((f for f in glob.glob(os.path.join(item_dir, "*"))
                     if f.lower().endswith(IMAGE_EXTS) and not os.path.basename(f).lower().startswith(("nu-", "nam-"))),
                    key=_number_order)
    if len(images) <= 2:
        return [os.path.basename(f) for f in images]
    sole, rest = images[-1], images[:-1]
    shapes = {f: shape(f) for f in rest}
    head = []
    front = min(rest, key=lambda f: shapes[f][0])
    if shapes[front][0] < 1.1:
        head.append(front)
    three_q = [f for f in rest if f not in head and 1.3 <= shapes[f][0] <= 1.9]
    if three_q:
        head.append(min(three_q, key=lambda f: shapes[f][1]))
    middle = [f for f in rest if f not in head]
    while middle and len(head) + len(middle) + 1 > max_shoes:
        kept = head + middle
        middle.remove(min(middle, key=lambda f: min(abs(shapes[f][0] - shapes[g][0]) for g in kept if g != f)))
    return [os.path.basename(f) for f in head + middle + [sole]]


def crop_model_upper(src: str, item_dir: str, keep: float) -> str:
    """Bản cắt ảnh người mẫu từ thắt lưng trở lên (giữ `keep` phần trên, cả bề ngang) → <tên>_tren.jpg; ảnh gốc giữ nguyên.
    Ảnh characters/ là tờ 2 hình (chân dung + toàn thân, giày nâu); bỏ phần dưới để Flow không lấy giày của người mẫu."""
    out = os.path.join(item_dir, os.path.splitext(os.path.basename(src))[0] + "_tren.jpg")
    subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-i", src, "-vf", f"crop=iw:trunc(ih*{keep}/2)*2:0:0",
                    "-q:v", "3", out], check=True)
    return out


def build_script_lien(info: Dict, cfg: Dict) -> str:
    """Kiểu liền: 1 cảnh 10 giây, chỉ tả đúng kiểu giày + màu + chất liệu mặt, gọi ảnh theo thứ tự dán (ảnh giày trước, người mẫu sau cùng)."""
    p = describe_shoe(info, cfg)
    lien = cfg["lien"]
    scene = scene_for(info, cfg)
    motion = lien["chuyen_dong"].get(info.get("chuyen_dong") or "lui_ra") or lien["chuyen_dong"]["lui_ra"]
    if motion.get("prompt"):  # tu_nhien: 1 câu tiếng Việt ngắn, để tác nhân Flow tự dựng cảnh (anh Kha 30/10)
        return motion["prompt"].format(gioi="nữ" if is_female(info) else "nam", **scene) + "\n"
    camera = motion["camera"].format(walk=scene["walk"])
    giu_giay = motion.get("giu_giay") or lien.get("giu_giay", "")
    setting_line = motion.get("cau_boi_canh", "{setting}").format(setting=scene["setting"], walk=scene["walk"])
    lines = (line.format(**p, **scene, camera=camera, giu_giay=giu_giay, setting_line=setting_line, dang_chan=lien.get("dang_chan", ""),
                                 buoc_di=lien.get("buoc_di", "") if motion.get("co_buoc") else "", n=len(info.get("anh_lien") or []) or "",
                                 model_word="female" if is_female(info) else "male")
             for line in lien["prompt"])
    return "\n".join(line for line in lines if line.strip()) + "\n"  # kiểu không có câu bước đi → bỏ dòng trống


def popup_label(info: Dict, cfg: Optional[Dict] = None) -> str:
    """Nhãn cạnh mã trong popup: "JH8918N_2.mp4 · tien_vao · sảnh khách sạn" (4 cảnh: "… · 4 cảnh · …")."""
    cfg = cfg or load_config()
    scene = scene_for(info, cfg).get("nhan", "")
    if info.get("kieu") == "lien":
        name = info.get("chuyen_dong") or "lui_ra"
        kieu = cfg["lien"]["chuyen_dong"].get(name, {}).get("nhan", name)
    else:
        kieu = "4 cảnh"
    out = f"{info['ten_video']} · " if info.get("ten_video") else ""
    return f"{out}{kieu} · {scene}"


def build_script(info: Dict, cfg: Dict) -> str:
    """Kịch bản Flow hàng tiệm, cùng khung [ASSETS] / [PROMPT] / [CONSTRAINTS] như kịch bản Omni."""
    if info.get("kieu") == "lien":
        return build_script_lien(info, cfg)
    p = describe_shoe(info, cfg)
    scene = scene_for(info, cfg)
    shots = " ".join(f"({i}) {shot.format(**p)}" for i, shot in enumerate(cfg["shots"], start=1))
    rules = "\n".join(f"- {rule}" for rule in cfg["fidelity_rules"])
    return f"""[ASSETS]:
- Product (Primary Subject - Input Image 1; other product images are extra angles of the same shoe): {p["shoe"]}. Must keep 100% visual fidelity to the product images; the product images are the only source of truth for shape and details, the text is only a hint.
- Model (Input Image 2): {cfg["model"]["nu" if is_female(info) else "nam"]} {cfg["outfit"]}

[PROMPT]:
- Setting: {scene["setting"]}
- Visual: A 10-second vertical product film of the {p["shoe_short"]}. {cfg["framing"]} Shots in order: {shots}
- Camera: {cfg["camera"]}
- Audio: {cfg["audio"].format(**scene)}

[CONSTRAINTS]:
- 9:16 vertical, 10s, photorealistic, no text/logos/watermarks.
{rules}
"""


def write_script(code: str, item_dir: str, cfg: Optional[Dict] = None, characters_dir: str = CHARACTERS_DIR,
                 used=(), motion: Optional[str] = None) -> str:
    """Ghi <mã>.txt (bối cảnh xoay vòng theo loại giày) + ảnh người mẫu: kiểu liền = bản cắt thắt lưng trở lên + ảnh giày
    đủ góc; kiểu 4 cảnh = chép ảnh Nam- / Nu- theo giới tính. 0 Gemini."""
    info = read_info(item_dir)
    cfg = cfg or load_config()
    if info.get("kieu") == "lien":
        if motion:  # gọi tay 1 kiểu (kể cả kiểu tắt xoay vòng như mang_giay)
            info["chuyen_dong"], info["boi_canh"] = motion, pick_scene(info, cfg)
        else:
            combo = pick_combo(info, cfg, used) or pick_combo(info, cfg)  # hết tổ hợp mới (làm tay) → xoay lại từ đầu
            info["chuyen_dong"], info["boi_canh"] = combo
        info["anh_lien"] = pick_lien_images(item_dir)
    else:
        info.pop("chuyen_dong", None)
        info["boi_canh"] = pick_scene(info, cfg)
    write_info(item_dir, info)
    path = os.path.join(item_dir, f"{code}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_script(info, cfg))
    prefix = "nu-" if is_female(info) else "nam-"
    chars = sorted(f for f in glob.glob(os.path.join(characters_dir, "*")) if os.path.basename(f).lower().startswith(prefix))
    if info.get("kieu") == "lien":
        if chars:
            info["nguoi_mau_lien"] = os.path.basename(crop_model_upper(chars[-1], item_dir, cfg["lien"]["cat_nguoi_mau"]))
            write_info(item_dir, info)
        return path
    have = [f for f in os.listdir(item_dir) if f.lower().startswith(("nu-", "nam-")) and "_tren" not in f.lower()]
    if chars and not have:  # Nu-25t / Nam-25t (bản 25 tuổi đứng sau khi sắp xếp), giống kịch bản Omni
        shutil.copy2(chars[-1], os.path.join(item_dir, os.path.basename(chars[-1])))
    return path


SCRIPTS_MADE_DIR = os.path.join(PROJECT_DIR, "data", "kich_ban_da_tao")


def save_made_script(item_dir: str, out_dir: Optional[str] = None) -> Optional[str]:
    """Chép kịch bản của video vừa tải về data/kich_ban_da_tao/<tên video>.txt (kèm kiểu, bối cảnh, ngày) để so sau."""
    info = read_info(item_dir)
    code = info.get("itemId") or os.path.basename(item_dir)
    src = os.path.join(item_dir, f"{code}.txt")
    if not os.path.isfile(src):
        return None
    out_dir = out_dir or SCRIPTS_MADE_DIR
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, os.path.splitext(output_name(info, code))[0] + ".txt")
    head = (f"# {output_name(info, code)} · kiểu {info.get('kieu')} · {info.get('chuyen_dong', '')} · "
            f"bối cảnh {info.get('boi_canh', '')} · tải {datetime.now():%Y-%m-%d %H:%M}\n")
    with open(src, "r", encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as g:
        g.write(head + f.read())
    return dst


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
        if info.get("hang_tiem") and info.get("da_tai") and not os.path.exists(os.path.join(downloads_dir, output_name(info, code))):
            shutil.rmtree(item_dir, ignore_errors=True)
            removed.append(code)
    return removed


def make_item(code: str, row: Dict[str, str], lien: bool = True, extra: Optional[Dict] = None, used=(),
              motion: Optional[str] = None, **prepare_kw) -> Optional[str]:
    """Ảnh + info.json + kịch bản cho 1 mã (dùng chung cho HangTiem.command và hàng chờ tự động). None = không có ảnh."""
    item_dir = prepare(code, row, **prepare_kw)
    if not item_dir:
        return None
    info = read_info(item_dir)
    info["kieu"] = "lien" if lien else "4_canh"
    info.pop("anh_lien", None)
    info.pop("nguoi_mau_lien", None)
    info.update(extra or {})
    write_info(item_dir, info)
    write_script(code, item_dir, used=used, motion=motion)
    return item_dir


def main(argv: List[str]) -> int:
    codes = list(dict.fromkeys(c.strip().upper() for c in argv if c.strip() and not c.startswith("-")))
    lien = "--4-canh" not in argv  # kiểu liền là mặc định từ 30/10 (anh Kha); --lien vẫn nhận
    motion = next((a.split("=", 1)[1] for a in argv if a.startswith("--chuyen-dong=")), None)
    motions = [k for k in load_config()["lien"]["chuyen_dong"] if not k.startswith("_")]
    if motion and motion not in motions:
        print(f"❌ Không có kiểu {motion}. Có: {', '.join(motions)}")
        return 1
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
        item_dir = make_item(code, row, lien, motion=motion)
        if item_dir:
            ok.append(code)
            n_img = len([f for f in os.listdir(os.path.join(ASSETS_DIR, code)) if f.lower().endswith(IMAGE_EXTS)])
            chosen = read_info(item_dir).get("anh_lien")
            print(f"✅ {code}: {row.get('product_name', '').strip()} — "
                  + (f"{popup_label(read_info(item_dir), load_config())}, {len(chosen)} ảnh giày + người mẫu"
                     if chosen else f"4 cảnh, {n_img} ảnh"))
        else:
            print(f"❌ {code}: chưa có ảnh (NAS HNC_Master / web / image_01… đều trống) — bỏ qua.")
    print(f"\n📦 Sẵn sàng {len(ok)}/{len(codes)} mã. Đã có kịch bản — mở Flow, bấm extension → Tạo video.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
