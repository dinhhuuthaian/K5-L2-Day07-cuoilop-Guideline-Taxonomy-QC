# Guideline gán nhãn — v0 (bản khởi đầu)

> **Đây là bản do giảng viên viết nhanh. Nó CHƯA đủ dùng.**
> Đừng sửa file này. Hãy copy sang `submission/guidelines/individual/` rồi sửa bản của bạn
> (xem `GUIDE.md`, Pha 1).

- Phiên bản: v0
- Loại nhãn: bounding box (hộp chữ nhật) trên ảnh đường phố
- Công cụ: CVAT, xuất COCO 1.0

---

## 1. Mục tiêu

Nhãn dùng để huấn luyện mô hình phát hiện người và phương tiện trên ảnh 2D đường phố (camera giao thông, xe tự lái).
Sai ở đâu thì nguy hiểm:
Bỏ sót vật thật ở gần: xe hoặc người ở gần là thứ nguy hiểm nhất. Quy tắc nào cũng không được dẫn tới việc bỏ vật ở gần.
Gán box cho vật không thật (tượng, ma-nơ-canh, xe đồ chơi, hình in, phản chiếu): mô hình học báo động giả, xe phanh gấp vô cớ.
Cùng một tình huống mà mỗi người vẽ một kiểu (người đi xe máy, xe chở xe): nhãn nhiễu, IoU thấp.
Nguyên tắc chung: gán những gì là vật thật, nằm trong thế giới giao thông, nhìn thấy đủ để nhận ra loại; những gì còn lại thì không gán.

## 2. Lớp và thuộc tính

### Lớp (mỗi vật thuộc đúng một lớp)

| Lớp | Định nghĩa |
|---|---|
| `car` | Ô tô con ≤ 9 chỗ, mũi xe có nắp capo rõ: sedan, hatchback, SUV, MPV, wagon, taxi. |
| `truck` | Xe chở hàng có thùng riêng (hở, bạt phủ hay kín) tách khỏi cabin, kể cả bán tải (pickup), xe tải nhỏ, xe tải thùng, xe đầu kéo, xe chở xe. |
| `van` | Xe thùng kín liền khối với cabin (không có capo tách rõ), cỡ nhỏ, chở hàng hoặc khách. |
| `bus` | Xe khách, xe buýt, minibus > 9 chỗ, lớn hơn rõ rệt xe van. |
| `motorcycle` | Xe 2 bánh có động cơ: xe số, tay ga, mô tô, kể cả mô tô có thùng bên (sidecar). |
| `three_wheeler` | Xe 3 bánh có động cơ: tuk-tuk, xe lam, auto-rickshaw |
| `bicycle` | Xe 2–3 bánh đạp chân, kể cả xích lô đạp. |
| `person` | Người thật: đi bộ, đứng, ngồi, và người lái/hành khách trên xe hở (xe máy, xe đạp, xích lô, tuk-tuk, thùng xe bán tải). |
| `ignore_region` | Một hộp phủ cụm vật quá nhỏ hoặc đám đông/xe dày đặc không tách được; bỏ sót bên trong không tính là lỗi. |

### Thuộc tính

| Thuộc tính | Giá trị | Ý nghĩa |
|---|---|---|
| `occluded_level` | `0`, `1`, `2`, `3` | Tính theo tỉ lệ diện tích vật bị vật khác che (không tính phần bị cắt mép ảnh). 0: Không bị che. 1: che > 0% đến 40%. 2: che > 40% đến 70%. 3: che > 70% nhưng vẫn nhận ra được lớp. Nếu không nhận ra lớp → không gán box (R-08). Ước lượng bằng mắt: nhìn xem còn thấy bao nhiêu phần thân xe/người. |
| `truncated` | `no`, `yes` | yes khi mép ảnh cắt từ 10% trở lên thân vật (ước tính). Dưới 10% thì no. Box vẽ sát mép ảnh. |
| `can_review` | tick / không | Tick khi: (a) lớp nằm ngoài taxonomy hoặc dễ nhầm hai lớp; (b) không chắc là vật thật hay vật giả; (c) hàng quá khổ, hình dạng lạ; (d) không chắc ranh giới box. Tick là cách hỏi, không phải cách tránh quyết định: vẫn phải chọn một lớp.|

Một vật vừa bị che vừa bị cắt mép thì đánh cả hai thuộc tính độc lập.
## 3. Quy tắc vẽ box

