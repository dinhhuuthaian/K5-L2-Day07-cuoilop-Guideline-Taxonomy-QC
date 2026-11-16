# Guideline gán nhãn — v0.1 (102) 


- Phiên bản: v0.1 (bản cá nhân, trước họp nhóm)
- Ngày: 2026-11-16
- Người viết: 102 · Người duyệt: (nhóm, Pha 2)

---

## 1. Mục tiêu

Nhãn dùng để huấn luyện mô hình **phát hiện vật trên ảnh 2D** (bounding box) cho **người và phương tiện
giao thông đường bộ** ở ảnh đường phố (camera giao thông / xe tự lái).

- Sai nguy hiểm nhất: **bỏ sót** người hoặc xe **thật, đang ở trên/cạnh đường** (mô hình học rằng chỗ đó trống).
- Sai cũng có hại: gán nhãn cho vật **không phải người/xe thật** (tượng, poster, phản chiếu, đồ chơi) →
  mô hình báo động giả.
- Không quan trọng: biển hiệu, đồ vật, động vật, hàng hóa.

## 2. Lớp và thuộc tính

### 2.1 Lớp

| Lớp | Định nghĩa (một câu) | Ví dụ | Phản ví dụ / dễ nhầm với |
|---|---|---|---|
| `car` | Ô tô chở người ≤ 9 chỗ, khoang người và khoang hành lý liền một khối (sedan, hatchback, SUV, wagon, taxi). | img_015, img_023, img_034 | Pickup → xem R-05; minivan chở khách → `van` |
| `truck` | Xe có cabin riêng tách khỏi thùng hàng (thùng hở, thùng kín, thùng bạt), kể cả pickup và đầu kéo. | img_002, img_007, img_036 | Van thùng liền cabin → `van` |
| `van` | Xe 4 bánh thân hộp liền một khối (cabin và khoang sau chung vỏ), không có thùng tách rời. | img_005 (xe trắng 51LD), img_016 | SUV nhỏ → `car` |
| `motorcycle` | Xe 2 bánh có động cơ (xe máy, tay ga, mô tô), **kể cả khi đang đỗ** và có/không có người. | img_008, img_010, img_030 | Xe đạp → R-07 |
| `person` | Người thật, đi bộ, đứng, ngồi, hoặc đang lái/ngồi trên xe. | img_014, img_034 | Tượng, ma-nơ-canh, người trên poster/mural → R-10 |
| `bus` | Xe bus 4 bánh, chở từ 25 khách trở lên | img_009, img_031, img_037 | Xe van, xe truck |
| `bicycle` | Xe 2 bánh có bàn đạp | xe đạp, xe đạp điện | xe máy, xe mô hình |
| `three_wheeler` | Xe 3 bánh | Xích lô, tuk-tuk, xe lam  | xe đẩy hàng |
| `ignore_region` | Vùng có **nhiều vật dính nhau** mà không thể vẽ từng box tách bạch; bỏ sót trong vùng này không tính lỗi. | img_021 (cuối đoàn xe), img_030 | **Không** dùng để che vật mình không chắc → dùng `can_review` |


### 2.2 Thuộc tính

| Thuộc tính | Mức | Ngưỡng cụ thể |
|---|---|---|
| `occluded_level` | `0` | Thấy ≥ 90% vật. |
| | `1` | Bị che 10% – < 30%. |
| | `2` | Bị che 30% – 70%. |
| | `3` | Bị che > 70% **hoặc** không ước lượng được (tối, nhòe, đám đông). |
| `truncated` | `yes` | Box chạm mép ảnh **và** phần vật bị mất ngoài khung ước tính ≥ 10%. |
| | `no` | Còn lại (kể cả box chạm mép nhưng vật gần như đủ). |
| `can_review` | tick | Không chắc **lớp** hoặc **có nên gán hay không**. Không tick chỉ vì box hơi lệch. |


## 3. Quy tắc vẽ box

