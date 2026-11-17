# Tóm tắt IAA (taxonomy v1.0)

- Ảnh được so sánh (có >=2 người gán): **40**; số người gán: 4
- Lượt gán đủ **80/80**.
- IoU trung bình và % cùng lớp **chỉ tính trên các cặp box đã ghép** (IoU >= 0.5, ghép 1-1 không phân biệt lớp). Box chưa ghép được thống kê riêng ở cột bỏ sót/thừa.
- Mẫu số: 296 cặp box ghép (tổng mọi cặp người gán, ảnh chung).

| Cặp | Ảnh | Cặp box ghép | IoU TB | Cùng lớp | Cùng occluded_level | Cùng truncated | Chưa ghép (A/B) | Bỏ qua do ignore | Đạt IAA |
|---|---|---|---|---|---|---|---|---|---|
| **TỔNG** | 40 | 296 | 0.825 | 93.2% | 51.0% | 92.9% | 91/122 | 0 | CHƯA ĐẠT |
| 101|102 | 6 | 26 | 0.850 | 92.3% | 80.8% | 96.2% | 6/4 | 0 | CHƯA ĐẠT |
| 101|103 | 9 | 84 | 0.776 | 97.6% | 41.7% | 92.9% | 24/38 | 0 | CHƯA ĐẠT |
| 101|104 | 5 | 52 | 0.842 | 92.3% | 48.1% | 90.4% | 11/19 | 0 | CHƯA ĐẠT |
| 102|103 | 5 | 30 | 0.856 | 100.0% | 63.3% | 93.3% | 8/23 | 0 | ĐẠT |
| 102|104 | 9 | 78 | 0.842 | 92.3% | 46.2% | 93.6% | 21/7 | 0 | CHƯA ĐẠT |
| 103|104 | 6 | 26 | 0.840 | 76.9% | 57.7% | 92.3% | 21/31 | 0 | CHƯA ĐẠT |

Ngưỡng IAA: IoU TB >= 0.85, đồng thuận lớp >= 95%.

Số ca bất thường: 544 ({'iou_thap': 128, 'sai_thuoc_tinh': 152, 'bat_dong_ignore': 76, 'bo_sot_thua': 164, 'sai_lop': 20, 'co_can_review': 4}), trên 37 ảnh cần calibration.