| Mã | Quy tắc |
|---|---|
| R-01 | Ôm sát phần nhìn thấy: box là hình chữ nhật nhỏ nhất bao hết phần nhìn thấy của vật; dư tối đa 2 px mỗi cạnh (vật cao ≥ 50 px). Gồm gương chiếu hậu, tay lái, ăng-ten gắn cố định. Không gồm bóng đổ, nước bắn, vệt nhòe kéo dài ra ngoài thân vật. |
| R-02 | Vật bị che: vẽ box cho phần nhìn thấy, không đoán phần khuất. Gán `occluded_level` theo 2.2. Hai box được phép chồng lên nhau. |
| R-03 | Vật bị cắt mép ảnh: vẫn gán, kéo box sát mép ảnh, `truncated = yes` khi ≥ 10%. Nếu phần nhìn thấy nhỏ hơn 30% thân và không xác định được lớp thì không gán (R-17). |
| R-04 | Vật nhỏ: vật cao < 20 px thì không vẽ box riêng. Nhiều vật nhỏ nằm sát nhau thì phủ một `ignore_region` quanh cụm. Vật cao ≥ 20 px phải có box, không được để nằm trong `ignore_region`. |
| R-05 | Đám đông / xe dày đặc: vẽ box cho từng vật tách được (còn thấy ranh giới và cao ≥ 20 px). Phần sau, nơi các vật dính vào nhau không tách được, phủ `ignore_region`. Quy trình: gán từ gần ra xa; dừng khi không tách được nữa thì đặt vùng ignore. |
| R-06 | Vật không thật (tượng, ma-nơ-canh, đồ chơi, mô hình thu nhỏ, hình in, linh vật): không gán, kể cả khi hình dạng giống vật thật. Xe thật chở bên trên vẫn gán (R-12). |
| R-07 | Phản chiếu (gương chiếu hậu, mặt nước, kính, đường ướt): không gán vật trong phản chiếu. |
| R-08 | Người đi xe máy (và các xe hở khác): vẽ hai loại box tách nhau `motorcycle` = thân xe, bánh, tay lái, hàng chằng trên xe, không gồm người. `person` = từng người trên xe (lái và từng người ngồi sau), ôm phần thân người nhìn thấy. Hai box chồng nhau là bình thường. Người trên xe đạp, xích lô, tuk-tuk, thùng bán tải làm tương tự: người một box, xe một box. |
| R-09 | Hàng hóa chằng trên xe (bao, chậu, ống dài): gộp vào box của xe cho đến hết phần nhìn thấy. Lý do: hàng là phần vật cản thực tế trên đường. Hàng vượt quá thân xe rõ (cao hoặc dài gấp đôi xe) thì tick `can_review`. |
| R-10 | Xe chở xe (img_002): vẽ một box `truck` cho cả đầu kéo và rơ-moóc; và một box `car` cho từng xe nhìn rõ ≥ 20 px đang nằm trên xe chở. Xe bị che bởi khung giá thì `occluded_level` theo tỉ lệ nhìn thấy. |
| R-11 | Xe đỗ / trưng bày thật xe thật đỗ ngoài đường, trong bãi, trong nhà trưng bày vẫn gán như xe đang chạy (img_030, img_024, img_007). Xe không có người cũng gán. |
| R-12 | Xe thật nhưng hình dạng lạ (xe tự chế, xe diễu hành, xe chạy được có biển số và người lái, như img_019): gán lớp gần nhất (`car`) và tick `can_review`. Vật nhỏ hơn tỉ lệ thật đặt trên xe khác (xe vàng trên mui img_024) là mô hình → R-06. |
| R-13 | Nhòe chuyển động gán nếu còn nhận ra lớp. Box ôm phần thân nhòe thấy rõ nhất, không kéo hết vệt mờ. Nhòe nặng tới mức không nhận lớp thì không gán và nếu vùng lớn thì phủ `ignore_region` (img_014 phần nhòe phía sau hai người đi bộ). |
| R-14 | Ban đêm, ngược sáng, đèn lóa vẫn gán nếu thấy hình dáng thân vật (không chỉ riêng đèn). Chỉ thấy đèn pha mà không thấy thân thì không gán. |
| R-15 | Bộ phận xe chủ (ego) và camera: gương, mũi xe nơi gắn camera (img_020) không gán. |
| R-16 | Người trong ô tô kín (qua kính): không gán. Người ngồi trong xe hở (tuk-tuk, thùng bán tải, xích lô) thì gán. |
| R-17 | Không xác định được lớp phần nhìn thấy quá ít hoặc quá lạ nên không biết là xe gì (img_033: gương và cửa trắng cận cảnh) → không gán; ghi vào `image_issues.csv`: ảnh, vùng, lý do. |
| R-18 | Một vật = một box không vẽ hai box cho cùng một vật. Một xe có hai phần dính liền (đầu kéo + rơ-moóc, xe + sidecar) là một vật. |

Kết quả: cùng quy tắc cho ra số box dự đoán được ở cả ba ảnh.

