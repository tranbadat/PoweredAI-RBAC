import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


# =========================
# 1. LOAD DATA
# =========================
print("Đang tải dữ liệu...")

users = pd.read_csv("users.csv")
permissions = pd.read_csv("permissions.csv")
if "user_id" not in permissions.columns:
    roles = pd.read_csv("roles.csv")
    role_permissions = pd.read_csv("role_permissions.csv")
    user_additional_permissions = pd.read_csv("user_additional_permissions.csv")

    role_map = roles.set_index("id")["name"]
    if "role" not in users.columns:
        users = users.copy()
        users["role"] = users["role_id"].map(role_map)

    if "license" not in users.columns:
        if "has_license" in users.columns:
            users = users.copy()
            users["license"] = users["has_license"].map(
                lambda v: "Yes" if str(v).strip().lower() in {"true", "1", "yes"} else "No"
            )
        else:
            users = users.copy()
            users["license"] = "No"

if "has_license_binary" not in users.columns:
    if "has_license" in users.columns:
        users = users.copy()
        users["has_license_binary"] = users["has_license"].map(
            lambda v: 1 if str(v).strip().lower() in {"true", "1", "yes"} else 0
        )
    else:
        users = users.copy()
        users["has_license_binary"] = users["license"].map(lambda v: 1 if str(v).strip().lower() == "yes" else 0)

    role_assigned = (
        users[["id", "user_id", "role_id"]]
        .merge(role_permissions, on="role_id", how="left")
        .merge(permissions, left_on="permission_id", right_on="id", how="left")
    )
    role_assigned = role_assigned[["user_id", "resource_type", "action", "scope"]]

    if not user_additional_permissions.empty:
        user_assigned = (
            user_additional_permissions.rename(columns={"user_id": "user_pk"})
            .merge(users[["id", "user_id"]].rename(columns={"id": "user_pk"}), on="user_pk", how="left")
            .merge(permissions, left_on="permission_id", right_on="id", how="left")
        )
        user_assigned = user_assigned[["user_id", "resource_type", "action", "scope"]]
        permissions = pd.concat([role_assigned, user_assigned], ignore_index=True)
    else:
        permissions = role_assigned

    permissions = permissions.dropna(subset=["user_id", "resource_type", "action"])

# =========================
# 2. PREPARE LABELS (MULTI-LABEL)
# =========================
# Create combined label: resource_action
permissions["label"] = permissions["resource_type"] + "_" + permissions["action"]

# Pivot to multi-label matrix
label_df = (
    permissions
    .assign(value=1)
    .pivot_table(
        index="user_id",
        columns="label",
        values="value",
        fill_value=0
    )
    .reset_index()
)

# Merge user profile with labels
data = users.merge(label_df, on="user_id", how="left")
data.fillna(0, inplace=True)

print(f"Tổng số người dùng: {len(data)}")
print(f"Tổng số nhãn quyền: {len(label_df.columns) - 1}")

# =========================
# 3. FEATURE & TARGET
# =========================
X = data[
    [
        "role",
        "department",
        "branch",
        "position",
        "employment_type",
        "license",
        "has_license_binary",
        "seniority",
    ]
]

label_columns = [col for col in label_df.columns if col != "user_id"]
Y = data[label_columns]

# =========================
# 4. PREPROCESSING
# =========================
categorical_features = [
    "role",
    "department",
    "branch",
    "position",
    "employment_type",
    "license",
    "seniority",
]
numeric_features = ["has_license_binary"]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("num", "passthrough", numeric_features),
    ]
)

# =========================
# 5. TRAIN / TEST SPLIT
# =========================
X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y,
    test_size=0.2,
    random_state=42
)

X_test.to_csv("X_test.csv", index=False)
Y_test.to_csv("Y_test.csv", index=False)

# =========================
# 6. MODEL
# =========================
model = Pipeline(steps=[
    ("preprocess", preprocessor),
    ("classifier", MultiOutputClassifier(
        RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
    ))
])

print("Đang huấn luyện mô hình...")
model.fit(X_train, Y_train)

# =========================
# 6.1 SAVE TRAINED MODEL
# =========================
import joblib

MODEL_PATH = "permission_recommender.pkl"
joblib.dump(model, MODEL_PATH)
print(f"Đã lưu mô hình vào {MODEL_PATH}")

# =========================
# 7. EVALUATION
# =========================
print("\nĐánh giá trên tập kiểm thử:")
Y_pred = model.predict(X_test)

print(classification_report(
    Y_test,
    Y_pred,
    target_names=Y.columns
))

# =========================
# 8. DEMO: RECOMMEND PERMISSIONS FOR NEW USER
# =========================
print("\nDemo: Gợi ý quyền cho người dùng mới")

new_user = pd.DataFrame([{
    "role": "Doctor",
    "department": "Khoa_Noi",
    "branch": "CN_HN",
    "position": "Doctor",
    "employment_type": "FullTime",
    "license": "Yes",
    "has_license_binary": 1,
    "seniority": "Senior"
}])

