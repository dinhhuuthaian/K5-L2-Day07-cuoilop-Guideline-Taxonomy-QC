# Báo cáo QC — Nhóm 101 · 102 · 103 · 104 (Day 07)

## 1. Mục đích, dữ liệu và phiên bản

- Mục đích và giới hạn sử dụng: Thực hành đặc tả và QC nhãn bounding box 2D cho người và phương tiện giao thông (9 lớp). Lô 40 ảnh được tuyển chọn để luyện ca biên (tượng, đồ chơi, phản chiếu, đám đông, xe chở xe), không đại diện cho dữ liệu vận hành; không dùng để huấn luyện hay đánh giá mô hình thật khi lô còn ở trạng thái Hold.
- Nguồn và phép sử dụng dữ liệu: 40 ảnh Wikimedia Commons, giấy phép CC BY / CC BY-SA / CC0 / public domain theo `data/ATTRIBUTION.csv`; chia sẻ lại phải giữ ghi công, ảnh CC BY-SA phải chia sẻ tương tự. Không sửa, đổi tên hay thêm bớt ảnh.
- Manifest và checksum nhãn cuối: `submission/qc/batch_manifest.json`; `submission/qc/labels_calibrated.json` SHA-256 `07be474372e80c62690a9eaf52d66fecb30d5f5a9d608e066481eec29b99692a` (40 ảnh, 477 annotation, 16 ignore_region).
- Guideline và taxonomy khi gán / khi bàn giao: Gán độc lập theo `guideline_v1.0_agreed.md` + `taxonomy.json` v1.0 (9 lớp, thêm `bus`, `three_wheeler`, `bicycle` so với v0). Bàn giao theo `guideline_v1.1_calibrated.md`, thay đổi loại semantic (`guideline_change.json`): thêm R-16 (cách ước lượng occluded_level), R-17 (người chỉ lộ mũ), sửa R-08/R-09 (đo vật nhỏ, phạm vi ignore), làm rõ R-01/R-10. Taxonomy giữ nguyên v1.0, không cần mapping.

## 2. Phân công và đồng thuận trước calibration

- Lượt hoàn thành / được giao: 80/80 lượt (40 ảnh × 2 người, mỗi thành viên 20 ảnh theo `assignment.csv`, seed 42). 4 file `submission/labels/10x.json` hợp lệ theo `validate_labels.py --all`.
- Số cặp box ghép, IoU TB, đồng thuận lớp và mẫu số: Mẫu số 296 cặp box ghép 1-1 (IoU ≥ 0.5, không phân biệt lớp) trên 40 ảnh. IoU TB 0.825 (ngưỡng 0.85, chưa đạt); cùng lớp 93.2% (ngưỡng 95%, chưa đạt); cùng occluded_level 51.0%; cùng truncated 92.9%. Chỉ cặp 102|103 đạt (IoU 0.856, lớp 100%). Box dưới ngưỡng IoU: 128.
- Box chưa ghép, loại do ignore, bất đồng vùng ignore: Chưa ghép 91 (người A) / 122 (người B); loại do ignore 0; bất đồng ignore 76 ca, tập trung img_011 (20), img_019 (13), img_021 (10). Tổng 544 ca trên 37 ảnh: bỏ sót/thừa 164, sai thuộc tính 152, IoU thấp 128, ignore 76, sai lớp 20, can_review 4.
- Ca hai người có thể cùng sai sau khi đối chiếu tham chiếu: Chưa nhận được ca tham chiếu của coach nên chưa đối chiếu được. Cơ chế đã xác định: nếu hai người cùng phủ `ignore_region` lên vật cao ≥ 20 px (trái R-08), hoặc cùng gán cùng một lớp sai, cặp đó không sinh ca nào trong `calibration_candidates.csv`. Vì vậy các quyết định R-16 và R-08/R-09 đặt phạm vi `lo` (rà cả 40 ảnh), không chỉ ảnh bị flag.

## 3. Calibration và kiểm lại

