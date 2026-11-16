# Guideline gán nhãn — đề xuất sau khảo sát — 104

- Phiên bản: proposal-104-v1
- Ngày khảo sát: 2026-11-16
- Mã thành viên nhận bản đề xuất: 104
- Khảo sát và soạn đề xuất: Codex (AI), theo yêu cầu của 104.
- Phạm vi: xem tổng quan 40/40 ảnh; mở lớn thêm các ca khó. Chưa rà từng đối tượng để vẽ box.
- Trạng thái: đề xuất có AI hỗ trợ, chờ 104 kiểm lại và xác nhận; không thay cho bằng chứng khảo sát độc lập của 104.
- Công cụ dự kiến: CVAT, Rectangle, xuất COCO 1.0.

## 1. Mục tiêu

Nhãn phục vụ mô hình phát hiện người thật và phương tiện cơ giới trong cảnh đường phố 2D. Phạm vi đề xuất gồm người, ô tô con, xe tải/bán tải, van, xe buýt, xe máy và tuk-tuk. Xe đạp/xích lô không động cơ ngoài phạm vi phương tiện, nhưng người sử dụng chúng vẫn thuộc `person`.

Bỏ sót người làm thiếu mẫu quan trọng; gộp người và xe làm sai ranh giới lớp; gán tượng như vật thật làm nhiễu dữ liệu. Bộ 40 ảnh phục vụ thực hành, chưa đủ chứng minh dữ liệu đại diện cho triển khai giao thông thực tế. Đây là một phương án thiết kế để nhóm thảo luận, không phải đáp án chính thức của coach.

## 2. Lớp và thuộc tính

### 2.1. Taxonomy đề xuất

Mỗi đối tượng thuộc một lớp. Bổ sung `bus`, `tuk_tuk` so với v0. Chưa sửa taxonomy chung; chỉ đồng bộ sau buổi thống nhất Pha 2.

| Lớp | Định nghĩa | Ví dụ quan sát | Phản ví dụ / dễ nhầm |
|---|---|---|---|
| `car` | Ô tô con, gồm sedan, hatchback, station wagon và SUV | Xe đen `img_023`; xe con trên sàn `img_002` | Bán tải `img_037` là truck; đồ chơi `img_038` bị loại |
| `truck` | Xe chở hàng có cabin và sàn/thùng hàng phân biệt; gồm bán tải có hoặc không có nắp thùng | `img_001`, `img_002`, `img_036`, `img_037` | Nắp thùng cao không tự biến bán tải thành van; tượng `img_027` bị loại |
| `van` | Xe thân kín liền khối dạng van/minivan, không có thùng bán tải tách biệt | Xe bạc sau người đi xe ở `img_005`; van `img_016` | Xe tải phủ bạt `img_036`; bus `img_009` |
| `bus` | Xe buýt/xe khách có khoang nhiều hành khách, nhận diện bằng thân dài và bố trí cửa/cửa sổ hành khách | `img_009`, `img_037`, `img_040` | Van cỡ nhỏ; không suy lớp chỉ từ màu xe |
| `motorcycle` | Xe máy/mô tô có động cơ, gồm mô tô gắn thùng bên hông như một cụm xe | `img_005`, `img_026`, sidecar `img_022` | Xe đạp `img_029`; tuk-tuk có cabin |
| `tuk_tuk` | Xe ba bánh có động cơ, cấu trúc cabin/khoang chở người hoặc hàng riêng | `img_004`, `img_016`, `img_035` | Xích lô đạp `img_023`; sidecar `img_022` |
| `person` | Người thật nhìn thấy trực tiếp, kể cả trên xe hoặc sau kính trong | `img_014`, `img_026`, người đạp xích lô `img_023` | Tượng `img_017`, chân dung in `img_018`, ma-nơ-canh `img_033` |
| `ignore_region` | Vùng không gán từng vật theo điều kiện vật nhỏ/cụm không tách được | Vùng nền đông và nhỏ cần kiểm ở `img_021` | Không dùng thay cho một ca chưa chắc lớp |