print("Input new_user:", new_user.to_dict(orient="records")[0])

proba = model.predict_proba(new_user)

recommendations = []
for idx, label in enumerate(Y.columns):
    confidence = proba[idx][0][1]
    if confidence >= 0.6:
        recommendations.append((label, round(confidence, 2)))

recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)

print("Quyền được gợi ý:")
for perm, conf in recommendations:
    print(f"- {perm} (độ tin cậy={conf})")

print("Output new_user (labels):", [perm for perm, _ in recommendations])

# =========================
# 9. FEATURE IMPORTANCE (EXPLAINABILITY)
# =========================
print("\nTầm quan trọng đặc trưng (top) cho nhãn quyền đầu tiên:")

rf = model.named_steps["classifier"].estimators_[0]
feature_names = model.named_steps["preprocess"].get_feature_names_out()

importance = (
    pd.Series(rf.feature_importances_, index=feature_names)
    .sort_values(ascending=False)
)

print(importance.head(10))

# =========================
# 10. USE-CASE: JOB TRANSFER / POSITION CHANGE
# =========================
print("\nTình huống: Gợi ý quyền khi chuyển vị trí công tác")

# Example: a Doctor temporarily transferred to Administration (HR)
old_profile = {
    "role": "Doctor",
    "department": "Khoa_Noi",
    "branch": "CN_HN",
    "position": "Doctor",
    "employment_type": "FullTime",
    "license": "Yes",
    "has_license_binary": 1,
    "seniority": "Senior"
}

new_profile = {
    "role": "HR",
    "department": "Phong_NhanSu",
    "branch": "CN_HN",
    "position": "HR",
    "employment_type": "FullTime",
    "license": "No",
    "has_license_binary": 0,
    "seniority": "Senior"
}

old_user_df = pd.DataFrame([old_profile])
new_user_df = pd.DataFrame([new_profile])

print("Input old_profile:", old_profile)
print("Input new_profile:", new_profile)

old_proba = model.predict_proba(old_user_df)
new_proba = model.predict_proba(new_user_df)

old_perms = {
    Y.columns[idx]: old_proba[idx][0][1]
    for idx in range(len(Y.columns))
    if old_proba[idx][0][1] >= 0.6
}

new_perms = {
    Y.columns[idx]: new_proba[idx][0][1]
    for idx in range(len(Y.columns))
    if new_proba[idx][0][1] >= 0.6
}

print("\nQuyền TRƯỚC khi chuyển:")
for p, c in sorted(old_perms.items(), key=lambda x: x[1], reverse=True):
    print(f"- {p} (độ tin cậy={round(c, 2)})")

print("\nQuyền SAU khi chuyển:")
for p, c in sorted(new_perms.items(), key=lambda x: x[1], reverse=True):
    print(f"- {p} (độ tin cậy={round(c, 2)})")

print("Output old_profile (labels):", sorted(old_perms.keys()))
print("Output new_profile (labels):", sorted(new_perms.keys()))

# Delta analysis
added = set(new_perms.keys()) - set(old_perms.keys())
removed = set(old_perms.keys()) - set(new_perms.keys())
retained = set(old_perms.keys()) & set(new_perms.keys())

print("\nPhân tích chênh lệch quyền:")
print(f"Quyền được thêm   : {list(added)}")
print(f"Quyền bị gỡ      : {list(removed)}")
print(f"Quyền được giữ lại: {list(retained)}")

print("\nChiến lược khuyến nghị:")
print("- Quyền giữ lại: giới hạn phạm vi hoặc chỉ đọc nếu là tạm thời")
print("- Quyền thêm: gán kèm hạn sử dụng")
print("- Quyền gỡ: thu hồi hoặc hạ xuống chỉ đọc")

# =========================
# 11. USE-CASE: RIGHTSIZING (REMOVE UNUSED PERMISSIONS)
# =========================
print("\nTình huống: Rightsizing – phát hiện quyền không sử dụng")

# Load audit logs
audit_logs = pd.read_csv("audit_logs.csv")
if "success" not in audit_logs.columns and "allowed" in audit_logs.columns:
    audit_logs = audit_logs.copy()
    audit_logs["success"] = audit_logs["allowed"]

# Consider last N days
LOOKBACK_DAYS = 90
cutoff_time = pd.Timestamp.now() - pd.Timedelta(days=LOOKBACK_DAYS)
audit_logs["timestamp"] = pd.to_datetime(audit_logs["timestamp"])

recent_logs = audit_logs[
    (audit_logs["timestamp"] >= cutoff_time) &
    (audit_logs["success"] == True)
]

# Build usage map: (user, permission) -> count
recent_logs["label"] = recent_logs["resource_type"] + "_" + recent_logs["action"]

