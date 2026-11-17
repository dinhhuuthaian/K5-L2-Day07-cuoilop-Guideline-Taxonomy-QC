"""Sửa kỹ thuật: lỗi làm tròn khiến consensus_draft.json có box vượt ảnh 0.01 px (img_040).

qc_compare.py lấy trung bình box của 2 người rồi làm tròn x và w riêng lẻ, nên với hai box cùng
chạm mép ảnh (103 và 104 ở img_040) mép phải/dưới thành 960.01 / 640.01 > kích thước ảnh, và
build_final.py dừng với lỗi "bbox không hợp lệ hoặc vượt ảnh". Script này kéo mép box CHẠM MÉP ẢNH
trong một file nhãn vào trong 1 px (không đổi lớp, thuộc tính hay vật được gán). Cần chủ file đồng ý
và ghi vào QC_REPORT.

    python tools/fix_bbox_rounding.py submission/labels/104.json img_040.jpg
"""
import json
import sys
from pathlib import Path

path, image = Path(sys.argv[1]), sys.argv[2]
d = json.loads(path.read_text(encoding="utf-8"))
sizes = {i["id"]: (i["width"], i["height"]) for i in d["images"] if Path(i["file_name"]).name == image}
n = 0
for a in d["annotations"]:
    if a["image_id"] in sizes:
        w, h = sizes[a["image_id"]]
        x, y, bw, bh = a["bbox"]
        if x + bw > w - 0.5:
            a["bbox"][2] = round(w - 1 - x, 2); n += 1
        if y + bh > h - 0.5:
            a["bbox"][3] = round(h - 1 - y, 2); n += 1
path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
print(f"{path}: kéo {n} mép box chạm biên ảnh {image} vào trong 1 px.")
