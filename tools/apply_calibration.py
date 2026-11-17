"""Áp quyết định calibration v1.1 lên nhãn đồng thuận nháp (sửa nhãn có hỗ trợ AI, được coach cho phép).

Đầu vào : submission/qc/consensus_draft.json, calibration_candidates.csv, sai_lop_review.csv,
          submission/labels/<mã>.json (lấy vùng ignore của từng người)
Đầu ra  : đường dẫn --out (COCO 1.0, đủ 40 ảnh) + báo cáo thay đổi tools/apply_calibration_report.csv

Các bước (khớp nhóm K trong tools/decision_groups.json):
  K5  img_038: xoá mọi box (đồ chơi, R-06).
  K7  đổi lớp theo lop_chot; "giữ nguyên" -> tách thành 2 box riêng (R-02).
  K8  C058, C059: person, occluded_level=3 (R-17).
  K9  C461: box tuk-tuk đã chỉ ôm thân xe -> chỉ bỏ can_review (R-05).
  K2  truncated theo bảng TRUNCATED bên dưới (đã xem ảnh từng ca, R-10).
  R-08 box cao < 20 px -> đổi thành ignore_region.
  K6  thêm ignore_region của một người nếu không chứa tâm box nào cao >= 20 px; không thêm ở ảnh vật giả.
  K1  ca lệch occluded_level: chọn giá trị của một trong hai người gán gần nhất với ước lượng R-16
      bằng hình học (occlusion_r16); hoà thì chọn mức cao hơn (mục 2.2). Box hai người đã đồng ý giữ nguyên.
  K4  xoá box trùng theo DUPLICATE_DROP (đã xem ảnh từng cặp).
  K3/K4 còn lại: giữ box trung bình của nhóm đồng thuận / box của người duy nhất vẽ (chưa tinh chỉnh bằng mắt).
Cuối cùng bỏ can_review và needs_calibration.

Giới hạn: R-16 ở đây ước lượng bằng box (vật nào có mép dưới thấp hơn coi là ở gần camera hơn),
không phải bằng mắt; người kiểm lại vẫn phải duyệt ảnh trước khi ghi "đạt".
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "submission" / "qc"
LABELS = ROOT / "submission" / "labels"

FAKE_ONLY = {"img_017.jpg", "img_020.jpg", "img_027.jpg", "img_033.jpg", "img_038.jpg"}
TRUNCATED = {"C065": "yes", "C068": "yes", "C093": "yes", "C120": "yes",
             "C122": "yes", "C180": "no", "C381": "yes"}
OCCLUDED_3 = {"C058", "C059"}
# K4: cặp box do 2 người vẽ cho CÙNG một vật nhưng lệch nhau (IoU < 0.5 nên không ghép được).
# Đã xem ảnh từng cặp; xoá box ghi ở đây, giữ box còn lại (ôm đủ phần nhìn thấy theo R-01,
# không trùm sang vật khác). Các cặp img_005 C051/C055, C052/C054, img_021 C234/C246,
# img_030 C362/C370 là hai vật khác nhau -> giữ cả hai.
DUPLICATE_DROP = {
    "C050": "trùm 2 người (giữ C054)", "C053": "trùm cả ô tô và đuôi van (giữ C056)",
    "C069": "thiếu chân (giữ C076)", "C098": "chỉ đuôi xe (giữ C108)", "C105": "trùm 2 xe (giữ C102)",
    "C148": "trùm xe đã có box C149 (giữ C146)", "C232": "chỉ nửa xe (giữ C244)",
    "C233": "chỉ đuôi xe (giữ C246)", "C235": "chỉ đuôi xe (giữ C248)", "C237": "giữ C255",
    "C256": "kéo lên cả người lái (giữ C239)", "C257": "kéo lên cả người lái (giữ C240)",
    "C241": "chỉ đuôi xe (giữ C247)", "C243": "thiếu chân (giữ C245)", "C309": "chỉ nửa xe (giữ C310)",
    "C319": "thiếu thân (giữ C321)", "C361": "chỉ đuôi xe (giữ C369)", "C442": "kéo lên cả người lái (giữ C451)",
    "C471": "chỉ một phần xe (giữ C473)", "C472": "chỉ một phần xe (giữ C473)", "C518": "thiếu thân (giữ C522)",
}
KEEP_BOTH = {"giu_ca_hai", "giữ nguyên", "giu nguyen", "giữ cả hai"}
TWO_WHEEL = {"motorcycle", "bicycle"}


def iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0, min(ax2, bx2) - max(a[0], b[0]))
    ih = max(0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union else 0.0


def inter_area(a, b):
    iw = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    ih = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return iw * ih


SHRINK, PART_THR = 0.15, 0.6  # box là hình chữ nhật rộng hơn vật thật: thu 15% mỗi cạnh trước khi tính che


def covered_fraction(part, occluders, step=3):
    """Tỉ lệ diện tích `part` nằm dưới hợp các box `occluders` (lấy mẫu lưới)."""
    occluders = [(o[0] + o[2] * SHRINK, o[1] + o[3] * SHRINK, o[2] * (1 - 2 * SHRINK), o[3] * (1 - 2 * SHRINK))
                 for o in occluders]
    x, y, w, h = part
    if w <= 0 or h <= 0:
        return 0.0
    nx, ny = max(1, int(w // step)), max(1, int(h // step))
    hit = 0
    for i in range(nx):
        px = x + (i + 0.5) * w / nx
        for j in range(ny):
            py = y + (j + 0.5) * h / ny
            if any(o[0] <= px <= o[0] + o[2] and o[1] <= py <= o[1] + o[3] for o in occluders):
                hit += 1
    return hit / (nx * ny)


def rider_pairs(objs):
    """Ghép người với xe 2 bánh họ đang lái/ngồi: người chồng lên xe và tâm ngang của người nằm trong xe."""
    pairs = set()
    for i, p in enumerate(objs):
        if p["cls"] != "person":
            continue
        pb = p["box"]
        cx = pb[0] + pb[2] / 2
        for j, v in enumerate(objs):
            vb = v["box"]
            if v["cls"] in TWO_WHEEL | {"three_wheeler"} and vb[0] <= cx <= vb[0] + vb[2] \
                    and inter_area(pb, vb) >= 0.2 * pb[2] * pb[3]:
                pairs.add((i, j))
                pairs.add((j, i))
    return pairs


def occlusion_r16(objs):
    """R-16: chia vật thành 4 phần (người: theo chiều cao; xe: theo chiều dài), đếm phần bị vật
    ở gần camera hơn che quá nửa. Không tính xe mình lái/người lái xe mình."""
    pairs = rider_pairs(objs)
    levels = []
    for i, o in enumerate(objs):
        x, y, w, h = o["box"]
        bottom = y + h
        occ = [p["box"] for j, p in enumerate(objs)
               if j != i and (i, j) not in pairs and p["box"][1] + p["box"][3] > bottom + 2]
        if o["cls"] == "person":
            parts = [(x, y + k * h / 4, w, h / 4) for k in range(4)]
        else:
            parts = [(x + k * w / 4, y, w / 4, h) for k in range(4)]
        n = sum(covered_fraction(p, occ) > PART_THR for p in parts)
        levels.append(str(min(3, n)))
    return levels


def load_coco(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    cats = {c["id"]: c["name"] for c in d["categories"]}
    names = {i["id"]: Path(i["file_name"]).name for i in d["images"]}
    return d, cats, names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path, help="Đường dẫn COCO đầu ra (tên do prepare_calibration.py in ra).")
    args = ap.parse_args()

    draft, cats, names = load_coco(QC / "consensus_draft.json")
    cat_id = {v: k for k, v in cats.items()}
    cand = {r["case_id"]: r for r in csv.DictReader(open(QC / "calibration_candidates.csv", encoding="utf-8"))}
    review = {r["case_id"]: (r.get("lop_chot") or "").strip()
              for r in csv.DictReader(open(QC / "sai_lop_review.csv", encoding="utf-8"))}

    per_img = {names[i["id"]]: [] for i in draft["images"]}
    for a in draft["annotations"]:
        per_img[names[a["image_id"]]].append({
            "cls": cats[a["category_id"]], "box": [round(v, 2) for v in a["bbox"]],
            "occ": a["attributes"].get("occluded_level", "0"), "trunc": a["attributes"].get("truncated", "no"),
        })
    log = []

    def find(image, box, cls_any=None):
        best, bi = 0.0, None
        for k, o in enumerate(per_img[image]):
            if o["cls"] == "ignore_region":
                continue
            v = iou(o["box"], box)
            if v > best:
                best, bi = v, k
        return bi if best >= 0.5 else None

    def case_box(c):
        boxes = [json.loads(b) for b in (c["box_a"], c["box_b"]) if b]
        return [sum(b[k] for b in boxes) / len(boxes) for k in range(4)]

    # K5 + ảnh chỉ có vật giả
    for image in FAKE_ONLY:
        n = len(per_img[image])
        if n:
            log.append((image, "K5/R-06", f"xoá {n} box (vật không thật)"))
        per_img[image] = []

    # K7 đổi lớp / tách hai vật
    for cid, lop in review.items():
        c = cand[cid]
        k = find(c["image"], case_box(c))
        if k is None:
            log.append((c["image"], f"K7 {cid}", "không tìm thấy box trong nháp - bỏ qua"))
            continue
        o = per_img[c["image"]][k]
        if lop.lower() in KEEP_BOTH:
            del per_img[c["image"]][k]
            for b, cl in ((c["box_a"], c["class_a"]), (c["box_b"], c["class_b"])):
                if b and cl:
                    per_img[c["image"]].append({"cls": cl, "box": json.loads(b), "occ": o["occ"], "trunc": o["trunc"]})
            log.append((c["image"], f"K7 {cid}", f"tách thành 2 box {c['class_a']} + {c['class_b']}"))
        elif lop:
            log.append((c["image"], f"K7 {cid}", f"đổi lớp {o['cls']} -> {lop}"))
            o["cls"] = lop

    # K4 trùng box
    for cid, why in DUPLICATE_DROP.items():
        c = cand[cid]
        k = find(c["image"], case_box(c))
        if k is None:
            log.append((c["image"], f"K4 {cid}", "không tìm thấy box - bỏ qua"))
            continue
        del per_img[c["image"]][k]
        log.append((c["image"], f"K4 {cid}", f"xoá box trùng: {why}"))

    # K2 truncated
    for cid, val in TRUNCATED.items():
        c = cand[cid]
        k = find(c["image"], case_box(c))
        if k is not None:
            per_img[c["image"]][k]["trunc"] = val
            log.append((c["image"], f"K2 {cid}", f"truncated={val}"))

    # R-08: vật < 20 px -> ignore
    for image, objs in per_img.items():
        for o in objs:
            if o["cls"] != "ignore_region" and o["box"][3] < 20:
                log.append((image, "R-08", f"{o['cls']} cao {o['box'][3]:.0f}px -> ignore_region"))
                o["cls"] = "ignore_region"

    # K6: thêm vùng ignore của từng người nếu không chứa vật >= 20 px
    for path in sorted(LABELS.glob("[0-9][0-9][0-9].json")):
        d, cmap, nmap = load_coco(path)
        for a in d["annotations"]:
            image = nmap[a["image_id"]]
            if cmap[a["category_id"]] != "ignore_region" or image in FAKE_ONLY or image not in per_img:
                continue
            b = a["bbox"]
            objs = per_img[image]
            if any(o["cls"] == "ignore_region" and iou(o["box"], b) > 0.3 for o in objs):
                continue
            has_big = any(o["cls"] != "ignore_region" and o["box"][3] >= 20
                          and b[0] <= o["box"][0] + o["box"][2] / 2 <= b[0] + b[2]
                          and b[1] <= o["box"][1] + o["box"][3] / 2 <= b[1] + b[3] for o in objs)
            if not has_big:
                objs.append({"cls": "ignore_region", "box": b, "occ": "0", "trunc": "no"})
                log.append((image, f"K6 ({path.stem})", f"giữ vùng ignore {[round(v) for v in b]}"))
            else:
                log.append((image, f"K6 ({path.stem})", f"bỏ vùng ignore {[round(v) for v in b]} vì phủ vật >= 20px"))

    # K1: phân xử ca lệch occluded_level bằng R-16 hình học
    import re
    changed = Counter()
    geo_cache = {}
    for cid, c in cand.items():
        if c["issue_type"] != "sai_thuoc_tinh" or "occluded_level" not in c["ghi_chu_tu_dong"]:
            continue
        vals = re.findall(r"occluded_level: \d{3}=(\d) vs \d{3}=(\d)", c["ghi_chu_tu_dong"])
        if not vals:
            continue
        a, b = vals[0]
        image = c["image"]
        k = find(image, case_box(c))
        if k is None:
            log.append((image, f"K1 {cid}", "không tìm thấy box - bỏ qua"))
            continue
        if image not in geo_cache:
            real = [o for o in per_img[image] if o["cls"] != "ignore_region"]
            geo_cache[image] = {id(o): lv for o, lv in zip(real, occlusion_r16(real))}
        o = per_img[image][k]
        geo = int(geo_cache[image].get(id(o), o["occ"]))
        pick = sorted((a, b), key=lambda v: (abs(int(v) - geo), -int(v)))[0]
        changed[(o["occ"], pick)] += 1
        log.append((image, f"K1 {cid}", f"occluded_level {a} vs {b}, R-16 hình học = {geo} -> chọn {pick}"))
        o["occ"] = pick
    for cid in OCCLUDED_3:
        c = cand[cid]
        k = find(c["image"], case_box(c))
        if k is not None:
            per_img[c["image"]][k]["occ"] = "3"
            log.append((c["image"], f"K8 {cid}", "person occluded_level=3 (R-17)"))
    log.append(("(cả lô)", "K1/R-16", "nháp -> chốt: " + ", ".join(f"{a}->{b}: {n}" for (a, b), n in sorted(changed.items()))))

    # ghi COCO
    images, anns = [], []
    for iid, image in enumerate(sorted(per_img), 1):
        w, h = next((i["width"], i["height"]) for i in draft["images"] if names[i["id"]] == image)
        images.append({"id": iid, "file_name": image, "width": w, "height": h})
        for o in per_img[image]:
            x, y, bw, bh = o["box"]
            x0, y0 = max(0.0, x), max(0.0, y)                       # cắt box về trong khung ảnh
            bw, bh = round(min(w, x + bw) - x0, 2), round(min(h, y + bh) - y0, 2)
            x, y = round(x0, 2), round(y0, 2)
            if bw <= 1 or bh <= 1:
                continue
            attrs = {} if o["cls"] == "ignore_region" else {
                "occluded_level": o["occ"], "truncated": o["trunc"], "can_review": False}
            anns.append({"id": len(anns) + 1, "image_id": iid, "category_id": cat_id[o["cls"]],
                         "bbox": [x, y, bw, bh], "area": round(bw * bh, 2), "iscrowd": 0,
                         "segmentation": [], "attributes": attrs})
    out = {"info": {"description": "Nhãn sau calibration v1.1 (áp quyết định bằng tools/apply_calibration.py)"},
           "licenses": draft.get("licenses", []), "categories": draft["categories"],
           "images": images, "annotations": anns}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rep = ROOT / "tools" / "apply_calibration_report.csv"
    with rep.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["image", "quyet_dinh", "thay_doi"])
        wr.writerows(log)
    print(f"Đã ghi {args.out} ({len(images)} ảnh, {len(anns)} annotation). Báo cáo: {rep.relative_to(ROOT)}")
    print(f"Ca lệch occluded_level đã phân xử: {sum(changed.values())}")


if __name__ == "__main__":
    main()