| ID | Quy tắc |
|---|---|
| **R-01** | Box ôm sát phần nhìn thấy (amodal = không). Không đoán phần bị che. Sai số cho phép ~2 px mỗi cạnh. |
| **R-02** | Chỉ gán vật có chiều cao box ≥ 20 px. Nhỏ hơn: bỏ qua, không lỗi. |
| **R-03** | Người đi xe máy: 2 box riêng.** Một box `person` cho mỗi người (lái và ngồi sau, mỗi người 1 box), một box `motorcycle` cho xe. Box xe không bao người; box người bao cả phần chân/tay đang nằm trên xe, mũ bảo hiểm tính là một phần người. |
| **R-04** | Người ngồi trên xe đang đỗ (img_010, cô gái ngồi trên xe 29-C1) vẫn theo R-03: 2 box. |
| **R-05** | Pickup (cabin + thùng hở) → `truck`. Áp dụng cho img_001, 012, 028, 037. Pickup gắn nắp thùng kín (img_037) vẫn theo cùng lớp. |
| **R-06** | Xe chở xe / hàng trên xe: xe chở là 1 box; mỗi xe thật được chở (thấy đủ hình dạng xe) là box riêng của lớp nó, có `occluded_level` theo khung che. Hàng hóa (thùng, bao, ống, tượng) nằm trong box xe chở nếu nhô ra — box xe bao cả hàng hoặc box chỉ bao thân xe. |
| **R-07** | Phương tiện ngoài danh sách lớp: theo lựa chọn ở mục 2.1 (a/b/c). Người lái/ngồi trên các xe này vẫn gán `person`. |
| **R-08** | Đám đông / đoàn xe dính nhau: nếu ≥ 5 vật cùng lớp chồng nhau mà không tách được từng box, vẽ một `ignore_region` bao cả cụm; các vật ở hàng trước, tách rõ vẫn gán từng box. |
| **R-09** | Phản chiếu (gương, kính, mặt đường ướt) → không gán. |
| **R-10** | Không phải người/xe thật → không gán: tượng, mô hình, ma-nơ-canh, đồ chơi, người trên biển quảng cáo/poster/mural/sticker. |
| **R-11** | Xe chủ (ego) — phần thân xe/gương của xe đang chụp ở mép ảnh → không gán. |
| **R-12** | Vật mờ do chuyển động → vẫn gán nếu nhận ra lớp; box ôm vùng nhòe của vật; `occluded_level=3` nếu không thấy rõ ranh giới. Không nhận ra lớp → `can_review`. |
| **R-13** | Người mặc trang phục hóa trang là `person`. Nhân vật hình nộm (không có người bên trong) → R-10. |

## 4. Ca khó

Phân loại: **Q** = loại/quyết theo quy tắc đã có · **H** = cần hỏi nhóm/reviewer.

