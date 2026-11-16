# Guideline gán nhãn — v1 — Phát hiện người và phương tiện

- Phiên bản: v1
- Ngày: 16/11/2026
- Người viết / duyệt: Nguyễn Hồ Bắc
- Loại nhãn: bounding box trên ảnh đường phố
- Công cụ: CVAT, xuất COCO 1.0

## 1. Mục tiêu

Guideline này dùng để gán nhãn người và phương tiện trong ảnh đường phố, phục vụ
huấn luyện mô hình phát hiện đối tượng cho camera giao thông hoặc xe tự hành.

Mỗi đối tượng nhìn thấy được phải có đúng một box và một class trong taxonomy.
Gán sai class, bỏ sót đối tượng hoặc vẽ box lệch đáng kể làm mô hình học sai;
đặc biệt nguy hiểm với `person`, `motorcycle` và các đối tượng nhỏ hoặc bị che.

## 2. Lớp và thuộc tính

### Lớp

| Lớp | Định nghĩa một câu | Ví dụ | Phản ví dụ / dễ nhầm với |
|---|---|---|---|
| `car` | Ô tô con hoặc SUV dùng để chở người, không có thùng hàng tách biệt. | Sedan, hatchback, SUV. | `van` nếu là xe thùng kín; `truck` nếu có thùng hàng riêng. |
| `truck` | Xe tải có phần cabin và thùng hoặc sàn chở hàng tách biệt. | Xe tải thùng, xe ben, xe đầu kéo. | Ô tô con kéo rơ-moóc nhỏ; `van` có khoang hàng kín liền thân. |
| `van` | Xe thùng kín cỡ nhỏ hoặc xe chở người có thân cao, khoang sau liền với cabin. | Minivan, xe van giao hàng. | `car` nếu có dạng ô tô con; `truck` nếu có thùng hàng tách biệt. |
| `motorcycle` | Phương tiện hai bánh có động cơ, gồm xe máy và mô tô. | Xe máy, mô tô, scooter. | Xe đạp không động cơ; người điều khiển được gán riêng là `person`. |
| `person` | Người nhìn thấy trong ảnh, dù đang đi bộ, ngồi hoặc đứng trên phương tiện. | Người đi bộ, tài xế, hành khách. | Hình người trên biển quảng cáo, ma-nơ-canh, tượng hoặc hình in. |
| `ignore_region` | Vùng hình chữ nhật cần bỏ qua vì không thể gán tin cậy từng đối tượng trong vùng đó. | Vùng quá đông hoặc bị che khuất nghiêm trọng. | Không dùng để thay thế box của một đối tượng nhìn thấy rõ. |

`ignore_region` là vùng bỏ qua, không phải một đối tượng. Không tạo class mới trong
quá trình gán nhãn. Vật không thuộc năm class đối tượng và không cần đánh dấu để
huấn luyện thì không gán; nếu vùng đó làm việc đánh giá không đáng tin cậy thì
dùng `ignore_region`.

### Thuộc tính

| Thuộc tính | Mức cố định | Quy tắc áp dụng |
|---|---|---|
| `occluded_level` | `0` | Thấy gần như toàn bộ đối tượng; phần bị che dưới 10%. |
| `occluded_level` | `1` | Bị che một phần nhưng vẫn nhận diện rõ; che từ 10% đến dưới 30%. |
| `occluded_level` | `2` | Bị che nhiều nhưng còn đủ dấu hiệu để xác định class; che từ 30% đến dưới 70%. |
| `occluded_level` | `3` | Bị che từ 70% trở lên nhưng vẫn còn dấu hiệu đáng tin cậy để gán box. |
| `truncated` | `no` | Toàn bộ box của đối tượng nằm trong ảnh, không bị mép ảnh cắt. |
| `truncated` | `yes` | Đối tượng bị mép ảnh cắt ở bất kỳ phía nào. |
| `can_review` | `false` | Người gán chắc chắn về class, box và thuộc tính. |
| `can_review` | `true` | Có điểm mơ hồ cần người khác xem lại; phải ghi lý do trong nhật ký QC. |

Nếu không ước lượng được chính xác phần bị che, chọn mức bảo thủ cao hơn và bật
`can_review`. Các thuộc tính không áp dụng cho `ignore_region` dùng giá trị mặc định.

## 3. Quy tắc vẽ box

1. Vẽ một box cho mỗi đối tượng thuộc `car`, `truck`, `van`, `motorcycle` hoặc
   `person`; không gộp nhiều đối tượng vào một box.
2. Box ôm sát toàn bộ phần đối tượng nhìn thấy. Không mở rộng box vào vùng nền,
   nhưng vẫn suy ra kích thước đầy đủ của đối tượng bị che khi phần còn lại đủ
   bằng chứng.
3. Với đối tượng bị che, box bao quanh phần bị che dự kiến nếu hình dạng và vị trí
   có thể suy ra; đặt `occluded_level` theo tỷ lệ bị che.
