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
Tổng số người dùng: 517
Tổng số nhãn quyền: 59
Đang huấn luyện mô hình...
Thời gian huấn luyện: 4.91s
Đã lưu mô hình vào permission_recommender.pkl

Đánh giá trên tập kiểm thử:
                         precision    recall  f1-score   support

      AccessPolicy_read       1.00      0.94      0.97        16
    AccessPolicy_update       1.00      1.00      1.00        11
 AdmissionRecord_create       1.00      1.00      1.00         8
   AdmissionRecord_read       1.00      0.98      0.99        45
     Appointment_create       1.00      1.00      1.00         8
       Appointment_read       1.00      1.00      1.00         8
     Appointment_update       1.00      1.00      1.00         8
          AuditLog_read       1.00      1.00      1.00        15
   BillingRecord_create       1.00      1.00      1.00        14
     BillingRecord_read       1.00      0.93      0.97        15
   BillingRecord_update       1.00      0.93      0.97        15
    ClinicalNote_create       1.00      1.00      1.00        19
      ClinicalNote_read       1.00      1.00      1.00        36
DischargeSummary_create       1.00      1.00      1.00        19
  DischargeSummary_read       1.00      1.00      1.00        36
   FinancialReport_read       1.00      1.00      1.00        26
    ImagingOrder_create       1.00      1.00      1.00        19
      ImagingOrder_read       1.00      1.00      1.00        19
     ImagingResult_read       1.00      1.00      1.00        36
    IncidentCase_create       1.00      1.00      1.00        11
      IncidentCase_read       1.00      1.00      1.00        11
    IncidentCase_update       1.00      1.00      1.00        11
  InsuranceClaim_create       1.00      1.00      1.00        14
    InsuranceClaim_read       1.00      0.88      0.93        16
  InsuranceClaim_update       1.00      1.00      1.00        14
         Invoice_create       1.00      0.93      0.97        15
           Invoice_read       1.00      1.00      1.00        14
         Invoice_update       1.00      0.93      0.97        15
        LabOrder_create       1.00      0.95      0.97        20
          LabOrder_read       1.00      1.00      1.00        19
         LabResult_read       1.00      1.00      1.00        36
   MedicalRecord_create       1.00      1.00      1.00        19
     MedicalRecord_read       1.00      1.00      1.00        36
   MedicalRecord_update       1.00      0.95      0.97        20
     MedicalReport_read       1.00      1.00      1.00        31
   OperationReport_read       1.00      0.97      0.98        32
  PatientProfile_create       1.00      0.89      0.94         9
    PatientProfile_read       1.00      1.00      1.00        44
  PatientProfile_update       1.00      1.00      1.00         8
   Prescription_approve       1.00      0.95      0.97        20
    Prescription_create       1.00      1.00      1.00        19
      Prescription_read       1.00      1.00      1.00        19
    Prescription_update       1.00      0.95      0.97        20
    StaffProfile_create       1.00      0.95      0.97        20
      StaffProfile_read       1.00      1.00      1.00        31
    StaffProfile_update       1.00      1.00      1.00        19
      SystemConfig_read       1.00      1.00      1.00        15
    SystemConfig_update       1.00      1.00      1.00         4
  TrainingRecord_create       1.00      0.95      0.97        20
    TrainingRecord_read       1.00      0.95      0.97        20
  TrainingRecord_update       1.00      0.95      0.97        20
  TransferRecord_create       1.00      0.89      0.94         9
    TransferRecord_read       1.00      1.00      1.00        44
      VitalSigns_create       1.00      1.00      1.00        17
        VitalSigns_read       1.00      1.00      1.00        36
      VitalSigns_update       1.00      1.00      1.00        17
    WorkSchedule_create       1.00      1.00      1.00        19
      WorkSchedule_read       1.00      1.00      1.00        31
    WorkSchedule_update       1.00      1.00      1.00        19

              micro avg       1.00      0.98      0.99      1187
              macro avg       1.00      0.98      0.99      1187
           weighted avg       1.00      0.98      0.99      1187
            samples avg       1.00      0.98      0.99      1187


