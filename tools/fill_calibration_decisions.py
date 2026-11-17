"""Điền submission/qc/calibration_decisions.csv từ các quyết định theo kiểu lỗi.

Không sửa script gốc của lab. Chạy từ thư mục gốc repo, SAU khi:
  1. python scripts/qc_compare.py
  2. python scripts/build_final.py   (lần đầu: sinh mẫu calibration_decisions.csv)

Lần chạy đầu sinh submission/qc/sai_lop_review.csv. Nhóm mở ảnh chồng nhãn (work/viz/),
điền cột lop_chot cho từng ca, rồi chạy lại:

  python tools/fill_calibration_decisions.py --nguoi-chot 104 --kiem-lai "103: đã kiểm trên work/viz, đạt"

Ca nào chưa có lop_chot sẽ để trống quyet_dinh để build_final.py chặn lại.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "submission" / "qc"
CANDIDATES = QC / "calibration_candidates.csv"
DECISIONS = QC / "calibration_decisions.csv"
REVIEW = QC / "sai_lop_review.csv"
GROUPS = Path(__file__).with_name("decision_groups.json")
COLUMNS = ["case_id", "image", "quyet_dinh", "quy_tac_ghi_vao_guideline", "phien_ban_guideline",
           "nguoi_chot", "phieu_sua", "kiem_lai", "pham_vi"]
REVIEW_COLUMNS = ["case_id", "image", "annotators", "class_a", "class_b", "box_a", "box_b",
                  "goi_y_theo_v1.0", "lop_chot", "ghi_chu"]
CLASSES = {"car", "truck", "van", "bus", "motorcycle", "three_wheeler", "bicycle", "person"}

# Gợi ý chỉ lấy từ ca đã ghi rõ trong bảng Ca khó của v1.0; nhóm vẫn phải xem ảnh và tự điền lop_chot.
HINTS = {
    "img_012.jpg": "truck nếu là bán tải (v1.0: img_012 → truck)",
    "img_022.jpg": "motorcycle nếu là mô tô sidecar (v1.0 R-02)",
    "img_023.jpg": "bicycle nếu là xích lô (v1.0: img_023 → bicycle)",
    "img_040.jpg": "three_wheeler nếu là tuk-tuk (v1.0: img_040)",
    "img_016.jpg": "three_wheeler nếu là tuk-tuk; van nếu là xe thân hộp (v1.0: img_016)",
}


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def group_of(case: dict) -> str:
    kind, image, note = case["issue_type"], case["image"], case["ghi_chu_tu_dong"]
    cls = case["class_a"] or case["class_b"]
    if kind == "sai_thuoc_tinh":
        return "K2" if note.startswith("truncated") else "K1"
    if kind == "iou_thap":
        return "K3"
    if kind == "bo_sot_thua":
        return "K5" if image == "img_038.jpg" else "K4"
    if kind == "bat_dong_ignore":
        return "K6"
    if kind == "sai_lop":
        return "K7"
    if kind == "co_can_review":
        if cls == "person":
            return "K8"
        if cls in {"three_wheeler", "truck"}:
            return "K9"
        return "K7"
    sys.exit(f"Kiểu lỗi chưa có nhóm: {kind} ({case['case_id']}). Thêm vào decision_groups.json.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nguoi-chot", required=True, help="Mã 3 chữ số người chốt quyết định.")
    ap.add_argument("--kiem-lai", required=True,
                    help='Ai kiểm lại và kết quả THẬT, ví dụ "103: đã kiểm trên work/viz, đạt".')
    args = ap.parse_args()
    if not (args.nguoi_chot.isdigit() and len(args.nguoi_chot) == 3):
        sys.exit("--nguoi-chot phải là mã 3 chữ số.")
    if not DECISIONS.is_file():
        sys.exit("Chưa có calibration_decisions.csv. Chạy python scripts/build_final.py trước để sinh mẫu.")

    cfg = json.loads(GROUPS.read_text(encoding="utf-8"))
    groups, version = cfg["groups"], cfg["phien_ban_guideline"]
    candidates = {c["case_id"]: c for c in read(CANDIDATES)}
    template = read(DECISIONS)
    if {r["case_id"] for r in template} != set(candidates):
        sys.exit("Bảng quyết định không khớp calibration_candidates.csv (IAA đã đổi?). "
                 "Lưu bản cũ ra chỗ khác, xoá rồi chạy lại build_final.py.")

    need_review = [c for c in candidates.values() if group_of(c) == "K7"]
    if not REVIEW.is_file():
        write(REVIEW, REVIEW_COLUMNS, [
            {**c, "goi_y_theo_v1.0": HINTS.get(c["image"], ""), "lop_chot": "", "ghi_chu": ""}
            for c in need_review
        ])
        print(f"Đã tạo {REVIEW.relative_to(ROOT)} ({len(need_review)} ca). "
              "Nhóm xem ảnh, điền lop_chot rồi chạy lại lệnh này.")
    chosen = {}
    for r in read(REVIEW):
        lop = (r.get("lop_chot") or "").strip()
        if lop:
            if lop not in CLASSES:
                sys.exit(f"{r['case_id']}: lop_chot '{lop}' không có trong taxonomy.")
            chosen[r["case_id"]] = lop

    rows, counts, pending = [], {}, []
    for t in template:
        case = candidates[t["case_id"]]
        gid = group_of(case)
        g = groups[gid]
        counts[gid] = counts.get(gid, 0) + 1
        boxes = " / ".join(b for b in (case["box_a"], case["box_b"]) if b)
        row = {"case_id": case["case_id"], "image": case["image"], "pham_vi": g["pham_vi"]}
        if g.get("can_review_sheet") and case["case_id"] not in chosen:
            pending.append(case["case_id"])
            rows.append(row)
            continue
        lop = chosen.get(case["case_id"], "")
        row.update({
            "quyet_dinh": f"[{gid}] " + g["quyet_dinh"].format(lop_chot=lop),
            "quy_tac_ghi_vao_guideline": g["quy_tac"],
            "phien_ban_guideline": version,
            "nguoi_chot": args.nguoi_chot,
            "phieu_sua": f"{case['image']} box {boxes} ({case['annotators']}): " + g["hanh_dong"].format(lop_chot=lop),
            "kiem_lai": args.kiem_lai,
        })
        rows.append(row)
    write(DECISIONS, COLUMNS, rows)

    print("Đã điền calibration_decisions.csv:")
    for gid in sorted(counts):
        print(f"  {gid} {groups[gid]['ten']}: {counts[gid]} ca (pham_vi={groups[gid]['pham_vi']})")
    if pending:
        print(f"\nCÒN {len(pending)} ca sai lớp chưa có lop_chot trong sai_lop_review.csv: {', '.join(pending)}")
    else:
        print("\nĐủ quyết định cho mọi ca. Bước tiếp: guideline v1.1 + guideline_change.json, "
              "rồi python scripts/prepare_calibration.py")


if __name__ == "__main__":
    main()
