import random
from datetime import datetime, timedelta

import pandas as pd

# ------------------------
# CONFIG
# ------------------------
ADD_USERS = 500
ADD_LOGS = 5000
OUTPUT_SUFFIX = "_v2"
SEED = 42

random.seed(SEED)

# ------------------------
# LOAD BASE DATA (DB EXPORTS)
# ------------------------
users = pd.read_csv("users.csv")
roles = pd.read_csv("roles.csv")
permissions = pd.read_csv("permissions.csv")
role_permissions = pd.read_csv("role_permissions.csv")
user_additional_permissions = pd.read_csv("user_additional_permissions.csv")
user_assigned_patients = pd.read_csv("user_assigned_patients.csv")
audit_logs = pd.read_csv("audit_logs.csv")

role_name_by_id = roles.set_index("id")["name"].to_dict()

def next_numeric(values):
    nums = []
    for value in values:
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if digits:
            nums.append(int(digits))
    return (max(nums) + 1) if nums else 0


def now_str():
    return datetime.now().isoformat(sep=" ", timespec="microseconds")


def pick_weighted_role():
    if "role_id" in users.columns and not users.empty:
        counts = users["role_id"].value_counts()
        role_ids = counts.index.tolist()
        weights = counts.values.tolist()
        return random.choices(role_ids, weights=weights, k=1)[0]
    return random.choice(roles["id"].tolist())


def sample_from_series(series, fallback):
    unique = series.dropna().unique().tolist()
    return random.choice(unique) if unique else fallback


# ------------------------
# GENERATE USERS
# ------------------------
start_user_id = next_numeric(users["user_id"]) if "user_id" in users.columns else 0
start_username_id = next_numeric(users["username"]) if "username" in users.columns else start_user_id
start_pk = (users["id"].max() + 1) if "id" in users.columns and not users.empty else 1
departments_by_role = users.groupby("role_id")["department"].unique().to_dict() if "department" in users.columns else {}
positions_by_role = users.groupby("role_id")["position"].unique().to_dict() if "position" in users.columns else {}
license_rate_by_role = users.groupby("role_id")["has_license"].mean().to_dict() if "has_license" in users.columns else {}

branches = users["branch"].dropna().unique().tolist() if "branch" in users.columns else ["CN_HN"]
seniority_levels = users["seniority"].dropna().unique().tolist() if "seniority" in users.columns else ["Junior", "Mid", "Senior"]
employment_types = users["employment_type"].dropna().unique().tolist() if "employment_type" in users.columns else ["FullTime"]

new_users = []
for i in range(ADD_USERS):
    role_id = pick_weighted_role()
    role_name = role_name_by_id.get(role_id, "Staff")

    role_departments = departments_by_role.get(role_id, [])
    department = random.choice(role_departments) if len(role_departments) else sample_from_series(users["department"], "General")
    position = random.choice(positions_by_role.get(role_id, [role_name]))

    has_license_rate = license_rate_by_role.get(role_id, 0.0)
    has_license = random.random() < has_license_rate if has_license_rate > 0 else role_name in {"Doctor", "Nurse"}

    user_id_numeric = start_user_id + i
    username_numeric = start_username_id + i
    user_id = f"U{user_id_numeric:04d}"
    username = f"u{username_numeric:04d}"

    new_users.append(
        {
            "id": start_pk + i,
            "user_id": user_id,
            "username": username,
            "email": f"{username}@hospital.com",
            "department": department,
            "branch": random.choice(branches) if branches else "CN_HN",
            "position": position,
            "has_license": has_license,
            "seniority": random.choice(seniority_levels),
            "employment_type": random.choice(employment_types),
            "enabled": True,
            "account_non_expired": True,
            "account_non_locked": True,
            "credentials_non_expired": True,
            "role_id": role_id,
            "created_at": now_str(),
            "updated_at": now_str(),
        }
    )

new_users_df = pd.DataFrame(new_users)
users_base = users.drop(columns=["password"], errors="ignore")
users_v2 = pd.concat([users_base, new_users_df], ignore_index=True)
users_v2.to_csv(f"users{OUTPUT_SUFFIX}.csv", index=False)

# ------------------------
# USER ADDITIONAL PERMISSIONS
# ------------------------
permission_ids = permissions["id"].tolist()
role_perm_map = role_permissions.groupby("role_id")["permission_id"].apply(set).to_dict()

additional_rows = []
for _, user in new_users_df.iterrows():
    if random.random() < 0.1:
        role_perm_ids = role_perm_map.get(user["role_id"], set())
        candidate_ids = [pid for pid in permission_ids if pid not in role_perm_ids]
        if candidate_ids:
            for pid in random.sample(candidate_ids, k=min(len(candidate_ids), random.randint(1, 3))):
                additional_rows.append({"user_id": user["id"], "permission_id": pid})