4. Với đối tượng bị cắt ở mép ảnh, box dừng tại mép ảnh và đặt `truncated=yes`.
5. Người và phương tiện là hai đối tượng độc lập: người lái xe hoặc hành khách
   được gán `person`, phương tiện được gán class phương tiện tương ứng.
6. Không gán box cho phản chiếu, hình in, ảnh trên màn hình, tượng, ma-nơ-canh
   hoặc đồ chơi nếu không phải đối tượng thật trong cảnh.
7. Không gán xe chủ (ego vehicle) nếu chỉ thấy một phần thiết bị hoặc thân xe
   đang chụp ảnh; nếu một phương tiện thật xuất hiện rõ trong ảnh thì vẫn gán.
8. Đối tượng có chiều cao box dưới 20 px không gán như đối tượng thông thường;
   nếu nằm trong vùng đông hoặc không thể xác định tin cậy thì đưa vùng đó vào
   `ignore_region`. Đối tượng cao từ 20 px trở lên vẫn phải gán nếu nhận diện được.
9. Đám đông không được gán một box chung. Gán từng người nhìn thấy rõ; dùng
   `ignore_region` cho phần còn lại nếu không thể tách riêng đáng tin cậy.
10. Không dùng `ignore_region` để che lỗi bỏ sót một đối tượng rõ ràng hoặc để
    tránh chọn class giữa `car`, `truck`, `van` và `motorcycle`.

## 4. Ca khó

| Ca | Tình huống | Rule ID | Quyết định | Lý do |
|---|---|---|---|---|
| R-01 | Người đang ngồi trên xe máy | R-01 | Gán một `person` và một `motorcycle` nếu cả hai nhìn thấy. | Người và phương tiện là hai thực thể độc lập. |
| R-02 | Xe bị mép ảnh cắt | R-02 | Gán box phần nhìn thấy, đặt `truncated=yes`. | Không kéo box ra ngoài ảnh. |
| R-03 | Xe bị vật khác che một phần | R-03 | Gán box theo hình dạng có thể suy ra, đặt `occluded_level` theo tỷ lệ che. | Phần bị che vẫn thuộc cùng đối tượng. |
| R-04 | Vật thể cao dưới 20 px | R-04 | Không gán box đối tượng; nếu là một vùng không thể đánh giá thì dùng `ignore_region`. | Dưới ngưỡng tối thiểu không đủ tin cậy cho QC. |
| R-05 | Biển quảng cáo, hình in, tượng hoặc đồ chơi hình người/xe | R-05 | Không gán class đối tượng. | Đây không phải đối tượng thật trong cảnh. |
| R-06 | Nhiều người hoặc xe chồng lấn, không tách được | R-06 | Gán các box nhận diện chắc chắn; đánh dấu `can_review=true` hoặc dùng `ignore_region` cho phần mơ hồ. | Không tự suy đoán class/biên box. |
| R-07 | Không phân biệt chắc chắn `car`, `van` và `truck` | R-07 | Chọn class có bằng chứng mạnh nhất, bật `can_review=true` và ghi lý do. | Không tạo class tạm ngoài taxonomy. |

Nếu chưa chốt được ca khó, vẫn gán nhãn tốt nhất có thể, bật `can_review=true`
trên box liên quan và ghi `Rule ID` cùng lý do trong nhật ký QC. Ca ảnh hưởng đến
nhiều box phải ghi thêm vấn đề cấp ảnh.

## 5. QC và phiên bản

### Ngưỡng QC

- Chiều cao box tối thiểu: `20 px`.
- Với vật lớn (chiều cao từ `50 px`): IoU giữa hai box phải đạt ít nhất `0.85`.
- Với vật nhỏ (chiều cao dưới `50 px`): IoU giữa hai box phải đạt ít nhất `0.70`.
- IAA dùng IoU tối thiểu `0.85` và cùng class tối thiểu `0.95`.
- Hai box được ghép cặp khi IoU đạt ít nhất `0.50`.
- Tỷ lệ lỗi tối đa trên mỗi ảnh: `2%`.
- Ca có `can_review=true` phải được người duyệt hoặc coach quyết định trước khi
  phát hành nhãn cuối.

Người gán chịu trách nhiệm tạo nhãn ban đầu; người QC kiểm bằng script và kiểm
tra mắt các box bị flag. Mọi quyết định khác với guideline phải có ảnh, Rule ID,
lý do và người quyết định trong nhật ký QC.

### Lịch sử thay đổi

| Phiên bản | Thay đổi | Lý do |
|---|---|---|
| v1 | Chuẩn hóa năm class đối tượng theo taxonomy; định nghĩa ngưỡng che/cắt/vật nhỏ; bổ sung quy tắc box, ca khó và ngưỡng QC. | Loại bỏ cách hiểu khác nhau của guideline v0 và làm nhãn có thể kiểm tra, tái lập. |
