# policy

Python project scaffold.

## Development

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run training (run from repo root; creates `permission_recommender.pkl`):

```bash
python src/policy/train.py
```

Run FastAPI:

```bash
python -m uvicorn api:app --reload
```

## Cơ cấu tổ chức

Mô hình dữ liệu mô phỏng một bệnh viện/chuỗi chi nhánh với các thành phần chính:

- Chi nhánh (branch): ví dụ `CN_HN`, `CN_HCM`.
- Khoa/Phòng ban (department): ví dụ `Khoa_Noi`, `Khoa_Ngoai`, `Phong_TiepDon`, `Phong_NhanSu`, `Phong_TaiChinh`.
- Vai trò (role): Doctor, Nurse, Receptionist, Cashier, HR.
- Thuộc tính bổ sung: `license` (Yes/No), `seniority` (Junior/Senior), `employment_type`.

## Vai trò và quyền

Quyền được biểu diễn theo dạng `resource_action` (ví dụ `MedicalRecord_read`), và mỗi vai trò thường gắn với các nhóm quyền đặc trưng:

- Doctor: truy cập hồ sơ bệnh án và kê đơn.
- Nurse: đọc hồ sơ bệnh án, tạo/chỉnh dấu hiệu sinh tồn.
- Receptionist: tạo/đọc thông tin bệnh nhân và lịch hẹn.
- Cashier: đọc/cập nhật hóa đơn.
- HR: đọc/cập nhật hồ sơ nhân sự.

Quyền thực tế cho từng người dùng được học từ dữ liệu lịch sử trong `permissions.csv` và `audit_logs.csv`.

## Training output

Captured from running `python src/policy/train.py` (saved in `training_output.txt`).

