# Guideline gán nhãn — v1.1 (sau calibration)

- Phiên bản: **v1.1** — sau calibration Pha 5 (thay v1.0). Thay đổi loại **semantic**: xem mục 5 và mục 7.
- Ngày: 2026-11-17
- Nguồn: tổng hợp từ `guideline_101.md`, `guideline_102.md`, `guideline_103.md`, `guideline_104.md`
- Người viết: 101, 102, 103, 104 · Người chốt: 101
- Loại nhãn: bounding box 2D · Công cụ: CVAT, xuất COCO 1.0 · Taxonomy: `submission/taxonomy.json` v1.0

---

## 1. Mục tiêu

Nhãn dùng để huấn luyện mô hình phát hiện người và phương tiện giao thông trên ảnh 2D đường phố
(camera giao thông, xe tự lái). Nguyên tắc chung: gán vật thật, thuộc giao thông, nhìn thấy đủ để nhận ra lớp; còn lại không gán.

| Loại sai | Hậu quả | Quy tắc chặn |
|---|---|---|
| Bỏ sót người/xe thật, nhất là ở gần | Mô hình coi vật cản là nền → nguy hiểm nhất | R-01, R-03, R-08 |
| Gán vật không thật (tượng, hình in, đồ chơi, phản chiếu) | Báo động giả, phanh gấp vô cớ | R-06, R-07 |
| Cùng tình huống, mỗi người vẽ một kiểu | Nhãn nhiễu, IAA thấp | Toàn bộ mục 3–4 |

## 2. Lớp và thuộc tính

### 2.1 Lớp (mỗi vật thuộc đúng một lớp)

Trục phân loại phương tiện: có động cơ hay không → số bánh → cấu trúc thân xe. Không dựa vào màu, kích thước tuyệt đối hay số người trên xe.

| Lớp | Định nghĩa | Ví dụ | Phản ví dụ / dễ nhầm |
|---|---|---|---|
| `car` | Ô tô con ≤ 9 chỗ, khoang người và khoang hành lý liền một khối: sedan, hatchback, SUV, MPV, wagon, taxi. | img_023 (xe đen), img_034, img_040 (taxi) | Bán tải img_001 → `truck`; ô tô đồ chơi img_038, tượng xe img_027 → không gán |
| `truck` | Xe chở hàng có cabin tách khỏi thùng/sàn hàng (hở, bạt, kín), gồm bán tải (kể cả có nắp thùng), xe tải nhỏ, xe đầu kéo, xe chở xe. | img_002, img_007, img_036, img_037 (bán tải nắp cao) | Van thân liền img_005 → `van`; nắp thùng cao không biến bán tải thành van |
| `van` | Xe 4 bánh thân hộp liền một khối (cabin và khoang sau chung vỏ), ≤ 9 chỗ hoặc chở hàng cỡ nhỏ. | img_005 (xe 51LD), img_016 | Minibus img_009 → `bus`; xe tải bạt img_036 → `truck` |
| `bus` | Xe chở khách > 9 chỗ: thân dài một khối, từ 4 ô cửa sổ hông trở lên hoặc có cửa lên xuống riêng cho khách; gồm minibus, xe buýt, xe khách. | img_009 (minibus), img_031, img_037 (xe xanh), img_040 | Van img_005 (≤ 3 cửa sổ hông); trạm chờ xe buýt img_032 không có xe → không gán |
| `motorcycle` | Xe 2 bánh có động cơ: xe số, tay ga, mô tô; kể cả mô tô gắn sidecar (xe + thùng là một vật). | img_008, img_026, img_030, img_022 (sidecar) | Xe đạp img_006 → `bicycle`; tuk-tuk có cabin → `three_wheeler` |
| `three_wheeler` | Xe 3 bánh có động cơ có khoang/cabin chở người hoặc hàng: tuk-tuk, auto-rickshaw, xe lam. | img_004, img_016, img_035, img_040 (tuk-tuk "TAXI") | Xích lô đạp img_023 → `bicycle`; sidecar img_022 → `motorcycle` |
| `bicycle` | Xe chạy bằng sức người (bàn đạp), 2 hoặc 3 bánh: xe đạp, xe đạp chở hàng, xích lô. | img_003, img_006, img_029, img_023 (xích lô) | Xe máy/xe đạp điện có động cơ → `motorcycle`; xe đẩy tay img_010 → không gán |
| `person` | Người thật nhìn thấy trực tiếp: đi bộ, đứng, ngồi, người lái/hành khách trên xe hở (xe máy, xe đạp, xích lô, tuk-tuk, thùng bán tải). | img_014, img_026, img_034 | Tượng img_017, ma-nơ-canh img_033, hình in img_018/img_026 (mural), linh vật img_019 |
| `ignore_region` | Vùng chữ nhật phủ vật cao < 20 px hoặc cụm vật dính nhau không tách được; bỏ sót trong vùng không tính lỗi. Không phải vật. | Đuôi đoàn xe img_021, phía sau bãi xe img_030 | Không dùng để né ca khó hay né chọn lớp → dùng `can_review` |