Xe đạp/xích lô không động cơ, động vật, hàng rời và vật mô phỏng không gán lớp đối tượng. Không mặc định vẽ ignore cho mọi vật ngoài phạm vi. Người thật cạnh chúng vẫn được xét riêng. Vật chưa thuộc lớp nào ghi vấn đề cần chốt, không ép vào lớp gần giống.

### 2.2. Thuộc tính

Các mức dưới đây là quy ước đề xuất để 104 thử và nhóm thảo luận, không phải ngưỡng che khuất bắt buộc của lab.

| Thuộc tính | Giá trị | Nghĩa |
|---|---|---|
| `occluded_level` | `0` | Không có phần bị vật khác che trong phần đối tượng nằm trong ảnh |
| `occluded_level` | `1` | Tỷ lệ bị che 0% < p ≤ 30% |
| `occluded_level` | `2` | 30% < p ≤ 70% |
| `occluded_level` | `3` | 70% < p < 100%, vẫn đủ bằng chứng nhận diện vật |
| `truncated` | `no`, `yes` | `yes` khi đường bao vật bị cắt do tiếp tục ra ngoài mép ảnh |
| `can_review` | `false`, `true` | `true` khi box cần kiểm lại về lớp, biên hoặc thuộc tính |

Ước lượng p bằng phần diện tích đường bao vật trong khung ảnh bị vật khác chắn chia diện tích đường bao đầy đủ ước lượng của vật trong khung ảnh. Đây là ước lượng thị giác để chọn mức, không phải số đo mask. Không tính phần ngoài ảnh vào occlusion. Không dùng mức 3 để chỉ không biết; bất định gần ngưỡng thì bật can_review. Che hoàn toàn, không có dấu vết trực tiếp: không tạo box suy đoán.

Mũ bảo hiểm, khẩu trang và quần áo là diện mạo người, không tự làm người mang thuộc tính bị che; người/xe khác chắn cơ thể mới tính che. Mờ chuyển động không phải che khuất. Cờ occluded mặc định của CVAT khác thuộc tính `occluded_level` mà script đọc.

## 3. Quy tắc vẽ box

### R-01 — Ôm phần nhìn thấy

Box là hình chữ nhật nhỏ nhất bao các phần nhìn thấy của vật trên ảnh gốc, không thêm lề hoặc kéo ra ngoài ảnh. Không khôi phục đường bao phần bị khuất. Người gồm cơ thể, mũ và quần áo, không chủ động mở rộng theo túi/gánh hàng. Xe gồm thân, bánh và bộ phận gắn cố định như gương; không mở rộng theo bóng, phản chiếu hoặc hàng rời.

### R-02 — Một vật một box

Một đối tượng có một box dù thấy nhiều mảnh rời. Chỉ bao các mảnh xác định chắc là cùng vật; khoảng trống giữa chúng có thể nằm trong box. Không tạo nhiều box cho một vật và không gộp các xe sát nhau.

### R-03 — Tách người và phương tiện

Một người trên một xe máy, nếu cả hai đủ điều kiện: hai box `person` và `motorcycle`. Xe chở hai người: ba box nếu cả ba đối tượng đủ điều kiện. Đây là quy tắc đếm theo cấu trúc, không phải tổng box cả ảnh. Box xe không chủ động bao người, box người không bao xe; hai box có thể chồng nhau. Thử nhất quán trên `img_005` và `img_026`; ảnh sau thấy hai người trên cùng xe. Người trên xe đạp/xích lô vẫn xét `person`.

### R-04 — Xe chở xe, sidecar và hàng hóa

Xe vận chuyển `img_002` xét `truck`, từng xe được chở xét riêng `car`. Đầu kéo/rơ-moóc gắn thành tổ hợp được bao như một xe vận chuyển; không mở biên theo xe được chở chỉ vì chúng nhô lên cao. Sidecar `img_022`: một `motorcycle` bao mô tô và thùng bên hông gắn liền; người xét riêng theo phần thật nhìn thấy.