| Ảnh | Tình huống | Rule | Quyết định | Q/H | Lý do |
|---|---|---|---|---|---|
| img_002 | Xe tải chở ô tô (car carrier), các ô tô trên giá bị khung che | R-06 | 1 `truck` + mỗi ô tô thấy rõ hình dạng là `car` (occluded 1–2) | H | Có người coi xe được chở là “hàng” → không gán; cần thống nhất |
| img_024 | Ô tô vàng đặt trên nóc ô tô đen, trong bảo tàng xe | R-06 | 2 box `car`; xe trưng bày trong nhà vẫn là xe thật | H | Môi trường không phải đường; mục tiêu có cần không? |
| img_005 / 006 / 008 / 021 | Người đi xe máy, nhiều người chồng nhau | R-03, R-08 | 2 box/xe ở hàng trước; cụm phía sau không tách được → `ignore_region` | Q | |
| img_026 | 2 người trên 1 xe máy, phía sau là mural có hình | R-03, R-10 | 2 `person` + 1 `motorcycle`; mural không gán | Q | |
| img_010 | Người ngồi trên xe đỗ bên lề; xe đẩy rau | R-04, R-07 | 2 box; xe đẩy không gán | Q | |
| img_029 | Người đi xe máy và xe đạp cùng vác ống thép dài | R-03, R-06, R-07 | `person` + `motorcycle`; ống không thuộc box nào; xe đạp theo R-07 | H | Xe đạp chưa có lớp |
| img_035 | Tuk-tuk (auto-rickshaw) chở hàng cao gấp đôi xe | R-07, R-06 | Theo R-07; nếu gán thì box có bao hàng hay không? | H | |
| img_004 / 016 / 040 | Tuk-tuk, có người ngồi trong | R-07 | Theo R-07; người thấy rõ → `person` | H | Lớp chưa có |
| img_009 / 032 / 037 / 040 | Xe buýt (minibus, bus thành phố) | R-07 | Theo R-07 | H | Xe lớn trên đường, bỏ sót là nguy hiểm |
| img_023 / 039 | Xích lô, người đạp | R-07 | Theo R-07; người đạp → `person` | H | |
| img_003 / 006 / 034 | Xe đạp (đỗ, dắt, đang đi) | R-07 | Theo R-07 | H | |
| img_022 | Mô tô có thùng sidecar, ảnh đen trắng | R-07 | `motorcycle`, box bao cả sidecar | H | |
| img_001 / 012 / 028 / 037 | Pickup (cabin + thùng) | R-05 | `truck` | H | car hay truck? |
| img_036 | Xe tải nhỏ thùng bạt | — | `truck` | Q | Cabin tách thùng |
| img_005 / 016 | Xe thân hộp liền (van) | — | `van` | Q | |
| img_007 | Kho hàng tối, pickup + xe tải thùng | R-05 | `truck` ×2 | Q | |
| img_017 | Tượng người cưỡi ngựa | R-10 | Không gán | Q | |
| img_027 | Tượng/đài tưởng niệm hình xe pickup | R-10 | Không gán | Q | |
| img_028 | Tượng ngựa trên thùng pickup thật | R-06, R-10 | Pickup gán; tượng ngựa không gán, không bao vào box xe | H | Box xe có bao tượng nhô lên? |
| img_011 | Người hóa trang Predator; mô-tô trang trí kiểu điêu khắc | R-13, R-10 | Predator: `person` nếu có người bên trong, không thì không gán; mô-tô điêu khắc → `can_review` | H | Không chắc là xe chạy được |
| img_019 | Xe diễu hành hình hoạt hình, có người lái và hình nộm chuột; đám đông sau rào | R-13, R-08 | Xe → `car` (xe thật chạy được); người lái → `person`; hình nộm không gán; đám đông → `ignore_region` | H | “Xe đồ chơi” hay xe thật? |
| img_038 | Tủ kính đầy ô tô đồ chơi | R-10 | Không gán | Q | |
| img_033 | Ma-nơ-canh + phản chiếu trên kính | R-09, R-10 | Không gán | Q | |
| img_018 | Biển quảng cáo có hình người; ô tô đỗ sau hàng rào | R-10, R-01 | Người trên biển không gán; xe gán phần nhìn thấy, occluded theo rào | H | Hàng rào thưa có tính là che? |
| img_020 | Gương chiếu hậu phản chiếu ô tô; thân xe ego | R-09, R-11 | Không gán gì → ảnh không có vật, vẫn phải có trong COCO | Q | |
| img_015 / 031 | Phản chiếu trên đường ướt; xe nhòe; xe cắt mép | R-09, R-12 | Chỉ gán xe thật; `truncated=yes` cho xe mép | Q | |
| img_040 | Gương xe máy gần camera; sticker hình người trên taxi | R-11, R-10 | Không gán gương/sticker; người đội mũ → `person` | Q | |
| img_014 | Xe máy nhòe chuyển động sau 2 người đi bộ | R-12 | Gán nếu nhận ra; không thì `can_review` | H | Ranh giới nhòe khó IoU cao |
| img_030 | Bãi xe máy đỗ dày đặc | R-08 | Hàng trước gán từng xe; phía sau `ignore_region` | H | Ngưỡng “không tách được” chủ quan |
| img_025 / 013 / 039 | Người/xe rất nhỏ ở xa | R-02 | < 20 px bỏ qua | Q | |

## 5. QC và phiên bản

- Ngưỡng QC : ghép box IoU ≥ 0.5; IAA đạt khi IoU ≥ 0.85 và đồng thuận lớp ≥ 0.95; lỗi ảnh ≤ 2%.
- Ca H do nhóm chốt ở Pha 2; trong lúc gán, ca không có trong bảng → tick `can_review` và ghi vào `image_issues.csv`.
- Đổi cách chọn vật/lớp/box/thuộc tính = thay đổi semantic → tăng phiên bản, kiểm lại cả lô.

| Phiên bản | Thay đổi | Lý do (ca nào) |
|---|---|---|
| v0 | Bản khởi đầu của giảng viên | — |
| v0.1 | Thêm định nghĩa lớp, ngưỡng thuộc tính, R-01 → R-13, bảng ca khó | Đọc 40 ảnh; các ca ở mục 4 |