## 4. Ca khó
| Ảnh | Tình huống | Rule ID | Quyết định | Lý do |
|---|---|---|---|---|
| img_001 | Xe bán tải cũ đỗ; người ngồi bàn ăn phía sau bị che một phần | R-02, R-11 | `truck` cho bán tải; từng người nhìn thấy rõ → `person` (`occluded_level` 1–2) | Bán tải có thùng hàng → `truck`; xe đỗ vẫn gán |
| img_002 | Xe chở xe, 8 ô tô đặt trên | R-10 | 1 `truck` (đầu kéo + rơ-moóc) + 1 `car` cho từng xe thấy rõ | Xe thật có thể thấy được; gán cả để mô hình biết xe chở xe là vật liên quan |
| img_003 | Người gánh hàng rong; xe đạp bên trái; xe máy đỗ phía xa | R-04, R-08 | Người gánh → `person`; xe đạp → `bicycle`; xe máy xa cao < 20 px → `ignore_region` | Gánh hàng là vật mang theo, không phải xe |
| img_007 | Gara ban đêm: xe tải Isuzu thùng kín, bán tải Hilux phía sau | R-11, R-14 | Cả hai → `truck` | Bán tải = `truck`; đèn xe sáng không làm mất thân xe |
| img_008 | Bãi xe máy dày đặc ban đêm; người mặc áo cam trên xe | R-05, R-08, R-14 | Xe và người gần → box riêng; phần xa dính nhau → `ignore_region` | Dừng gán khi không tách được ranh giới |
| img_013 | Ban đêm, đường ướt, người và xe rất nhỏ ở xa; nón giao thông | R-04, R-07 | Vật cao < 20 px → `ignore_region`; phản chiếu trên đường ướt không gán; nón không gán | Vật nhỏ; phản chiếu; nón không có lớp |
| img_014 | Hai người đi bộ nét rõ ở tiền cảnh; xe máy phía sau nhòe nặng | R-13 | 2 `person`; xe nhòe không nhận ra lớp → không gán (hoặc `ignore_region` nếu vùng lớn) | Nhòe nặng không đủ thông tin |
| img_019 | Xe diễu hành giả tưởng màu vàng có biển số, người lái bên trong, linh vật chuột; đám đông sau hàng rào | R-12, R-06, R-05 | Xe: `car` + `can_review`; chuột: không gán; người lái → `person`; đám đông: người gần tách được → `person`, phần dính nhau → `ignore_region` | Xe chạy thật có người lái; linh vật là vật giả |
| img_020 | Gương chiếu hậu có hình xe và đường phản chiếu | R-07, R-15 | Không gán | Phản chiếu; bộ phận xe chủ |
| img_021 | Hàng trăm xe máy và người dày đặc ở ngã tư | R-05, R-08 | Vài xe gần → `motorcycle` + `person`; phần xa → `ignore_region` | Gán từ gần ra xa |
| img_022 | Ảnh đen trắng, mô tô có thùng bên giữa đường rừng, nhỏ | R-04, R-18 | 1 `motorcycle` ôm cả thùng bên; nếu cao < 20 px thì không gán | Sidecar là một vật |
| img_029 | Ảnh đen trắng; xe máy chở ống dài nhô ra rất xa; người đạp xe bên cạnh | R-09, R-08 | `motorcycle` ôm cả ống dài (`can_review`); `person` × 2; xe đạp → `bicycle` | Hàng chằng trên xe gộp vào box; box rất dài nên tick hỏi |
| img_030 | Bãi gửi xe máy dày đặc, người coi xe mặc áo xanh | R-05, R-11 | Xe gần → mỗi xe một box; phần xa chồng chéo → `ignore_region`; người coi xe → `person` | Xe đỗ vẫn gán |
| img_031 | Phố đêm mưa, đèn phản chiếu trên đường; xe buýt, ô tô nhỏ ở xa | R-07, R-04, R-14 | Xe ≥ 20 px → gán (`car`, `bus`); phản chiếu và đèn không gán; vật < 20 px → `ignore_region` | Phản chiếu; đêm |
| img_032 | Hàng dài người chờ ở trạm; ô tô Honda xanh bị cắt mép; nón giao thông | R-05, R-03 | Người cao ≥ 20 px tách được → `person`; người dính nhau → `ignore_region`; `car` truncated; nón không gán | Gán từ gần ra xa |
| img_033 | Ma-nơ-canh; ảnh in phía trái; gương và cửa trắng cận cảnh bên phải | R-06, R-17 | Ma-nơ-canh và hình in: không gán; gương, cửa không xác định lớp → không gán, ghi `image_issues.csv` | Vật không thật; không đủ thông tin để chọn lớp |
| img_039 | Phố, xe máy đỗ bên trái; người và xe máy đi xa | R-11, R-04 | Xe đỗ → `motorcycle`; người/xe xa cao ≥ 20 px → gán, nhỏ hơn → `ignore_region` | Xe đỗ vẫn gán |
| img_040 | Taxi cận cảnh bị cắt mép; người đội mũ bảo hiểm đen sát ống kính; tuk-tuk và xe buýt phía sau | R-03, R-08, R-02 | `car` (taxi, `truncated = yes`); `person` (người đội mũ); xe máy của người đó chỉ thấy gương/tay lái → `motorcycle` `truncated = yes` `can_review`; `three_wheeler`, `bus`, `car` phía sau | Vật gần phải gán đủ; xe máy chỉ lộ ít nhưng đã nhận ra |
## 5. QC và phiên bản

- Ngưỡng QC áp dụng: vật cao < 20 px là vật nhỏ (R-04); IoU đạt 0.85 với box cao ≥ 50 px, 0.7 với box nhỏ hơn; ghép cặp box với IoU ≥ 0.5; IAA lớp ≥ 95%; ảnh lỗi ≤ 2% mới Release.
- Ca mơ hồ: tick `can_review`.