additional_df = pd.DataFrame(additional_rows)
user_additional_v2 = pd.concat([user_additional_permissions, additional_df], ignore_index=True)
user_additional_v2 = user_additional_v2.drop_duplicates()
user_additional_v2.to_csv(f"user_additional_permissions{OUTPUT_SUFFIX}.csv", index=False)

# ------------------------
# USER ASSIGNED PATIENTS
# ------------------------
existing_patient_ids = user_assigned_patients["patient_id"] if "patient_id" in user_assigned_patients.columns else []
start_patient_id = next_numeric(existing_patient_ids)
patient_counter = start_patient_id

patient_rows = []
for _, user in new_users_df.iterrows():
    role_name = role_name_by_id.get(user["role_id"], "")
    if role_name in {"Doctor", "Nurse"}:
        for _ in range(random.randint(1, 5)):
            patient_id = f"P{patient_counter:05d}"
            patient_rows.append({"user_id": user["id"], "patient_id": patient_id})
            patient_counter += 1

patients_df = pd.DataFrame(patient_rows)
user_assigned_patients_v2 = pd.concat([user_assigned_patients, patients_df], ignore_index=True)
user_assigned_patients_v2 = user_assigned_patients_v2.drop_duplicates()
user_assigned_patients_v2.to_csv(f"user_assigned_patients{OUTPUT_SUFFIX}.csv", index=False)

# ------------------------
# AUDIT LOGS
# ------------------------
permission_lookup = permissions.set_index("id")[["resource_type", "action"]].to_dict("index")

def permissions_for_user(user_row):
    role_perm_ids = role_perm_map.get(user_row["role_id"], set())
    user_perm_ids = user_additional_v2[user_additional_v2["user_id"] == user_row["id"]]["permission_id"].tolist()
    return set(role_perm_ids).union(user_perm_ids)

user_perm_cache = {row["id"]: permissions_for_user(row) for _, row in users_v2.iterrows()}

start_log_id = (audit_logs["id"].max() + 1) if "id" in audit_logs.columns and not audit_logs.empty else 1
start_time = datetime.now() - timedelta(days=90)

ip_samples = ["10.0.0.10", "10.0.1.11", "172.19.0.1", "192.168.1.20"]
agent_samples = ["PostmanRuntime/7.51.0", "Mozilla/5.0", "okhttp/4.11.0"]

log_rows = []
for i in range(ADD_LOGS):
    user = users_v2.sample(1).iloc[0]
    perm_ids = list(user_perm_cache.get(user["id"], set()))
    allow = random.random() < 0.85 and bool(perm_ids)

    if allow:
        pid = random.choice(perm_ids)
        deny_reason = None
        policy_id = "ALLOW_DEFAULT"
        risk_score = 0
    else:
        candidate_ids = [pid for pid in permission_ids if pid not in perm_ids]
        pid = random.choice(candidate_ids) if candidate_ids else random.choice(permission_ids)
        deny_reason = "NOT_ALLOWED"
        policy_id = "DENY_POLICY"
        risk_score = 3

    res = permission_lookup[pid]["resource_type"]
    act = permission_lookup[pid]["action"]
    resource_id = f"{res[:3].upper()}-{random.randint(10000, 99999)}"

    log_rows.append(
        {
            "id": start_log_id + i,
            "user_id": user["user_id"],
            "resource_type": res,
            "resource_id": resource_id,
            "action": act,
            "allowed": allow,
            "policy_id": policy_id,
            "deny_reasons": deny_reason,
            "risk_score": risk_score,
            "timestamp": (start_time + timedelta(minutes=random.randint(0, 60 * 24 * 90))).isoformat(
                sep=" ",
                timespec="microseconds",
            ),
            "ip_address": random.choice(ip_samples),
            "user_agent": random.choice(agent_samples),
        }
    )

logs_df = pd.DataFrame(log_rows)
audit_logs_v2 = pd.concat([audit_logs, logs_df], ignore_index=True)
audit_logs_v2.to_csv(f"audit_logs{OUTPUT_SUFFIX}.csv", index=False)

print("Dataset v2 generated:")
print(f"- users{OUTPUT_SUFFIX}.csv")
print(f"- user_additional_permissions{OUTPUT_SUFFIX}.csv")
print(f"- user_assigned_patients{OUTPUT_SUFFIX}.csv")
print(f"- audit_logs{OUTPUT_SUFFIX}.csv")