Hàng rời `img_012`, bao tải chất cao `img_035`, tượng ngựa `img_028` không quyết định biên box xe. Mui/bạt thùng gắn theo kết cấu xe thuộc xe. Xe đỗ/trưng bày vẫn có thể là xe thật; không loại chỉ vì đặt trong nhà. Thân xe rời chưa rõ tính hoàn chỉnh, như xe vàng trên nóc `img_024`, cần review.

### R-05 — Che khuất và kính

Gán khi phần nhìn thấy đủ để nhận diện lớp và một instance. Không suy ra người từ ghế/mũ rời. Người thật nhìn xuyên kính vẫn xét `person`; ảnh phản chiếu trên kính bị loại. Không phân biệt chắc được hai tình huống thì review. Box theo phần nhìn thấy, thuộc tính occlusion theo mục 2.2.

### R-06 — Cắt mép

Box dừng tại biên ảnh khi đường bao vật tiếp tục ra ngoài, đặt truncated=yes. Chạm biên nhưng thấy trọn vật chưa đủ để đặt yes. Một vật có thể vừa bị che vừa cắt mép. Ví dụ: `img_005`, `img_015`, `img_026`, `img_040`.

### R-07 — Vật mô phỏng và phản chiếu

Loại tượng, ma-nơ-canh, hình in, đồ chơi và phản chiếu khỏi các lớp vật thật. Áp dụng cho `img_017`, `img_018`, `img_020`, `img_027`, `img_033`, `img_038`; loại phản chiếu đường ướt `img_015`, `img_031`. Không loại người thật cạnh tượng hay xe thật chở tượng. Nhân vật trang trí trên xe `img_019` không phải person.

### R-08 — Vật nhỏ

Giữ ngưỡng lab: cao < 20 px dùng ignore_region. Đo chiều cao bbox phần nhìn thấy tại kích thước ảnh gốc, trước khi phóng màn hình; cao đúng 20 px không bị loại theo ngưỡng. Vật bị che/cắt mép cũng đo phần nhìn thấy, không suy chiều cao ngoài ảnh. Vùng ignore bám vật nhỏ, không phủ vật đủ lớn bên cạnh. Không đo trên contact sheet; `img_013`, `img_025`, `img_031` cần đo lúc gán.

### R-09 — Đám đông/bãi xe

Ưu tiên từng instance rõ. Đề xuất chỉ ignore phần cụm có từ ba đối tượng chồng lấp mà sau khi xem ảnh gốc ở 200% vẫn không xác định được số instance và biên nhìn thấy từng vật. Ba vật tách biệt không tự thành ignore. Giữ các box rõ ở tiền cảnh, không phủ cả ảnh đông. Thử trên `img_021`, `img_030`, `img_032`. Tiêu chí này là lựa chọn thiết kế cần nhóm xác nhận; khi chưa rõ ghi review thay vì che bằng ignore.

### R-10 — Xe chủ (ego)

Loại phần xe gắn camera nếu có bằng chứng rõ, như gương/cửa sát máy ở `img_020`. Không mặc định mọi thùng xe tiền cảnh đều là ego. Riêng `img_012` chưa chứng minh chắc vị trí máy ảnh từ ảnh đơn: ghi review trước khi loại xe tiền cảnh.

### R-11 — Ngoài phạm vi và xe dễ nhầm

Xe đạp/xích lô không động cơ ở `img_006`, `img_023`, `img_029`, `img_039` ngoài phạm vi phương tiện, người vẫn được xét. Bán tải nắp thùng cao `img_037` vẫn là truck vì nền tảng cabin/thùng tách biệt. Xe tải nhỏ phủ bạt `img_036` không thành van. Tuk-tuk và sidecar phân theo cấu trúc, không chỉ đếm bánh. Chưa đủ dấu hiệu thì review.

### R-12 — Bất định và mờ chuyển động