**Vật không thuộc lớp nào** (xe đẩy tay, động vật, hàng rời, biển hiệu): không gán, không vẽ `ignore_region` chỉ vì nằm ngoài taxonomy. Nếu nghi là phương tiện mà không xếp được lớp → gán lớp gần nhất theo trục phân loại + `can_review` (R-12).

### 2.2 Thuộc tính

**`occluded_level`** — p = tỉ lệ diện tích vật (phần nằm trong ảnh) bị vật khác che, ước lượng bằng mắt. Không tính phần ngoài mép ảnh (đó là `truncated`), không tính mũ/khẩu trang/quần áo, không tính mờ chuyển động.

| Mức | Ngưỡng | Cách kiểm nhanh |
|---|---|---|
| `0` | p < 10% | Thấy gần trọn vật |
| `1` | 10% ≤ p < 30% | Mất một góc nhỏ (ví dụ một bánh xe) |
| `2` | 30% ≤ p < 70% | Mất khoảng nửa vật |
| `3` | p ≥ 70%, vẫn nhận ra chắc chắn lớp | Chỉ còn đầu người / đầu xe |

Không nhận ra lớp → **không gán** (không dùng mức 3 để thay "không biết"). Phân vân giữa hai mức → chọn mức cao hơn + `can_review`. **Cách ước lượng bắt buộc: R-16.**

**`truncated`**

| Giá trị | Ngưỡng |
|---|---|
| `yes` | Mép ảnh cắt mất ≥ 10% thân vật (ước lượng). Box dừng tại mép ảnh. |
| `no` | Còn lại, kể cả box chạm mép nhưng vật gần như đủ. |

Một vật có thể vừa `occluded_level ≥ 1` vừa `truncated = yes`.

**`can_review`** — tick khi: (a) phân vân giữa hai lớp; (b) không chắc vật thật hay giả; (c) hàng quá khổ / hình dạng lạ; (d) không chắc ranh giới box. Tick là hỏi, không phải né: vẫn phải chọn lớp và vẽ box.

## 3. Quy tắc vẽ box