Chi so (Metric) | Gia tri | Y nghia
Accuracy | 89.42% | Ty le du doan dung tong the
Precision (Macro) | 92.8% | Giam thieu goi y sai (it False Positive)
Recall (Macro) | 98.08% | Dam bao khong bo sot quyen can thiet
F1-Score | 99.01% | Can bang giua do chinh xac va do phu
Training Time | 4.91s | Thoi gian huan luyen nhanh, phu hop tai huan luyen

Demo: Gợi ý quyền cho người dùng mới
Input new_user: {'role': 'Doctor', 'department': 'Khoa_Noi', 'branch': 'CN_HN', 'position': 'Doctor', 'employment_type': 'FullTime', 'license': 'Yes', 'has_license_binary': 1, 'seniority': 'Senior'}
Quyền được gợi ý:
- AdmissionRecord_read (độ tin cậy=1.0)
- ClinicalNote_create (độ tin cậy=1.0)
- ClinicalNote_read (độ tin cậy=1.0)
- DischargeSummary_create (độ tin cậy=1.0)
- DischargeSummary_read (độ tin cậy=1.0)
- ImagingOrder_create (độ tin cậy=1.0)
- ImagingOrder_read (độ tin cậy=1.0)
- ImagingResult_read (độ tin cậy=1.0)
- LabOrder_create (độ tin cậy=1.0)
- LabOrder_read (độ tin cậy=1.0)
- LabResult_read (độ tin cậy=1.0)
- MedicalRecord_create (độ tin cậy=1.0)
- MedicalRecord_read (độ tin cậy=1.0)
- MedicalRecord_update (độ tin cậy=1.0)
- MedicalReport_read (độ tin cậy=1.0)
- PatientProfile_read (độ tin cậy=1.0)
- Prescription_approve (độ tin cậy=1.0)
- Prescription_create (độ tin cậy=1.0)
- Prescription_read (độ tin cậy=1.0)
- Prescription_update (độ tin cậy=1.0)
- TransferRecord_read (độ tin cậy=1.0)
- VitalSigns_read (độ tin cậy=1.0)
Output new_user (labels): ['AdmissionRecord_read', 'ClinicalNote_create', 'ClinicalNote_read', 'DischargeSummary_create', 'DischargeSummary_read', 'ImagingOrder_create', 'ImagingOrder_read', 'ImagingResult_read', 'LabOrder_create', 'LabOrder_read', 'LabResult_read', 'MedicalRecord_create', 'MedicalRecord_read', 'MedicalRecord_update', 'MedicalReport_read', 'PatientProfile_read', 'Prescription_approve', 'Prescription_create', 'Prescription_read', 'Prescription_update', 'TransferRecord_read', 'VitalSigns_read']

Tầm quan trọng đặc trưng (top) cho nhãn quyền đầu tiên:
cat__department_Security          0.232035
cat__role_SecurityAdmin           0.162808
cat__position_SecurityAdmin       0.158828
cat__role_ITAdmin                 0.134441
cat__department_IT                0.097441
cat__position_ITAdmin             0.087847
num__has_license_binary           0.016131
cat__license_No                   0.013984
cat__license_Yes                  0.009182
cat__department_Phong_TaiChinh    0.007753
dtype: float64

Tình huống: Gợi ý quyền khi chuyển vị trí công tác
Input old_profile: {'role': 'Doctor', 'department': 'Khoa_Noi', 'branch': 'CN_HN', 'position': 'Doctor', 'employment_type': 'FullTime', 'license': 'Yes', 'has_license_binary': 1, 'seniority': 'Senior'}
Input new_profile: {'role': 'HR', 'department': 'Phong_NhanSu', 'branch': 'CN_HN', 'position': 'HR', 'employment_type': 'FullTime', 'license': 'No', 'has_license_binary': 0, 'seniority': 'Senior'}