Vẽ được box nhưng chưa chắc: dùng lớp/thuộc tính tạm và can_review=true kèm lý do. Chưa vẽ/nhận diện được: ghi tên ảnh, vùng và vấn đề để nhóm tổng hợp `image_issues.csv` sau khi khóa nhãn độc lập. Vùng mờ `img_014`, `img_015` chỉ gán khi nhận diện được vật và biên chính; không kéo box theo toàn bộ vệt sáng mờ. Chưa rõ biên thì review, không tự đổi occluded_level vì mờ.

## 4. Khảo sát 40 ảnh và ca khó

Bảng là quan sát/hướng xử lý đề xuất của AI, chưa phải COCO, tổng số box hoặc quyết định calibration của nhóm. Ca ghi review chưa được coi là đã xử lý.

| Ảnh | Quan sát | Rule ID | Đề xuất và lý do |
|---|---|---|---|
| `img_001.jpg` | Bán tải cạnh quán, người bị bàn/xe chắn | R-01, R-05, R-11 | Truck cho bán tải; người riêng theo phần nhìn thấy, không bao cả bàn |
| `img_002.jpg` | Xe chở nhiều ô tô hai tầng | R-02, R-04 | Truck cho xe vận chuyển; car riêng cho từng xe được chở, kể cả xe khuất nhận diện được |
| `img_003.jpg` | Người bán hàng, người đi xe, xe đạp và gánh hàng | R-01, R-03, R-11 | Tách người/xe; không kéo box người theo gánh; xe đạp ngoài phạm vi |
| `img_004.jpg` | Hai tuk-tuk xanh đỗ cạnh nhau | R-02, R-11 | Hai instance tuk_tuk riêng; người trong cabin chỉ gán nếu nhìn thấy thật |
| `img_005.jpg` | Người/xe máy chồng lấp trước van bạc, cắt mép | R-03, R-05, R-06 | Tách từng người và xe; không suy số xe từ số đầu người; phân biệt che/cắt |
| `img_006.jpg` | Xe máy và xe đạp cùng đường | R-03, R-11 | Xe máy trong phạm vi, xe đạp ngoài; người sử dụng cả hai vẫn xét |
| `img_007.jpg` | Bán tải và xe tải thùng trong khu mái che | R-05, R-11 | Cả hai truck; đỗ trong nhà không phải lý do loại |
| `img_008.jpg` | Người và xe máy đỗ dày ban đêm | R-02, R-03, R-09 | Xe không người vẫn gán; giữ instance rõ, ignore chỉ cụm đủ điều kiện |
| `img_009.jpg` | Xe chở khách dài trước dãy nhà | R-11 | Bus riêng, không nhập van; người/xe nền xét riêng |
| `img_010.jpg` | Người bán hàng, người ngồi xe và hàng hóa | R-01, R-03 | Tách người và xe; hàng/quầy không quyết định biên người |
| `img_011.jpg` | Điêu khắc lớn và người thật ở khu phía sau | R-07, R-08 | Loại tượng; xét người thật, đo người nhỏ ở ảnh gốc |
| `img_012.jpg` | Thùng bán tải chứa hàng sát máy ảnh | R-04, R-10, R-12 | Không bao hàng theo truck; review xe có phải ego, chưa tự loại |
| `img_013.jpg` | Phố đêm, người/xe ở xa | R-08, R-12 | Đo vật nhỏ trên ảnh gốc; thiếu sáng không tự là ngoài phạm vi |
| `img_014.jpg` | Hai người rõ, xe/người nền mờ mạnh | R-05, R-12 | Người rõ gán bình thường; vùng mờ review khi thiếu biên, mờ không phải che |
| `img_015.jpg` | Xe cắt hai mép, xe chạy mờ và phản chiếu đường ướt | R-06, R-07, R-12 | Truncated cho xe cắt mép; loại phản chiếu; review biên xe mờ |
| `img_016.jpg` | Tuk-tuk, xe máy, van và người sát mép | R-03, R-06, R-11 | Phân lớp theo kết cấu, tách người/xe; xét cắt mép từng vật |
| `img_017.jpg` | Tượng người cưỡi ngựa | R-07 | Loại người trên tượng khỏi person; ca loại có quy tắc |
| `img_018.jpg` | Chân dung biển quảng cáo, xe thật sau hàng rào | R-05, R-07 | Loại chân dung; xe thật vẫn xét theo phần nhìn thấy |
| `img_019.jpg` | Xe diễu hành vàng, người lái, nhân vật trang trí, khán giả | R-03, R-07, R-09, R-12 | Đề xuất car cho xe thật, review nếu cấu trúc chưa chắc; người lái riêng; loại nhân vật trang trí |
| `img_020.jpg` | Gương chiếu hậu, phản chiếu đường và phần xe sát máy | R-07, R-10 | Loại phản chiếu và ego; không tạo xe chỉ từ hình trong gương |
| `img_021.jpg` | Dòng người/xe máy rất đông, xa nhỏ | R-03, R-08, R-09 | Tách tiền cảnh; nền đo/ignore cục bộ, không phủ toàn dòng xe |
| `img_022.jpg` | Mô tô sidecar trong ảnh đen trắng | R-04, R-05 | Một motorcycle gồm thùng bên hông; người xét bằng dấu vết trực tiếp, không suy từ ghế |
| `img_023.jpg` | Người đạp xích lô, xe con và xe khác | R-03, R-11 | Person cho người đạp; loại xích lô; car cho xe con |
| `img_024.jpg` | Xe trưng bày, thân xe vàng trên nóc xe đen | R-04, R-12 | Xe thật rõ là car; vật vàng review tính hoàn chỉnh/thân vỏ, không suy khả năng vận hành |
| `img_025.jpg` | Lối đi ven biển, người xa và xe bên đường | R-08 | Xét vật thuộc phạm vi, đo chiều cao trước khi ignore |
| `img_026.jpg` | Hai người trên một xe máy, phần dưới xe bị cắt | R-03, R-05, R-06 | Cụm chính: hai person và một motorcycle nếu đủ điều kiện; thuộc tính xét riêng |
| `img_027.jpg` | Vật hình bán tải trên bệ tại nghĩa trang | R-07 | Loại tượng hình xe; không dùng hình dáng xe làm bằng chứng duy nhất |
| `img_028.jpg` | Bán tải chở tượng ngựa, xe đỏ phía sau | R-04, R-07, R-11 | Truck, car riêng; không mở truck theo tượng ngựa |
| `img_029.jpg` | Người, xe máy, xe đạp và thanh dài chắn chéo | R-01, R-03, R-05, R-11 | Thanh dài không thuộc biên người/xe; tính che khi chắn; xe đạp ngoài phạm vi |
| `img_030.jpg` | Bãi xe máy nhiều lớp, người và hình quảng cáo nền | R-02, R-07, R-09 | Từng xe rõ; ignore cụm không tách được; phân biệt người thật với hình in |
| `img_031.jpg` | Xe trên phố đêm và phản chiếu dưới đường | R-07, R-08, R-12 | Không nhân đôi theo phản chiếu; xe xa đo, thiếu sáng review |
| `img_032.jpg` | Đám đông bên kia đường, nhiều mức che | R-05, R-09 | Từng người rõ; chỉ ignore vùng không phân biệt instance |
| `img_033.jpg` | Ma-nơ-canh trong cửa hàng/kính | R-07 | Loại ma-nơ-canh khỏi person; không suy có người từ hình giống người |
| `img_034.jpg` | Người băng giao lộ, xe nền, người/xe sát mép phải | R-03, R-05, R-06 | Person riêng; tách người đi xe; kiểm truncated phía phải |
| `img_035.jpg` | Tuk-tuk chất bao tải cao, xe máy và ô tô khác | R-03, R-04, R-11 | Tuk_tuk không mở biên theo hàng nhô cao; không đổi truck chỉ vì chở hàng |
| `img_036.jpg` | Xe tải nhỏ xanh, thùng phủ bạt | R-04, R-11 | Truck; bạt thùng thuộc kết cấu xe, khác hàng rời |
| `img_037.jpg` | Bán tải trắng nắp thùng cao cạnh bus | R-11 | Truck cho bán tải; bus riêng; nắp thùng không làm thành van |
| `img_038.jpg` | Tủ đồ chơi có nhiều ô tô mô hình | R-07 | Loại đồ chơi; không dùng kích thước lớn làm bằng chứng xe thật |
| `img_039.jpg` | Xe máy, người đi bộ và người đi xe đạp | R-03, R-08, R-11 | Person vẫn xét; xe đạp ngoài phạm vi; vật xa cần đo/kiểm |
| `img_040.jpg` | Người trên xe tiền cảnh, taxi, tuk-tuk và bus nền | R-03, R-05, R-06, R-11 | Tách người/xe; taxi là car; tuk_tuk/bus riêng; phân biệt che/cắt |