| ID | Quy tắc |
|---|---|
| **R-01** | **Ôm phần nhìn thấy.** Box là hình chữ nhật nhỏ nhất bao phần nhìn thấy; dư ≤ 2 px mỗi cạnh. **Không đoán phần bị che** (không amodal). **Người:** gồm mũ bảo hiểm, tay, chân kể cả phần đặt trên xe; không gồm túi/gánh hàng cầm theo. **Xe:** gồm gương, tay lái, mui/bạt gắn cố định; không gồm hàng rời (R-05), bóng đổ, nước bắn, vệt nhòe. *(v1.1: thêm phạm vi người/xe — ca K3)* |
| **R-02** | **Một vật một box.** Không gộp nhiều vật, không chia một vật. Tổ hợp gắn liền (đầu kéo + rơ-moóc, mô tô + sidecar) là một vật. |
| **R-03** | **Người trên xe hở: tách box.** Mỗi người (lái và từng người ngồi sau) một box `person`; xe một box riêng. Box xe không bao người, box người không bao xe; hai box chồng nhau là bình thường. Áp dụng cả khi xe đang đỗ (img_010) và cho xe đạp, xích lô, tuk-tuk, thùng bán tải. Kiểm thử: img_005, img_026 (1 xe + 2 người = 3 box), img_006. |
| **R-04** | **Người trong ô tô kín** (chỉ thấy qua kính chắn gió/kính cửa): không gán. Người ngồi trong xe hở (R-03) thì gán. |
| **R-05** | **Hàng hóa trên xe.** Bộ phận gắn cố định (mui, bạt, nắp thùng) thuộc box xe. Hàng rời (bao, thùng, ống, tượng) không mở rộng box xe; hàng nhô quá thân xe rõ rệt → `can_review` (img_012, img_029, img_035, img_028). |
| **R-06** | **Vật không thật → không gán:** tượng, ma-nơ-canh, đồ chơi, mô hình, linh vật, hình in trên biển/poster/mural/sticker, ảnh trên màn hình. Xe thật chở vật giả vẫn gán xe (img_028). |
| **R-07** | **Phản chiếu → không gán:** gương, kính, mặt nước, đường ướt (img_015, img_020, img_031). |
| **R-08** | **Vật nhỏ:** đo chiều cao phần nhìn thấy trên **ảnh gốc** bằng cách **vẽ thử box trong CVAT và đọc kích thước** (không ước bằng mắt, không đo trên ảnh thu nhỏ). Cao **< 20 px** → không vẽ box riêng, phủ `ignore_region` quanh vật/cụm. Cao ≥ 20 px **bắt buộc** có box và **không được nằm trong** `ignore_region`. *(v1.1: bắt buộc đo bằng box thử — ca K4, K6)* |
| **R-09** | **Đám đông / xe dày đặc:** gán từ gần ra xa từng vật tách được (thấy ranh giới, ≥ 20 px). Chỉ khi gặp cụm **≥ 3 vật chồng nhau** mà phóng **200%** vẫn không đếm được số vật và biên từng vật → phủ `ignore_region` **vừa khít cụm đó**. Không phủ cả hàng/cả dãy/cả ảnh; một ảnh có thể có nhiều vùng ignore nhỏ. Ảnh chỉ có vật giả hoặc phản chiếu (img_020, img_038) **không** vẽ ignore. *(v1.1: thu hẹp vùng ignore — ca K6)* |
| **R-10** | **Cắt mép ảnh:** vẫn gán, box sát mép. `truncated=yes` chỉ khi mép ảnh cắt mất **≥ 10% thân vật**; box chạm mép nhưng vật gần đủ → `no`. Phần nhìn thấy không đủ để nhận ra lớp → không gán, ghi `image_issues.csv`. *(v1.1: nhắc lại ngưỡng — ca K2)* |
| **R-11** | **Xe chủ (ego):** phần xe/xe máy gắn camera (gương, cửa, tay lái sát ống kính – img_020, img_040) → không gán. Chỉ loại khi có bằng chứng rõ; không chắc → gán + `can_review`. |
| **R-12** | **Xe thật hình dạng lạ** (xe diễu hành, xe tự chế, xe trưng bày): xe thật (có bánh, biển số, người lái hoặc đặt trên mặt đất như xe thường) → gán lớp theo cấu trúc + `can_review`. Vật trông như xe nhưng không có dấu hiệu xe thật (thân vỏ đặt trên nóc xe khác, img_024) → `can_review`, không tự loại. |
| **R-13** | **Xe chở xe:** xe chở = 1 box `truck` (đầu kéo + rơ-moóc), không mở box theo xe được chở; mỗi xe được chở cao ≥ 20 px và nhận ra được = 1 box `car`, `occluded_level` theo khung giá che (img_002). |
| **R-14** | **Mờ chuyển động / đêm / lóa:** gán nếu còn nhận ra lớp; box ôm phần thân nhìn rõ nhất, không kéo theo vệt mờ hoặc chỉ theo đèn. Mờ **không** làm tăng `occluded_level`. Không nhận ra lớp, vùng lớn → `ignore_region` (img_014 phía sau hai người đi bộ). |
| **R-15** | **Ca chưa chốt trong lúc gán:** vẽ được box → gán lớp tốt nhất + `can_review`. Không vẽ được → ghi nháp ảnh / vùng / lý do; sau khi khóa nhãn mới đưa vào `submission/qc/image_issues.csv`. |
| **R-16** | **Ước lượng `occluded_level` (mới ở v1.1).** (1) Hình dung vật đầy đủ trong khung ảnh, chia thành **4 phần bằng nhau** (người: đầu-vai / thân trên / hông-đùi / cẳng chân; xe: chia 4 theo chiều dài). (2) Đếm số phần bị **vật khác** che quá nửa: 0 phần → `0`; 1 phần → `1`; 2 phần → `2`; 3 phần trở lên mà vẫn nhận ra lớp → `3`. (3) **Không tính là che:** phần người bị **chính chiếc xe họ đang lái/ngồi** che (chân sau thân xe máy, xe đạp); phần xe bị **người đang lái nó** che; mũ, khẩu trang, quần áo; mờ chuyển động; phần ngoài mép ảnh. *(ca K1: 145 ca lệch, 51% đồng thuận)* |
| **R-17** | **Người chỉ lộ đầu/mũ bảo hiểm (mới ở v1.1).** Mũ đang đội trên đầu, ở vị trí người đứng/ngồi trên xe → `person`, `occluded_level=3`, box ôm phần nhìn thấy. Mũ rời (treo trên xe, đặt trên yên) → không gán. *(ca K8: img_005)* |