- Ca đã xử lý, rule ID, bản sửa và người xác nhận: 544/544 ca có một dòng trong `submission/qc/calibration_decisions.csv` (người chốt 101), gom theo 9 nhóm trong `tools/decision_groups.json`: K1 occluded_level 145 ca (R-16, lo); K2 truncated 7 (R-10); K3 IoU thấp 128 (R-01); K4 bỏ sót/thừa 139 (R-08/R-09); K5 đồ chơi img_038 25 (R-06, một người lệch); K6 ignore 76 (R-08/R-09, lo); K7 sai lớp 21 (mục 2.1, lớp do nhóm chốt trong `sai_lop_review.csv`); K8 người chỉ lộ mũ 2 (R-17); K9 hàng trên tuk-tuk 1 (R-05). Tổng 221 dòng phạm vi lo, 323 dòng phạm vi ảnh. Cột kiem_lai ghi 102 xác nhận trên `duyet_nhan_cuoi.html`.
- Tác động v1.1 lên nhãn và ảnh: Phạm vi cả lô 40 ảnh. Nhãn sửa bằng script có hỗ trợ AI (coach cho phép ở bước calibration): `tools/apply_calibration.py`, nhật ký từng thay đổi trong `tools/apply_calibration_report.csv`. Kết quả: xoá 25 box đồ chơi img_038; đổi lớp 21 ca (C302 xích lô → bicycle theo D3 của v1.0); xoá 21 box trùng sau khi xem từng cặp; truncated 7 ca chấm lại bằng mắt; 145 ca occluded_level chọn giá trị người gán gần ước lượng hình học R-16; box < 20 px thành ignore. Giới hạn: box K3 còn là trung bình hai người, occluded_level phân xử bằng hình học, chưa duyệt bằng mắt — lý do lô ở trạng thái Hold.
- Tham chiếu bằng chứng khi Rework: Chưa mở vòng Rework. Sự cố kỹ thuật đã xử lý trước vòng 1: (a) `qc_compare.py` làm tròn x và w riêng nên box trung bình ở img_040 vượt ảnh 0.01 px và `build_final.py` dừng; đã kéo 3 mép box chạm biên trong `104.json` vào 1 px (`tools/fix_bbox_rounding.py`, 104 đồng ý), không đổi lớp/thuộc tính; (b) IAA chạy trên Windows ghi đường dẫn `\`, đã chạy lại trên Linux, bảng cũ lưu ở `submission/qc/old_windows/`; (c) `103.json` bị sửa sau khi khóa (commit 528d715), đã khôi phục bản đã khóa (commit c49515b); 3 vật 103 thêm (img_031, img_034) chuyển thành nghi vấn bỏ sót cho vòng duyệt.

## 4. Kết quả duyệt

- Vòng QC: 1
- Người review và ngày: Chưa có người duyệt bằng mắt hoàn tất; phiếu `reviews/round-01/qc_review.csv` để trống, ngày 2026-11-17.
- Đã duyệt / cả lô: 0/40 ảnh (chế độ full, duyệt toàn lô).
- Ảnh lỗi / ảnh đã duyệt: 0/0 (N/A) — chưa có ảnh nào được duyệt.
- Annotation đối tượng hiện có bị lỗi / annotation đối tượng đã duyệt: 0/0 (N/A).
- Vật bỏ sót, ảnh và vùng: Chưa ghi trên phiếu. Nghi vấn từ kiểm bằng script: img_031 xe máy x≈383–403, y≈364–389; img_034 xe đạp x≈147–169, y≈250–287 và người x≈158–178, y≈231–274.
- Ca khó / phần còn lại, lỗi lặp và ví dụ: Kiểm bằng script (`goi_y_kiem_bang_script.csv`) đánh dấu 431 nghi vấn trên 34 ảnh để người duyệt xác nhận: occluded_level chọn bằng hình học 145, box trung bình chưa khít 128 (ví dụ img_001 hai box person IoU 0.63–0.70), box chỉ một người vẽ 118 (ví dụ img_021 đoàn xe máy), lớp đã chốt 20, box sát ngưỡng 20 px 17, bỏ sót 3. Chưa xác nhận được lỗi lặp vì chưa có phiếu.
- Một lỗi máy chặn được và một lỗi cần người đọc ảnh: Máy chặn được: box trung bình vượt kích thước ảnh 0.01 px ở img_040 (`build_final.py` báo "bbox không hợp lệ hoặc vượt ảnh"). Cần người đọc ảnh: 25 box `motorcycle` 104 gán cho ô tô đồ chơi ở img_038 hợp lệ về cấu trúc COCO nhưng sai R-06 — script chỉ thấy là ca "bỏ sót/thừa", người xem ảnh mới biết đó là đồ chơi.

## 5. Quyết định bàn giao

- Quyết định: Hold
- Lý do, người nhận và phạm vi sử dụng: `qc_report.py --round 1` trả về HOLD vì 0/40 ảnh được duyệt bằng mắt; nhãn calibration được sửa bằng script có AI hỗ trợ nên bắt buộc phải có người duyệt độc lập trước khi Release. Chỉ dùng nội bộ cho bài thực hành và coach chấm; không bàn giao cho huấn luyện.
- Nếu còn việc: (1) 101, 103, 104 duyệt mỗi người khoảng 13 ảnh trong `work/review/round-01/`, đối chiếu `goi_y_kiem_bang_script.csv`, điền `qc_review.csv` vòng 1 rồi chạy lại `qc_report.py --round 1`; (2) nếu tỉ lệ ảnh lỗi > 2% hoặc có lỗi lặp → Rework: thêm ca Q01… vào quyết định, sửa nhãn, `build_final.py`, mở `--round 2` và giữ vòng 1; (3) đối chiếu ca tham chiếu của coach để tìm ca hai người cùng sai.
- Kiểm ngược từ báo cáo tới ảnh, rule và nhãn: Ca C302 — `calibration_candidates.csv` (img_023, 102 gán three_wheeler, 104 gán bicycle) → `sai_lop_review.csv` lop_chot bicycle → `calibration_decisions.csv` dòng C302 (K7, rule 2.1 / D3 v1.0: xích lô không động cơ = bicycle, phạm vi ảnh, chốt 101) → `labels_calibrated.csv` img_023 box [570.06, 185.81, 226.57, 340.12] lớp bicycle, nguồn calibration. Kết quả: khớp.