Quyền TRƯỚC khi chuyển:
- AdmissionRecord_read (độ tin cậy=1.0)   
- ClinicalNote_create (độ tin cậy=1.0)    
- ClinicalNote_read (độ tin cậy=1.0)      
- DischargeSummary_create (độ tin cậy=1.0)
- DischargeSummary_read (độ tin cậy=1.0)  
- ImagingOrder_create (độ tin cậy=1.0)    
- ImagingOrder_read (độ tin cậy=1.0)      
- ImagingResult_read (độ tin cậy=1.0)     
- LabOrder_create (độ tin cậy=1.0)        
- LabOrder_read (độ tin cậy=1.0)
- LabResult_read (độ tin cậy=1.0)
- MedicalRecord_create (độ tin cậy=1.0)   
- MedicalRecord_read (độ tin cậy=1.0)     
- MedicalRecord_update (độ tin cậy=1.0)
- MedicalReport_read (độ tin cậy=1.0)
- PatientProfile_read (độ tin cậy=1.0)
- Prescription_approve (độ tin cậy=1.0)
- Prescription_create (độ tin cậy=1.0)
- Prescription_read (độ tin cậy=1.0)
- Prescription_update (độ tin cậy=1.0)
- TransferRecord_read (độ tin cậy=1.0)
- VitalSigns_read (độ tin cậy=1.0)

Quyền SAU khi chuyển:
- OperationReport_read (độ tin cậy=1.0)
- StaffProfile_create (độ tin cậy=1.0)
- StaffProfile_read (độ tin cậy=1.0)
- StaffProfile_update (độ tin cậy=1.0)
- TrainingRecord_create (độ tin cậy=1.0)
- TrainingRecord_read (độ tin cậy=1.0)
- TrainingRecord_update (độ tin cậy=1.0)
- WorkSchedule_create (độ tin cậy=1.0)
- WorkSchedule_read (độ tin cậy=1.0)
- WorkSchedule_update (độ tin cậy=1.0)
Output old_profile (labels): ['AdmissionRecord_read', 'ClinicalNote_create', 'ClinicalNote_read', 'DischargeSummary_create', 'DischargeSummary_read', 'ImagingOrder_create', 'ImagingOrder_read', 'ImagingResult_read', 'LabOrder_create', 'LabOrder_read', 'LabResult_read', 'MedicalRecord_create', 'MedicalRecord_read', 'MedicalRecord_update', 'MedicalReport_read', 'PatientProfile_read', 'Prescription_approve', 'Prescription_create', 'Prescription_read', 'Prescription_update', 'TransferRecord_read', 'VitalSigns_read']
Output new_profile (labels): ['OperationReport_read', 'StaffProfile_create', 'StaffProfile_read', 'StaffProfile_update', 'TrainingRecord_create', 'TrainingRecord_read', 'TrainingRecord_update', 'WorkSchedule_create', 'WorkSchedule_read', 'WorkSchedule_update']

Phân tích chênh lệch quyền:
Quyền được thêm   : ['TrainingRecord_read', 'WorkSchedule_update', 'OperationReport_read', 'WorkSchedule_read', 'StaffProfile_read', 'StaffProfile_update', 'TrainingRecord_update', 'StaffProfile_create', 'WorkSchedule_create', 'TrainingRecord_create']
Quyền bị gỡ      : ['Prescription_update', 'Prescription_approve', 'ClinicalNote_create', 'VitalSigns_read', 'MedicalRecord_update', 'ImagingOrder_create', 'LabOrder_create', 'Prescription_read', 'ClinicalNote_read', 'LabResult_read', 'MedicalRecord_read', 'TransferRecord_read', 'DischargeSummary_create', 'PatientProfile_read', 'MedicalRecord_create', 'ImagingResult_read', 'Prescription_create', 'AdmissionRecord_read', 'ImagingOrder_read', 'MedicalReport_read', 'DischargeSummary_read', 'LabOrder_read']
Quyền được giữ lại: []

Chiến lược khuyến nghị:
- Quyền giữ lại: giới hạn phạm vi hoặc chỉ đọc nếu là tạm thời
- Quyền thêm: gán kèm hạn sử dụng
- Quyền gỡ: thu hồi hoặc hạ xuống chỉ đọc

Tình huống: Rightsizing – phát hiện quyền không sử dụng