## 4. Ca khó

**Q** = quyết theo quy tắc có sẵn · **H** = đã đưa ra họp, nhóm chốt như dưới.

| Ảnh | Tình huống | Rule | Quyết định | Q/H | Lý do |
|---|---|---|---|---|---|
| img_002 | Xe chở 8 ô tô hai tầng | R-13, R-02 | 1 `truck` + 1 `car` mỗi xe được chở ≥ 20 px | H | 4/4 bản đồng ý; xe được chở là xe thật |
| img_005 | Người đội mũ chồng nhau, xe máy cắt đáy, van phía sau | R-03, R-10 | Từng người `person`; xe máy `truncated=yes`; van | Q | |
| img_026 | Xe máy đỏ 2 người, tranh tường phía sau | R-03, R-06 | 1 `motorcycle` + 2 `person`; mural không gán | Q | Ca thử R-03 |
| img_010 | Người ngồi trên xe tay ga đang đỗ; xe đẩy rau | R-03 | 2 box mỗi xe có người; xe đẩy không gán | Q | Xe đẩy ngoài taxonomy, không phải phương tiện |
| img_004 / 016 / 035 / 040 | Tuk-tuk, auto-rickshaw | 2.1 | `three_wheeler`; tài xế thấy rõ → `person` | H | 4/4 đề xuất lớp riêng |
| img_009 / 031 / 037 / 040 | Minibus, xe buýt | 2.1 | `bus` | H | 4/4 đề xuất; ngưỡng > 9 chỗ / ≥ 4 cửa sổ |
| img_003 / 006 / 029 / 034 | Xe đạp | 2.1, R-03 | `bicycle` + `person` cho người đạp | H | 3/4 đề xuất; xem bảng 6 |
| img_023 | Xích lô đạp | 2.1 | `bicycle` + `person` | H | Không động cơ → theo trục phân loại |
| img_022 | Mô tô sidecar, ảnh đen trắng | R-02 | 1 `motorcycle` bao cả sidecar | Q | 101, 104 đồng ý; một tổ hợp gắn liền |
| img_001 / 012 / 028 / 037 | Bán tải, kể cả nắp thùng cao | 2.1 | `truck` | Q | 4/4 đồng ý |
| img_035 | Tuk-tuk chất bao hàng cao gấp đôi | R-05 | `three_wheeler` chỉ ôm thân xe + `can_review` | H | Xem bảng 6 |
| img_029 | Xe máy + xe đạp cùng vác ống thép dài | R-05, R-03 | `motorcycle`, `bicycle`, 2 `person`; ống không thuộc box nào | H | Hàng rời |
| img_012 | Thùng bán tải chất hàng sát máy ảnh | R-05, R-10, R-11 | `truck`, `truncated=yes`, box không bao hàng; `can_review` nếu nghi ego | H | 104 nêu khả năng ego |
| img_017 / 027 | Tượng người cưỡi ngựa; tượng xe bán tải | R-06 | Không gán | Q | |
| img_033 / 038 | Ma-nơ-canh; ô tô đồ chơi | R-06 | Không gán | Q | |
| img_018 | Người trên biển quảng cáo; xe sau hàng rào | R-06, R-01 | Hình in không gán; xe ≥ 20 px gán, occluded theo rào | Q | |
| img_019 | Xe diễu hành, người lái, linh vật chuột, đám đông | R-12, R-06, R-09 | Xe → `car` + `can_review`; người lái `person`; linh vật không gán; đám đông theo R-09 | H | 101, 102, 104 đều chọn car |
| img_024 | Thân xe vàng trên nóc xe đen (bảo tàng) | R-12 | Xe đen `car`; xe vàng `car` + `can_review` | H | Xem bảng 6 |
| img_011 | Tượng Predator, mô tô điêu khắc kim loại | R-06, R-08 | Không gán tượng và mô tô điêu khắc; người xa < 20 px → `ignore_region` | H | Mô tô kim loại là tác phẩm trưng bày |
| img_020 | Gương chiếu hậu phản chiếu xe; thân xe ego | R-07, R-11 | Không gán gì; ảnh vẫn phải có trong COCO | Q | |
| img_015 / 031 | Xe nhòe, phản chiếu đường ướt, cắt mép | R-07, R-14, R-10 | Chỉ gán xe thật; `truncated` theo ngưỡng | Q | |
| img_014 | Hai người rõ, xe máy nhòe nặng phía sau | R-14 | 2 `person`; vùng nhòe không nhận lớp → `ignore_region` | H | 101, 104 thống nhất |
| img_021 / 030 / 008 | Đoàn xe máy / bãi xe dày đặc | R-09, R-03 | Tiền cảnh từng box; cụm sau theo R-09 | Q | |
| img_040 | Gương xe máy sát ống kính, sticker người trên taxi | R-11, R-06 | Không gán gương/sticker; người đội mũ `person` | Q | |
| img_025 / 013 / 039 | Người, xe rất nhỏ ở xa | R-08 | Đo trên ảnh gốc; < 20 px → `ignore_region` | Q | |

