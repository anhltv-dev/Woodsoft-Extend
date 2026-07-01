# Tài Liệu Tổng Hợp & Phân Tích Codebase Woodsoft Packing List Tool

Tài liệu này tổng hợp toàn bộ cấu trúc, tính năng, kiến trúc kỹ thuật và luồng dữ liệu của codebase **Woodsoft - Công cụ hỗ trợ Bao Gói & Đóng Kiện**.

---

## 1. Tổng Quan Dự Án

*   **Tên dự án:** Woodsoft — Công cụ hỗ trợ Bao Gói & Đóng Kiện
*   **Mục tiêu:** Cung cấp công cụ nền web gọn nhẹ (chạy trực tiếp trong trình duyệt mà không cần máy chủ back-end) giúp các xưởng sản xuất đồ gỗ nội thất nhập các file dữ liệu packing list (dạng `.xls`/`.xlsx` xuất từ phần mềm thiết kế 3D/CAM như Bazis-Mebelshik), phân tích dữ liệu chi tiết cấu thành, gộp thông tin, hiển thị theo các chế độ trực quan, tùy chỉnh và in tem/phiếu đóng gói chất lượng cao, đồng thời xuất ngược lại dữ liệu báo cáo dạng Excel chuyên nghiệp.
*   **Đối tượng người dùng:** Nhân viên quản lý kho, bộ phận bao gói đóng kiện, và nhân viên kỹ thuật sản xuất tại các nhà máy chế biến gỗ/sản xuất nội thất.

---

## 2. Cấu Trúc Thư Mục Codebase

Codebase hiện tại rất tinh gọn, bao gồm các tệp tin sau:

```text
📂 Woodsoft tool Packing list WL (Thư mục gốc)
 ├── 📄 woodsoft tool packing list.html   # File ứng dụng web chính (tất cả HTML, CSS, JS, Assets)
 └── 📂 vi du mode7                      # Thư mục chứa các file dữ liệu mẫu dạng Excel (.xls)
      ├── 📊 DREAMCITY-CT04-L1-CAN 15A-TB(T21+23+25).xls
      ├── 📊 DREAMCITY-CT04-L1-CAN 15A-TB(T22+24+26).xls
      └── 📊 DREAMCITY-CT04-L2-CH01-TA(T21-26).xls
```

---

## 3. Kiến Trúc Kỹ Thuật & Công Nghệ Sử Dụng

Ứng dụng được xây dựng theo kiến trúc **Single-File Web Application** (Ứng dụng Web Đơn Bản), chạy hoàn toàn phía Client (Client-Side).

### Các thư viện sử dụng (CDN):
1.  **SheetJS (xlsx.full.min.js - v0.18.5):** Dùng để đọc và phân tích cấu trúc các file Excel `.xls`/`.xlsx` tải lên, cũng như tạo và tải xuống file Excel báo cáo mới.
2.  **HTML2PDF (html2pdf.bundle.min.js - v0.10.1):** Hỗ trợ việc xuất bản in ra file PDF chất lượng cao.
3.  **Google Fonts (Roboto & Roboto Mono):** Cung cấp phông chữ trực quan, hiện đại, tối ưu hóa hiển thị bảng biểu số liệu.

### Hệ thống thiết kế & Giao diện (CSS Variable):
Giao diện ứng dụng sử dụng hệ màu hiện đại (Blue-Accent & Dark-Sidebar) với các biến CSS:
*   `--bg`: `#F0F4F8`, `--bg2`: `#E8EDF2`, `--bg3`: `#fff` (Màu nền hệ thống).
*   `--blue`: `#1A73E8`, `--blue-d`: `#1557B0` (Màu xanh thương hiệu).
*   `--t1`, `--t2`, `--t3`: Các mức độ tương phản chữ.
*   `--sans`: font chữ Roboto, `--mono`: font chữ Roboto Mono dành cho các cột hiển thị kích thước số liệu để căn thẳng hàng đẹp mắt.

---

## 4. Tính Năng Chi Tiết & Luồng Xử Lý Logic

### 4.1. Đọc và Phân Tích Dữ Liệu Excel (Upload & Parsing)
*   Hỗ trợ cả thao tác **Kéo & Thả (Drag & Drop)** lẫn **Chọn File truyền thống** thông qua đối tượng `FileReader` đọc dưới dạng `ArrayBuffer`.
*   **Logic phân tích dữ liệu (hàm `parseFile`):**
    *   Mỗi Sheet trong file Excel đại diện cho một kiện hàng (`kien`).
    *   **Dữ liệu kiện hàng (Header của Sheet):** 6 dòng đầu tiên chứa metadata của kiện bằng tiếng Nga (được xuất từ phần mềm thiết kế):
        *   `Заказ:` ➡️ Đơn hàng (`order`)
        *   `Размер:` ➡️ Kích thước kiện (`size`)
        *   `Объем:` ➡️ Thể tích kiện (`vol`)
        *   `Масса:` ➡️ Khối lượng kiện (`mass`)
        *   `Количество:` ➡️ Số lượng kiện (`qty`)
    *   **Dữ liệu chi tiết tấm gỗ (Parts):** Bắt đầu từ dòng thứ 8 (index 7). Các cột tương ứng là:
        1.  Cột A (`index 0`): Layer (Lớp)
        2.  Cột B (`index 1`): STT (Số thứ tự chi tiết)
        3.  Cột C (`index 2`): Tên chi tiết
        4.  Cột D (`index 3`): Số lượng (SL)
        5.  Cột E (`index 4`): Chiều dài (mm)
        6.  Cột F (`index 5`): Chiều rộng (mm)
        7.  Cột G (`index 6`): Chiều dày (mm)
        8.  Cột H (`index 7`): Vật liệu
        9.  Cột I (`index 8`): Đối tượng 3D (Tên cấu thành mô hình)