Ưu tiên xác nhận: phạm vi loại xe đạp/xích lô; mức che khuất; tiêu chí ignore đám đông; ego ở img_012; xe đặc biệt img_019 và thân xe img_024. Ba ca review sau cùng cần người kiểm/bằng chứng, không được coi là đã chốt.

## 5. QC và phiên bản

### Ngưỡng cố định của lab

| Đại lượng | Ngưỡng / quy tắc |
|---|---|
| Vật nhỏ | Cao < 20 px |
| Ghép box IAA | Ghép 1–1, không phân biệt lớp, IoU ≥ 0.5 |
| IoU so box cao ≥ 50 px | ≥ 0.85 |
| IoU so box cao < 50 px | ≥ 0.7 |
| IAA | IoU TB ≥ 0.85; đồng thuận lớp ≥ 95%, chỉ trên cặp ghép được |
| Độ phủ | Đủ 100% lượt phân công trước khi đo IAA |
| Release | Duyệt toàn lô, ảnh lỗi ≤ 2%, không lỗi lặp theo lab, reviewer xác nhận |

Không có cặp thì IAA là N/A. Box chưa ghép đọc riêng; hai người có thể cùng sai dù IAA cao. Lô 40 ảnh có một ảnh lỗi là 2,5%, vượt ngưỡng. Luôn báo tử số/mẫu số theo ảnh và theo đối tượng. Quyết định theo thứ tự Hold → Rework → Release; thiếu bằng chứng không kết luận Release. Giữ nguyên mục rules của taxonomy.json.

