#!/usr/bin/env bash
# Chạy lại toàn bộ Pha 5 từ nhãn độc lập tới nhãn cuối. Dùng: bash tools/run_calibration.sh <mã-chốt> "<kiểm lại>"
set -euo pipefail
CHOT=${1:?mã người chốt}; KIEM=${2:?nội dung kiểm lại}
python scripts/validate_labels.py --all | tail -1
python scripts/qc_compare.py | sed -n 1,2p
stamp=$(date +%H%M%S); mkdir -p submission/qc/old_$stamp
for f in calibration_decisions.csv calibration_context.json; do
  [ -f submission/qc/$f ] && mv submission/qc/$f submission/qc/old_$stamp/
done
rm -f submission/qc/labels_calibrated_*.json
python scripts/build_final.py >/dev/null 2>&1 || true          # sinh mẫu bảng quyết định
python tools/fill_calibration_decisions.py --nguoi-chot "$CHOT" --kiem-lai "$KIEM" | tail -1
OUT=$(python scripts/prepare_calibration.py | grep -o 'submission/qc/labels_calibrated_[0-9a-f]*\.json')
python tools/apply_calibration.py --out "$OUT"
python scripts/build_final.py