```text
Đang tải dữ liệu...
Tổng số người dùng: 1000
Tổng số nhãn quyền: 11
Đang huấn luyện mô hình...
Đã lưu mô hình vào permission_recommender.pkl

Đánh giá trên tập kiểm thử:
                       precision    recall  f1-score   support

   BillingRecord_read       1.00      1.00      1.00        38
 BillingRecord_update       1.00      1.00      1.00        38
   MedicalRecord_read       1.00      1.00      1.00        45
 MedicalRecord_update       1.00      1.00      1.00        45
PatientProfile_create       1.00      1.00      1.00        38
  PatientProfile_read       1.00      1.00      1.00        38
  Prescription_create       1.00      1.00      1.00        45
    StaffProfile_read       1.00      1.00      1.00        31
  StaffProfile_update       1.00      1.00      1.00        31
    VitalSigns_create       1.00      1.00      1.00        48
      VitalSigns_read       1.00      1.00      1.00        48

            micro avg       1.00      1.00      1.00       445
            macro avg       1.00      1.00      1.00       445
         weighted avg       1.00      1.00      1.00       445
          samples avg       1.00      1.00      1.00       445


Demo: Gợi ý quyền cho người dùng mới
Input new_user: {'role': 'Doctor', 'department': 'Khoa_Noi', 'branch': 'CN_HN', 'license': 'Yes', 'seniority': 'Senior'}
Quyền được gợi ý:
- MedicalRecord_read (độ tin cậy=1.0)
- MedicalRecord_update (độ tin cậy=1.0)
- Prescription_create (độ tin cậy=1.0)
Output new_user (labels): ['MedicalRecord_read', 'MedicalRecord_update', 'Prescription_create']

Tầm quan trọng đặc trưng (top) cho nhãn quyền đầu tiên:
cat__role_Cashier                 0.417655
cat__department_Phong_TaiChinh    0.366174
cat__license_No                   0.053597
cat__department_Phong_NhanSu      0.037261
cat__role_Receptionist            0.036887
cat__license_Yes                  0.032627
cat__department_Phong_TiepDon     0.017436
cat__role_HR                      0.014950
cat__department_Khoa_Noi          0.007723
cat__department_Khoa_Ngoai        0.007063
dtype: float64

Tình huống: Gợi ý quyền khi chuyển vị trí công tác
Input old_profile: {'role': 'Doctor', 'department': 'Khoa_Noi', 'branch': 'CN_HN', 'license': 'Yes', 'seniority': 'Senior'}
Input new_profile: {'role': 'HR', 'department': 'Phong_NhanSu', 'branch': 'CN_HN', 'license': 'No', 'seniority': 'Senior'}

Quyền TRƯỚC khi chuyển:
- MedicalRecord_read (độ tin cậy=1.0)
- MedicalRecord_update (độ tin cậy=1.0)
- Prescription_create (độ tin cậy=1.0)

Quyền SAU khi chuyển:
- StaffProfile_read (độ tin cậy=1.0)
- StaffProfile_update (độ tin cậy=1.0)
Output old_profile (labels): ['MedicalRecord_read', 'MedicalRecord_update', 'Prescription_create']
Output new_profile (labels): ['StaffProfile_read', 'StaffProfile_update']

Phân tích chênh lệch quyền:
Quyền được thêm   : ['StaffProfile_read', 'StaffProfile_update']
Quyền bị gỡ      : ['MedicalRecord_read', 'MedicalRecord_update', 'Prescription_create']
Quyền được giữ lại: []

Chiến lược khuyến nghị:
- Quyền giữ lại: giới hạn phạm vi hoặc chỉ đọc nếu là tạm thời
- Quyền thêm: gán kèm hạn sử dụng
- Quyền gỡ: thu hồi hoặc hạ xuống chỉ đọc

Tình huống: Rightsizing – phát hiện quyền không sử dụng

Tổng quyền đã cấp: 2213
Số quyền không sử dụng: 68

Mẫu khuyến nghị rightsizing:
- User U0006 | Permission Prescription_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0025 | Permission Prescription_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0060 | Permission Prescription_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0069 | Permission PatientProfile_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0123 | Permission VitalSigns_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0149 | Permission MedicalRecord_update => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0154 | Permission MedicalRecord_update => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0171 | Permission MedicalRecord_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0173 | Permission StaffProfile_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0184 | Permission Prescription_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)

Chiến lược rightsizing:
- Gỡ quyền không dùng nếu rủi ro thấp
- Hạ xuống chỉ đọc với quyền rủi ro trung bình
- Yêu cầu phê duyệt quản lý + bảo mật nếu rủi ro cao

Tình huống: Phát hiện bất thường – truy cập đáng ngờ

Tổng số sự kiện audit: 10000
Số bất thường phát hiện: 1257

Mẫu cảnh báo bất thường:
- User U0398 | Role Nurse | Resource MedicalRecord | Risk=3 | Lý do=Truy cập ngoài giờ, Truy cập thất bại
- User U0779 | Role Cashier | Resource MedicalRecord | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0822 | Role Nurse | Resource StaffProfile | Risk=6 | Lý do=Sai quyền theo vai trò, Truy cập ngoài giờ, Truy cập thất bại
- User U0628 | Role Receptionist | Resource StaffProfile | Risk=6 | Lý do=Sai quyền theo vai trò, Truy cập ngoài giờ, Truy cập thất bại
- User U0144 | Role Cashier | Resource MedicalRecord | Risk=6 | Lý do=Sai quyền theo vai trò, Truy cập ngoài giờ, Truy cập thất bại
- User U0871 | Role Cashier | Resource MedicalRecord | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0729 | Role Doctor | Resource BillingRecord | Risk=6 | Lý do=Sai quyền theo vai trò, Truy cập ngoài giờ, Truy cập thất bại
- User U0798 | Role Cashier | Resource MedicalRecord | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0112 | Role Doctor | Resource BillingRecord | Risk=6 | Lý do=Sai quyền theo vai trò, Truy cập ngoài giờ, Truy cập thất bại
- User U0864 | Role Nurse | Resource MedicalRecord | Risk=3 | Lý do=Truy cập ngoài giờ, Truy cập thất bại

Chiến lược xử lý bất thường:
- Rủi ro thấp: ghi log và theo dõi
- Rủi ro trung bình: yêu cầu xác thực lại hoặc MFA
- Rủi ro cao: cảnh báo SOC và tạm khóa truy cập

Đang tải mô hình đã lưu để kiểm tra...
Kích thước dự đoán kiểm tra: (1, 11)

Hoàn tất huấn luyện.
```