## 5. QC và phiên bản

Ngưỡng: vật nhỏ < 20 px; ghép cặp box IoU ≥ 0.5; IoU box ≥ 0.85 (cao ≥ 50 px) / ≥ 0.7 (nhỏ hơn); IAA IoU TB ≥ 0.85 và đồng thuận lớp ≥ 95% trên các cặp ghép được; ảnh lỗi ≤ 2% mới Release.

- v1.0 và `taxonomy.json` v1.0 khóa trong Pha 3. Ca mới → `can_review` / `image_issues.csv`, không tự sửa quy tắc.
- Thay đổi ở Pha 5: đính chính câu chữ → `editorial`; đổi cách chọn vật/lớp/box/thuộc tính → `semantic`, cần ≥ 1 quyết định `pham_vi=lo` và kiểm lại cả lô.

| Phiên bản | Thay đổi | Lý do |
|---|---|---|
| v0 | Bản khởi đầu của giảng viên | — |
| v1.0 | Thêm `bus`, `three_wheeler`, `bicycle`; ngưỡng đo được cho `occluded_level`, `truncated`; R-01 → R-15; bảng ca khó | Tổng hợp 4 bản cá nhân, giải quyết bất đồng ở mục 6 |
| v1.1 | **semantic:** thêm R-16 (cách ước lượng che khuất, không tính xe tự lái che người lái), R-17 (người chỉ lộ mũ); sửa R-08/R-09 (đo bằng box thử, ignore vừa khít cụm, không ignore ảnh vật giả). **editorial:** làm rõ R-01 (phạm vi box người/xe), R-10 (ngưỡng truncated). Taxonomy giữ nguyên v1.0. | IAA v1.0 chưa đạt (IoU 0.825, cùng lớp 93.2%, cùng occluded 51%); 544 ca trên 37 ảnh — xem mục 7 |

