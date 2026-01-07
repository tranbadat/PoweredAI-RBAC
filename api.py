from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
from pathlib import Path
import logging

# =========================
# LOAD MODEL
# =========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "permission_recommender.pkl"

logger.info("Đang tải mô hình từ %s", MODEL_PATH)
model = joblib.load(MODEL_PATH)

# Load static data (for rightsizing / anomaly)
logger.info("Đang tải dữ liệu tĩnh (permissions, audit_logs, users)")
permissions = pd.read_csv(BASE_DIR / "permissions.csv")
audit_logs = pd.read_csv(BASE_DIR / "audit_logs.csv")
users = pd.read_csv(BASE_DIR / "users.csv")

# Build permission labels in correct order (must match training)
permissions["label"] = permissions["resource_type"] + "_" + permissions["action"]
PERMISSION_LABELS = sorted(permissions["label"].unique())

app = FastAPI(title="AI Permission Recommendation API")

# =========================
# REQUEST SCHEMAS
# =========================

class UserProfile(BaseModel):
    role: str
    department: str
    branch: str
    license: str
    seniority: str


class JobTransferRequest(BaseModel):
    old_profile: UserProfile
    new_profile: UserProfile


class RightsizingRequest(BaseModel):
    lookback_days: int = 90


class AnomalyRequest(BaseModel):
    risk_threshold: int = 3


# =========================
# HELPER
# =========================

def recommend_permissions(user_df, threshold=0.6):
    proba = model.predict_proba(user_df)
    labels = model.named_steps["classifier"].estimators_
    columns = model.feature_names_in_

    results = []
    for idx, label in enumerate(model.classes_ if hasattr(model, "classes_") else range(len(proba))):
        confidence = proba[idx][0][1]
        if confidence >= threshold:
            results.append({
                "permission": model.output_names_[idx] if hasattr(model, "output_names_") else idx,
                "confidence": round(confidence, 2)
            })
    return results


# =========================
# API 1: NEW USER
# =========================
@app.post("/recommend/new-user")
def recommend_new_user(profile: UserProfile):
    logger.info("Nhận yêu cầu gợi ý quyền cho người dùng mới")
    df = pd.DataFrame([profile.dict()])
    proba = model.predict_proba(df)

    recommendations = []
    for idx, label in enumerate(PERMISSION_LABELS):
        confidence = proba[idx][0][1]
        if confidence >= 0.6:
            recommendations.append({
                "permission": label,
                "confidence": round(confidence, 2)
            })

    return {
        "type": "NEW_USER",
        "recommendations": recommendations
    }


# =========================
# API 2: JOB TRANSFER
# =========================
@app.post("/recommend/job-transfer")
def recommend_job_transfer(req: JobTransferRequest):
    logger.info("Nhận yêu cầu gợi ý quyền cho chuyển vị trí công tác")
    old_df = pd.DataFrame([req.old_profile.dict()])
    new_df = pd.DataFrame([req.new_profile.dict()])

    old_proba = model.predict_proba(old_df)
    new_proba = model.predict_proba(new_df)

    old_perms = {
        idx for idx, p in enumerate(old_proba)
        if p[0][1] >= 0.6
    }

    new_perms = {
        idx for idx, p in enumerate(new_proba)
        if p[0][1] >= 0.6
    }

    return {
        "type": "JOB_TRANSFER",
        "added_permissions": list(new_perms - old_perms),
        "removed_permissions": list(old_perms - new_perms),
        "retained_permissions": list(old_perms & new_perms),
        "strategy": {
            "added": "secondary assignment with expiry",
            "retained": "scoped or read-only",
            "removed": "revoke or downgrade"
        }
    }


# =========================
# API 3: RIGHTSIZING
# =========================
@app.post("/recommend/rightsizing")
def recommend_rightsizing(req: RightsizingRequest):
    logger.info("Nhận yêu cầu rightsizing với lookback_days=%s", req.lookback_days)
    audit_logs["timestamp"] = pd.to_datetime(audit_logs["timestamp"])
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=req.lookback_days)

    recent = audit_logs[
        (audit_logs["timestamp"] >= cutoff) &
        (audit_logs["success"] == True)
    ]

    recent["label"] = recent["resource_type"] + "_" + recent["action"]

    usage = (
        recent.groupby(["user_id", "label"])
        .size()
        .reset_index(name="usage_count")
    )

    assigned = permissions.copy()
    assigned["label"] = assigned["resource_type"] + "_" + assigned["action"]

    merged = assigned.merge(
        usage, on=["user_id", "label"], how="left"
    ).fillna(0)

    unused = merged[merged["usage_count"] == 0]

    return {
        "type": "RIGHTSIZING",
        "total_assigned": len(merged),
        "unused_permissions": unused.head(20).to_dict(orient="records")
    }


# =========================
# API 4: ANOMALY
# =========================
@app.post("/recommend/anomaly")
def detect_anomaly(req: AnomalyRequest):
    logger.info("Nhận yêu cầu phát hiện bất thường với risk_threshold=%s", req.risk_threshold)
    role_allowed = {
        "Doctor": ["MedicalRecord", "Prescription", "LabResult"],
        "Nurse": ["VitalSigns", "MedicalRecord"],
        "Receptionist": ["PatientProfile", "Appointment"],
        "Cashier": ["BillingRecord", "Invoice"],
        "HR": ["StaffProfile"]
    }

    logs = audit_logs.merge(
        users[["user_id", "role"]], on="user_id", how="left"
    )

    logs["hour"] = pd.to_datetime(logs["timestamp"]).dt.hour
    logs["risk_score"] = (
        (logs["resource_type"].apply(
            lambda r: r not in role_allowed.get(logs["role"].iloc[0], [])
        ).astype(int) * 3) +
        (~logs["hour"].between(8, 18)).astype(int) * 2 +
        (logs["success"] == False).astype(int)
    )

    anomalies = logs[logs["risk_score"] >= req.risk_threshold]

    return {
        "type": "ANOMALY",
        "detected": len(anomalies),
        "samples": anomalies.head(20).to_dict(orient="records")
    }