Tổng quyền đã cấp: 5830
Số quyền không sử dụng: 2978

Mẫu khuyến nghị rightsizing:
- User U0000 | Permission MedicalRecord_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission MedicalRecord_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission VitalSigns_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
Số quyền không sử dụng: 2978

Mẫu khuyến nghị rightsizing:
- User U0000 | Permission MedicalRecord_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission MedicalRecord_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission VitalSigns_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
Mẫu khuyến nghị rightsizing:
- User U0000 | Permission MedicalRecord_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission MedicalRecord_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission VitalSigns_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission MedicalRecord_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission VitalSigns_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_update => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_approve => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_update => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_approve => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission Prescription_approve => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission LabOrder_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission LabOrder_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission LabResult_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission ImagingOrder_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission LabResult_read => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)
- User U0000 | Permission ImagingOrder_create => ĐỀ XUẤT GỠ (không sử dụng trong 90 ngày gần nhất)


Chiến lược rightsizing:
- Gỡ quyền không dùng nếu rủi ro thấp
- Hạ xuống chỉ đọc với quyền rủi ro trung bình
Chiến lược rightsizing:
- Gỡ quyền không dùng nếu rủi ro thấp
- Hạ xuống chỉ đọc với quyền rủi ro trung bình
- Yêu cầu phê duyệt quản lý + bảo mật nếu rủi ro cao

Tình huống: Phát hiện bất thường – truy cập đáng ngờ
- Hạ xuống chỉ đọc với quyền rủi ro trung bình
- Yêu cầu phê duyệt quản lý + bảo mật nếu rủi ro cao

Tình huống: Phát hiện bất thường – truy cập đáng ngờ

- Yêu cầu phê duyệt quản lý + bảo mật nếu rủi ro cao

Tình huống: Phát hiện bất thường – truy cập đáng ngờ

Tổng số sự kiện audit: 5011
Tình huống: Phát hiện bất thường – truy cập đáng ngờ

Tổng số sự kiện audit: 5011

Tổng số sự kiện audit: 5011
Tổng số sự kiện audit: 5011
Số bất thường phát hiện: 3685
Số bất thường phát hiện: 3685

Mẫu cảnh báo bất thường:
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò

Chiến lược xử lý bất thường:
- Rủi ro thấp: ghi log và theo dõi
- Rủi ro trung bình: yêu cầu xác thực lại hoặc MFA
- Rủi ro cao: cảnh báo SOC và tạm khóa truy cập

Đang tải mô hình đã lưu để kiểm tra...
Kích thước dự đoán kiểm tra: (1, 59)

- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò

Chiến lược xử lý bất thường:
- Rủi ro thấp: ghi log và theo dõi
- Rủi ro trung bình: yêu cầu xác thực lại hoặc MFA
- Rủi ro cao: cảnh báo SOC và tạm khóa truy cập

Đang tải mô hình đã lưu để kiểm tra...
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò

Chiến lược xử lý bất thường:
- Rủi ro thấp: ghi log và theo dõi
- Rủi ro trung bình: yêu cầu xác thực lại hoặc MFA
- Rủi ro cao: cảnh báo SOC và tạm khóa truy cập
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò

Chiến lược xử lý bất thường:
- Rủi ro thấp: ghi log và theo dõi
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User anonymous | Role nan | Resource Authentication | Risk=4 | Lý do=Sai quyền theo vai trò, Truy cập thất bại
- User U0001 | Role Doctor | Resource Authentication | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò
- User U0001 | Role Doctor | Resource PatientProfile | Risk=3 | Lý do=Sai quyền theo vai trò

Chiến lược xử lý bất thường:
- Rủi ro thấp: ghi log và theo dõi
- Rủi ro trung bình: yêu cầu xác thực lại hoặc MFA
- Rủi ro cao: cảnh báo SOC và tạm khóa truy cập

Đang tải mô hình đã lưu để kiểm tra...
Kích thước dự đoán kiểm tra: (1, 59)

Hoàn tất huấn luyện.
```