usage_counts = (
    recent_logs
    .groupby(["user_id", "label"])
    .size()
    .reset_index(name="usage_count")
)

# Merge with assigned permissions
assigned = permissions.copy()
assigned["label"] = assigned["resource_type"] + "_" + assigned["action"]

rightsizing_df = assigned.merge(
    usage_counts,
    on=["user_id", "label"],
    how="left"
)

rightsizing_df["usage_count"].fillna(0, inplace=True)

# Detect unused permissions
UNUSED_THRESHOLD = 0

unused_permissions = rightsizing_df[
    rightsizing_df["usage_count"] <= UNUSED_THRESHOLD
]

print(f"\nTổng quyền đã cấp: {len(rightsizing_df)}")
print(f"Số quyền không sử dụng: {len(unused_permissions)}")

# Show sample recommendations
print("\nMẫu khuyến nghị rightsizing:")
for _, row in unused_permissions.head(10).iterrows():
    print(
        f"- User {row['user_id']} | Permission {row['label']} "
        f"=> ĐỀ XUẤT GỠ (không sử dụng trong {LOOKBACK_DAYS} ngày gần nhất)"
    )

print("\nChiến lược rightsizing:")
print("- Gỡ quyền không dùng nếu rủi ro thấp")
print("- Hạ xuống chỉ đọc với quyền rủi ro trung bình")
print("- Yêu cầu phê duyệt quản lý + bảo mật nếu rủi ro cao")


# =========================
# 12. USE-CASE: ANOMALY DETECTION (SUSPICIOUS ACCESS)
# =========================
print("\nTình huống: Phát hiện bất thường – truy cập đáng ngờ")

# Define normal behavior per role
role_allowed_resources = {
    "Doctor": ["MedicalRecord", "Prescription", "LabResult"],
    "Nurse": ["VitalSigns", "MedicalRecord"],
    "Receptionist": ["PatientProfile", "Appointment"],
    "Cashier": ["BillingRecord", "Invoice"],
    "HR": ["StaffProfile"]
}

# Join audit logs with user role
audit_with_role = audit_logs.merge(
    users[["user_id", "role"]],
    on="user_id",
    how="left"
)

# Rule 1: Access resource not typical for role
audit_with_role["rule_role_violation"] = audit_with_role.apply(
    lambda r: r["resource_type"] not in role_allowed_resources.get(r["role"], []),
    axis=1
)

# Rule 2: Access outside working hours (08:00–18:00)
audit_with_role["hour"] = audit_with_role["timestamp"].dt.hour
audit_with_role["rule_off_hours"] = ~audit_with_role["hour"].between(8, 18)

# Rule 3: Failed access attempts
audit_with_role["rule_failed_access"] = audit_with_role["success"] == False

# Risk scoring
audit_with_role["risk_score"] = (
    audit_with_role["rule_role_violation"].astype(int) * 3 +
    audit_with_role["rule_off_hours"].astype(int) * 2 +
    audit_with_role["rule_failed_access"].astype(int) * 1
)

# Flag anomalies
RISK_THRESHOLD = 3
anomalies = audit_with_role[audit_with_role["risk_score"] >= RISK_THRESHOLD]

print(f"\nTổng số sự kiện audit: {len(audit_with_role)}")
print(f"Số bất thường phát hiện: {len(anomalies)}")

print("\nMẫu cảnh báo bất thường:")
for _, row in anomalies.head(10).iterrows():
    reasons = []
    if row["rule_role_violation"]:
        reasons.append("Sai quyền theo vai trò")
    if row["rule_off_hours"]:
        reasons.append("Truy cập ngoài giờ")
    if row["rule_failed_access"]:
        reasons.append("Truy cập thất bại")

    print(
        f"- User {row['user_id']} | Role {row['role']} | "
        f"Resource {row['resource_type']} | "
        f"Risk={row['risk_score']} | "
        f"Lý do={', '.join(reasons)}"
    )

print("\nChiến lược xử lý bất thường:")
print("- Rủi ro thấp: ghi log và theo dõi")
print("- Rủi ro trung bình: yêu cầu xác thực lại hoặc MFA")
print("- Rủi ro cao: cảnh báo SOC và tạm khóa truy cập")

# =========================
# 13. LOAD MODEL & SANITY CHECK
# =========================
print("\nĐang tải mô hình đã lưu để kiểm tra...")

loaded_model = joblib.load(MODEL_PATH)

sanity_user = pd.DataFrame([{
    "role": "Doctor",
    "department": "Khoa_Noi",
    "branch": "CN_HN",
    "position": "Doctor",
    "employment_type": "FullTime",
    "license": "Yes",
    "has_license_binary": 1,
    "seniority": "Senior"
}])

sanity_pred = loaded_model.predict(sanity_user)
print("Kích thước dự đoán kiểm tra:", sanity_pred.shape)

print("\nHoàn tất huấn luyện.")