### 4.2. Các Phép Tính Toán Khối Lượng và Thể Tích Tự Động
*   **Diện tích chi tiết:** $\text{Dài} \times \text{Rộng} \times \text{Số lượng} / 10^6$ (m²).
*   **Thể tích chi tiết:** $\text{Dài} \times \text{Rộng} \times \text{Chiều dày} \times \text{Số lượng} / 10^9$ (m³).
*   **Khối lượng ước tính:** Thể tích nhân với khối lượng riêng của vật liệu tương ứng.
*   **Bảng tra cứu Khối lượng riêng (Density Lookup):**
    *   `mdf`: 750 kg/m³
    *   `melamine`: 750 kg/m³
    *   `lvl`: 600 kg/m³
    *   `vlt`: 600 kg/m³
    *   `gỗ (go)`: 650 kg/m³
    *   `cemboard` / `cemboa`: 1400 kg/m³
    *   *Mặc định các vật liệu khác:* 700 kg/m³.

### 4.3. Các Chế Độ Hiển Thị Giao Diện (Views)
Ứng dụng cung cấp 3 chế độ xem linh hoạt qua menu sidebar bên trái:
1.  **Bảng gộp chi tiết (`nv-merged`):** Gom toàn bộ chi tiết của tất cả các file và tất cả các kiện lại thành một bảng phẳng lớn duy nhất. Cho phép lọc nhanh theo từ khóa, lọc theo kiện cụ thể, theo file nguồn, hoặc theo vật liệu.
2.  **Gộp theo block (`nv-block`):** Hiển thị danh sách các kiện dưới dạng các thẻ màu riêng biệt. Mỗi thẻ đại diện cho một kiện, bao gồm đầy đủ metadata (Kích thước, đơn hàng, khối lượng) và bảng các chi tiết thuộc kiện đó. Có nút in nhãn/phiếu chi tiết cho từng kiện riêng biệt.
3.  **Tổng hợp đóng kiện (`nv-kien`):** Bảng tổng quan thông tin bao bì của tất cả các kiện: kích thước kiện, khối lượng tổng hợp, tổng số lượng tấm gỗ bên trong, thể tích bao bì so với tổng thể tích các tấm gỗ bên trong.

### 4.4. Tính Năng In Tem & Phiếu Đóng Gói (Print System)
Cho phép người dùng thiết lập các thông số in ấn chuyên sâu trước khi in đơn lẻ hoặc in hàng loạt:
*   **Quy ước tên vật liệu (`materialMode`):**
    *   *Tên đầy đủ (Full):* MDF CA 17mm Melamine...
    *   *Quy ước ngắn (Abbr):* Tự động mã hóa thành `VL-01`, `VL-02`,... và hiển thị bảng chú giải (Legend) ở cuối trang để tiết kiệm không gian in.
*   **Số dòng trên 1 trang (`rowsPerPage`):** Cho phép tùy chỉnh từ 5 đến 20 dòng trên mỗi trang giấy để bảng vừa vặn không bị tràn trang.
*   **Khổ giấy & Bố cục (`paperSize`):**
    *   *A4 đơn (Portrait):* In 1 kiện trên 1 trang đứng.
    *   *A4 ghép đôi (A4x2 - Landscape):* Chia đôi trang giấy khổ ngang để in 2 kiện song song, tiết kiệm giấy.
*   Tự động sắp xếp các chi tiết theo thứ tự cột Layer trước khi in.

### 4.5. Xuất Excel Báo Cáo Chuyên Nghiệp (Export function)
Nút **"Xuất Excel"** tạo ra một bảng tính Excel mới tên là `Woodsoft_BangCat_DongKien.xlsx` có cấu trúc hoàn chỉnh bao gồm 3 Sheet:
1.  `Bang_Gop_Chi_Tiet`: Chứa dữ liệu bảng phẳng của tất cả chi tiết với màu nền phân biệt theo từng kiện.
2.  `Gop_Theo_Block`: Định dạng các kiện thành các khối bảng riêng biệt, được ngăn cách rõ ràng, có tiêu đề kiện lớn, kèm theo dòng tổng cộng (`TỔNG`) về số lượng tấm, diện tích, thể tích và khối lượng.
3.  `TH_Dong_Kien`: Bảng tổng hợp các thông số bao bì đóng gói của toàn bộ kiện hàng.
*   *Lưu ý:* Hàm xuất Excel có tùy chỉnh chi tiết chiều rộng cột (`!cols`), chiều cao dòng (`!rows`), gộp ô (`!merges`) và các thuộc tính style (màu nền, font chữ Roboto/Roboto Mono, viền nét mảnh) giúp báo cáo đạt chất lượng in ấn cao nhất.

---

## 6. Dữ Liệu File Excel Mẫu (Thư mục `vi du mode7`)

Các file Excel trong thư mục `vi du mode7` chứa dữ liệu chi tiết của công trình mẫu **DREAMCITY**:
*   Cấu trúc của các file này chứa các sheet ứng với từng mã kiện riêng biệt (ví dụ: `CAN 15A-TB`, `CH01-TA`, v.v.).
*   Thông số metadata tiếng Nga ở phần đầu sheet được sử dụng làm chuẩn đầu vào để test bộ parser của ứng dụng.

---

*Tài liệu này được biên soạn tự động để cung cấp cái nhìn toàn cảnh về cấu trúc và mã nguồn của Woodsoft Packing List Tool.*