## 6. Giải quyết bất đồng giữa các bản cá nhân

| # | Điểm bất đồng | 101 | 102 | 103 | 104 | Chốt v1.0 | Lý do |
|---|---|---|---|---|---|---|---|
| D1 | Lớp mới | bus, three_wheeler, bicycle | bus, three_wheeler, bicycle | bus, tuktuk, bike | bus, tuk_tuk; xe đạp ngoài phạm vi | `bus`, `three_wheeler`, `bicycle` | 3/4 thêm cả ba; xe đạp đi trên làn đường là vật cản thật, bỏ ra thì mô hình học nó là nền |
| D2 | Tên lớp | three_wheeler, bicycle | three_wheeler, bicycle | tuktuk, bike | tuk_tuk | `three_wheeler`, `bicycle` | Tên tổng quát (gồm xe lam, auto-rickshaw), khớp schema `^[a-z][a-z0-9_]*$` |
| D3 | Xích lô | bicycle | three_wheeler | không rõ | ngoài phạm vi | `bicycle` | Trục "có động cơ" đặt trước "số bánh" → mỗi xe chỉ rơi vào một lớp |
| D4 | Ngưỡng bus | > 9 chỗ | ≥ 25 khách | thân dài, nhiều cửa sổ | thân dài, cửa sổ hành khách | > 9 chỗ, nhận bằng ≥ 4 cửa sổ hông / cửa khách | Số chỗ không đếm được trên ảnh → dùng dấu hiệu nhìn thấy; minibus img_009 vào `bus` |
| D5 | Mốc `occluded_level` | 0 / 40 / 70 | 10 / 30 / 70 | 10 / 30 / 70 | 0 / 30 / 70 | 10 / 30 / 70 | 3/4 dùng mốc 30–70; mức 0 = < 10% vì ước lượng bằng mắt không phân biệt được 0% và 5% |
| D6 | Mức 3 khi "không rõ" | không gán | gộp "không ước lượng được" | — | không dùng thay "không biết" | Mức 3 chỉ khi còn nhận ra lớp | 3/4 đồng ý; gộp "không biết" vào mức 3 làm thuộc tính mất nghĩa |
| D7 | Ngưỡng `truncated` | ≥ 10% | ≥ 10% | bị cắt bất kỳ | vật tiếp tục ra ngoài | ≥ 10% | Tránh `yes` do chạm mép 1–2 px; thống nhất với mốc 10% của occlusion |
| D8 | Box đoán phần bị che (amodal) | không | không | có | không | Không | 3/4; phần đoán khác nhau giữa người gán → IoU thấp |
| D9 | Vật < 20 px | ignore_region cụm | bỏ qua | ignore nếu đông | ignore_region | `ignore_region` | Đúng quy chuẩn lab; "bỏ qua" làm vật nhỏ bị tính là bỏ sót |
| D10 | Hàng rời trong box xe | gộp vào box | chưa chốt | — | không gộp | Không gộp, `can_review` khi quá khổ | Biên hàng rời thay đổi theo từng ảnh → khó đạt IoU 0.85; 104 lập luận rõ nhất |
| D11 | Ngưỡng đám đông → ignore | không có số | ≥ 5 vật | không có số | ≥ 3 vật, phóng 200% | ≥ 3 vật, phóng 200% vẫn không tách | Có cách kiểm cụ thể; ngưỡng thấp hơn giữ được nhiều box tiền cảnh hơn |
| D12 | Mờ chuyển động | ignore nếu không nhận | occluded = 3 | — | không phải che | Không tính là che (R-14) | Mờ là chất lượng ảnh, không phải vật khác che |
| D13 | Người sau kính ô tô kín | không gán | — | — | gán person | Không gán (R-04) | Thường chỉ thấy mờ đầu/vai, khó nhất quán; mô hình phát hiện xe đã bao trường hợp này |
| D14 | Xe vàng trên nóc img_024 | mô hình → không gán | car | review | review | `car` + `can_review` | Chưa đủ bằng chứng loại; để reviewer xem ở Pha 4 |