### Trách nhiệm và lịch sử

104 kiểm lại đề xuất trước khi nhận làm bản cá nhân. Người chốt nhóm/reviewer chưa được chỉ định ở đây. Giữ nguyên bản cá nhân sau khi nộp; tạo v1.0 nhóm riêng sau buổi họp. Lượt gán độc lập dùng v1.0 đã khóa, không tự đổi quy tắc hoặc xem nhãn bạn khác.

Đổi nghĩa cách chọn vật/lớp/box/thuộc tính ở Pha 5 là semantic, phải rà cả lô theo workflow. Ca thực tế cần người chốt, rule, phạm vi, vết sửa và người kiểm lại thật; tài liệu này chưa ghi nhận các hoạt động đó.

| Phiên bản | Thay đổi | Cơ sở |
|---|---|---|
| draft-104 | Khung từ v0 và câu hỏi cần chốt | Bản nháp trước khảo sát |
| proposal-104-v1 | AI khảo sát 40 ảnh, đề xuất 8 lớp, R-01 đến R-12, bảng từng ảnh | Quan sát data/images, mở lớn ca khó; chờ 104 xác nhận |

Khai báo AI: Codex hỗ trợ xem ảnh, đề xuất quy tắc và soạn văn bản theo yêu cầu. 104 ghi cách kiểm lại thực tế trong ghi chú cá nhân; không ghi đã tự khảo sát/đã xác nhận khi chưa làm.
