# Mô tả thuật toán gợi ý phân quyền (VI)

Tài liệu này giải thích thuật toán học máy đang sử dụng trong dự án, cách sử dụng, lý do lựa chọn, ưu/nhược điểm, so sánh với thuật toán khác, và các câu hỏi thường gặp khi áp dụng học máy cho bài toán gợi ý phân quyền.

## 1) Tổng quan bài toán

Mục tiêu: từ thông tin hồ sơ người dùng (vai trò, phòng ban, chi nhánh, chức vụ, kinh nghiệm, loại hợp đồng, license) để gợi ý tập quyền phù hợp.

Đây là bài toán multi-label classification (một mẫu có nhiều nhãn cùng lúc): một người dùng có thể được gán nhiều quyền cùng lúc.

## 2) Thuật toán đang sử dụng

Hiện tại pipeline trong `src/policy/train.py`:
- OneHotEncoder cho các trường categorical (biến phân loại như role/department).
- MultiOutputClassifier + RandomForestClassifier cho bài toán multi-label (mỗi nhãn là một bài toán con).
- Dữ liệu đầu vào: `role`, `department`, `branch`, `position`, `employment_type`, `license`, `has_license_binary`, `seniority`.
- Nhãn đầu ra: label dạng `resource_type_action` (ghép tên tài nguyên + hành động; hoặc `resource_type_action_scope` nếu bạn chọn).

Bộ nhãn được tạo từ:
- Quyền gán theo role (role_permissions)
- Quyền bổ sung theo user (user_additional_permissions)

## 3) Lý do lựa chọn RandomForest + MultiOutput

- Hoạt động tốt với dữ liệu categorical sau one-hot (mã hóa thành cột 0/1), không cần chuẩn hóa.
- Mỗi label được huấn luyện như bài toán độc lập (one-vs-rest), dễ hiểu và dễ mở rộng.
- Tránh cài đặt phức tạp (so với deep learning).
- Khả năng xử lý quan hệ phi tuyến giữa feature (đặc trưng) và nhãn.

## 4) Cách sử dụng

### 4.1) Train

Chạy:
```
python src/policy/train.py
```

Kết quả:
- Tạo file model: `permission_recommender.pkl`
- Tạo file test split: `X_test.csv`, `Y_test.csv`

Nếu cần data mới:
- Chạy `python tests/create_data_set_v2.py` để tạo data lớn hơn
- Copy/overwrite các file csv vào bản chính: `users.csv`, `permissions.csv`, `audit_logs.csv`, ...

### 4.2) API

Chạy:
```
uvicorn api:app --reload
```

Endpoint chính:
- `POST /recommend/new-user`
- `POST /recommend/job-transfer`
- `POST /recommend/rightsizing`
- `POST /recommend/anomaly`

API tự suy từ dữ liệu thiếu: `position`, `employment_type`, `has_license_binary`.

## 5) Ưu điểm

- Đơn giản, dễ giải thích (có thể xem importance của features/đặc trưng).
- Dễ mở rộng thêm feature mới.
- Kết quả nhanh, chi phí train thấp.
- Phù hợp khi dữ liệu không quá lớn.

## 6) Nhược điểm

- MultiOutput + RandomForest có thể nặng khi số nhãn rất lớn.
- Có thể thiếu nhạy với quan hệ phức tạp (tương quan giữa các quyền).
- Phụ thuộc chất lượng label (quyền thực tế có thể không "chuẩn").
- Dữ liệu mất cân bằng (nhãn hiếm) làm giảm performance.

## 7) So sánh với thuật toán khác

- Logistic Regression (One-vs-Rest):
  - Ưu: nhanh, dễ giải thích.
  - Nhược: khó bắt phi tuyến, cần feature engineering (tạo thêm đặc trưng thủ công).

- Gradient Boosting / XGBoost / LightGBM:
  - Ưu: thường cho độ chính xác cao hơn.
  - Nhược: phức tạp hơn, cần tuning kỹ, khó giải thích.

- Neural Network:
  - Ưu: có thể học quan hệ phức tạp.
  - Nhược: cần nhiều dữ liệu, khó giải thích, chi phí train cao.

- Rule-based (thủ công):
  - Ưu: dễ kiểm soát, minh bạch.
  - Nhược: khó mở rộng và bảo trì khi quy định tăng lên.

## 8) Benchmark (nếu có)

Hiện tại chưa có benchmark tổng hợp trong repo. Bạn có thể:
- Chạy `train.py` và xem `classification_report`.
- Lưu log ra `training_output.txt` để theo dõi kết quả.

Để đánh giá đúng:
- Precision/Recall/F1 theo từng nhãn.
- Micro/Macro F1 tổng quan.
- PR-AUC nếu cần độ chính xác với nhãn hiếm.

## 9) Các câu hỏi thường gặp

### 9.1) Vì sao cần học máy cho gợi ý phân quyền?
- Giảm thời gian cấp quyền thủ công.
- Phát hiện quyền “ngoại lệ” và đề xuất điều chỉnh.
- Thích nghi nhanh khi có thay đổi tổ chức.

### 9.2) Có nguy cơ cấp sai quyền không?
- Có. Nên dùng threshold (ví dụ 0.6) và kết hợp duyệt thủ công.
- Nên ghi log để audit.

### 9.3) Làm sao giảm rủi ro?
- Áp dụng phạm vi (scope) giới hạn.
- Kiểm tra theo role + department.
- Duyệt thủ công cho quyền nhạy cảm.

### 9.4) Khi nào cần retrain?
- Khi có role mới, quyền mới.
- Khi policy thay đổi lớn.
- Định kỳ theo tháng/quý nếu data thay đổi nhanh.

### 9.5) Làm sao giải thích kết quả?
- Dùng feature importance từ RandomForest (mức độ ảnh hưởng của từng đặc trưng).
- Ghi lại confidence và so sánh với các role tương tự.

### 9.6) Dữ liệu cần tối thiểu bao nhiêu?
- Cần dữ liệu đủ để mỗi role có nhiều mẫu.
- Nếu nhãn hiếm, cần thêm data (hoặc gộp nhãn).

## 10) Đề xuất nâng cấp

- Thêm feature: số lượng audit log, tần suất truy cập, time-of-day (khung giờ truy cập).
- Đưa scope vào nhãn (`resource_action_scope`) nếu cần chi tiết.
- Cân bằng nhãn bằng over/under sampling.
- Thử XGBoost cho nhãn quan trọng.
