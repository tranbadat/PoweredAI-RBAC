import random
import pandas as pd
from datetime import datetime, timedelta

# ------------------------
# CONFIG
# ------------------------
NUM_USERS = 1000
NUM_LOGS = 10000

roles = {
    "Doctor": ["Khoa_Noi", "Khoa_Ngoai"],
    "Nurse": ["Khoa_Noi", "Khoa_Ngoai"],
    "Receptionist": ["Phong_TiepDon"],
    "Cashier": ["Phong_TaiChinh"],
    "HR": ["Phong_NhanSu"]
}

branches = ["CN_HN", "CN_HCM"]
seniority_levels = ["Junior", "Mid", "Senior"]

permissions_map = {
    "Doctor": [("MedicalRecord", "read"), ("MedicalRecord", "update"), ("Prescription", "create")],
    "Nurse": [("VitalSigns", "read"), ("VitalSigns", "create")],
    "Receptionist": [("PatientProfile", "create"), ("PatientProfile", "read")],
    "Cashier": [("BillingRecord", "read"), ("BillingRecord", "update")],
    "HR": [("StaffProfile", "read"), ("StaffProfile", "update")]
}

# ------------------------
# 1. USER PROFILE
# ------------------------
users = []

for i in range(NUM_USERS):
    role = random.choice(list(roles.keys()))
    department = random.choice(roles[role])
    user = {
        "user_id": f"U{i:04}",
        "role": role,
        "department": department,
        "branch": random.choice(branches),
        "position": role,
        "license": "Yes" if role in ["Doctor", "Nurse"] else "No",
        "seniority": random.choice(seniority_levels),
        "employment_type": "FullTime"
    }
    users.append(user)

users_df = pd.DataFrame(users)
users_df.to_csv("users.csv", index=False)

# ------------------------
# 2. PERMISSIONS
# ------------------------
permissions = []

for user in users:
    role = user["role"]
    for res, act in permissions_map.get(role, []):
        permissions.append({
            "user_id": user["user_id"],
            "resource_type": res,
            "action": act,
            "scope": "assigned_patients" if role in ["Doctor", "Nurse"] else "branch"
        })

permissions_df = pd.DataFrame(permissions)
permissions_df.to_csv("permissions.csv", index=False)

# ------------------------
# 3. AUDIT LOGS
# ------------------------
logs = []
start_time = datetime.now() - timedelta(days=90)

for i in range(NUM_LOGS):
    user = random.choice(users)
    role = user["role"]

    # 85% hành vi hợp lệ
    if random.random() < 0.85 and role in permissions_map:
        res, act = random.choice(permissions_map[role])
        success = True
    else:
        # access sai
        res = random.choice(["MedicalRecord", "BillingRecord", "StaffProfile"])
        act = random.choice(["read", "update", "export"])
        success = False

    log = {
        "log_id": f"L{i:05}",
        "user_id": user["user_id"],
        "resource_type": res,
        "action": act,
        "success": success,
        "timestamp": start_time + timedelta(minutes=random.randint(0, 60*24*90))
    }
    logs.append(log)

logs_df = pd.DataFrame(logs)
logs_df.to_csv("audit_logs.csv", index=False)

print("✅ Dataset generated:")
print("- users.csv")
print("- permissions.csv")
print("- audit_logs.csv")