## 7. Calibration v1.0 → v1.1

Nguồn: `submission/qc/iaa_summary.md`, `calibration_candidates.csv`. Quyết định từng ca: `calibration_decisions.csv` (544 dòng, cột `quyet_dinh` bắt đầu bằng mã nhóm K).

| Nhóm | Kiểu lỗi | Số ca | Chẩn đoán | Quyết định | Quy tắc | Phạm vi |
|---|---|---:|---|---|---|---|
| K1 | Lệch `occluded_level` | 145 | **Cả hai cùng lệch**, có hướng (102 chấm cao hơn 104; 101 ≠ 103): ngưỡng % có nhưng cách ước lượng mơ hồ, nhất là người trên xe | Thêm cách ước lượng 4 phần, không tính xe tự lái che người lái | R-16 (mới) | `lo` |
| K2 | Lệch `truncated` | 7 | Một người lệch: chấm `yes` khi box chỉ chạm mép | Nhắc lại ngưỡng ≥ 10% | R-10 | `anh` |
| K3 | IoU thấp | 128 | Phần lớn box `person` lỏng/thiếu chân, tay | Làm rõ phạm vi box người/xe | R-01 | `anh` |
| K4 | Bỏ sót / thừa | 139 | Ảnh đông (img_021, 006, 008, 032, 030, 034): mỗi người dừng gán ở độ sâu khác nhau | Đo bằng box thử; ≥ 20 px tách được là phải gán | R-08, R-09 | `anh` |
| K5 | Gán đồ chơi | 25 | **Một người lệch** (img_038): guideline đã rõ, người gán chưa nắm R-06 | Xoá box, không đổi quy tắc | R-06 | `anh` |
| K6 | Bất đồng `ignore_region` | 76 | 103 gần như không dùng ignore, người khác phủ ignore lên vật ≥ 20 px (img_011, 019, 021) | Ignore vừa khít cụm, không ignore ảnh vật giả | R-08, R-09 | `lo` |
| K7 | Sai lớp | 21 | Từng ca, chốt theo trục 2.1 sau khi nhóm xem ảnh (`sai_lop_review.csv`) | Lớp chốt ghi trong từng dòng | 2.1 | `anh` |
| K8 | `can_review`: chỉ lộ mũ | 2 | Guideline chưa có quy tắc | person, occluded 3 | R-17 (mới) | `anh` |
| K9 | `can_review`: hàng trên tuk-tuk | 1 | Đã có R-05, người gán chưa chắc | Box chỉ ôm thân xe | R-05 | `anh` |

**IAA không xác nhận được:** hai người cùng làm giống nhau vẫn có thể cùng sai (ví dụ cùng phủ một `ignore_region` lên người cao > 20 px) — cặp đó không sinh ca nào. Vì thế R-16/R-08/R-09 là `lo`: duyệt lại **cả 40 ảnh**, không chỉ các ảnh bị flag.

