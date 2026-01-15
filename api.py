from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import pandas as pd
import joblib
from pathlib import Path
import logging
import os
from urllib.parse import urlparse, quote_plus
from sqlalchemy import create_engine
from dotenv import load_dotenv

# =========================
# LOAD MODEL
# =========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "permission_recommender.pkl"

logger.info("Loading model from %s", MODEL_PATH)
model = joblib.load(MODEL_PATH)


def build_db_url() -> str | None:
    raw_url = os.getenv("SPRING_DATASOURCE_URL")
    username = os.getenv("SPRING_DATASOURCE_USERNAME")
    password = os.getenv("SPRING_DATASOURCE_PASSWORD")
    if not raw_url:
        return None

    if raw_url.startswith("jdbc:"):
        raw_url = raw_url[len("jdbc:") :]

    parsed = urlparse(raw_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError("Database name is missing from SPRING_DATASOURCE_URL")
    if not username or not password:
        raise ValueError("SPRING_DATASOURCE_USERNAME or SPRING_DATASOURCE_PASSWORD is missing")

    return (
        f"postgresql+psycopg2://{quote_plus(username)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def load_data_from_db():
    db_url = build_db_url()
    if not db_url:
        return None

    engine = create_engine(db_url)
    logger.info("Loading permissions, audit logs, and users from database")

    permissions_query = """
    SELECT u.user_id, p.id AS permission_id, p.resource_type, p.action, p.scope
    FROM users u
    JOIN roles r ON u.role_id = r.id
    JOIN role_permissions rp ON rp.role_id = r.id
    JOIN permissions p ON p.id = rp.permission_id
    UNION ALL
    SELECT u.user_id, p.id AS permission_id, p.resource_type, p.action, p.scope
    FROM users u
    JOIN user_additional_permissions uap ON uap.user_id = u.id
    JOIN permissions p ON p.id = uap.permission_id
    """
    users_query = """
    SELECT u.user_id, r.name AS role, u.department, u.branch, u.position,
           u.has_license, u.seniority, u.employment_type
    FROM users u
    JOIN roles r ON r.id = u.role_id
    """

    permissions_df = pd.read_sql(permissions_query, engine).drop_duplicates()
    audit_logs_df = pd.read_sql("SELECT * FROM audit_logs", engine)
    users_df = pd.read_sql(users_query, engine)

    return permissions_df, audit_logs_df, users_df


def normalize_audit_logs(df: pd.DataFrame) -> pd.DataFrame:
    if "allowed" not in df.columns and "success" in df.columns:
        df = df.copy()
        df["allowed"] = df["success"]
    return df


# Load data (for rightsizing / anomaly)
db_data = load_data_from_db()
if db_data is None:
    logger.info("SPRING_DATASOURCE_URL not set; loading data from CSV files")
    permissions = pd.read_csv(BASE_DIR / "permissions.csv")
    audit_logs = pd.read_csv(BASE_DIR / "audit_logs.csv")
    users = pd.read_csv(BASE_DIR / "users.csv")
else:
    permissions, audit_logs, users = db_data

audit_logs = normalize_audit_logs(audit_logs)

# Build permission labels in correct order (must match training)
permissions["label"] = permissions["resource_type"] + "_" + permissions["action"]
PERMISSION_LABELS = sorted(permissions["label"].unique())
PERMISSION_ID_BY_LABEL = {}
if "permission_id" in permissions.columns:
    PERMISSION_ID_BY_LABEL = (
        permissions.dropna(subset=["permission_id"])
        .drop_duplicates(subset=["label"])
        .set_index("label")["permission_id"]
        .to_dict()
    )
elif "id" in permissions.columns:
    PERMISSION_ID_BY_LABEL = (
        permissions.dropna(subset=["id"])
        .drop_duplicates(subset=["label"])
        .set_index("label")["id"]
        .to_dict()
    )

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
    position: str | None = None
    employment_type: str | None = None
    has_license_binary: int | None = None


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

def normalize_user_profile(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "position" not in df.columns or df["position"].isna().all():
        df["position"] = df["role"]
    else:
        df["position"] = df["position"].fillna(df["role"])

    if "employment_type" not in df.columns or df["employment_type"].isna().all():
        df["employment_type"] = "FullTime"
    else:
        df["employment_type"] = df["employment_type"].fillna("FullTime")

    if "has_license_binary" not in df.columns or df["has_license_binary"].isna().all():
        df["has_license_binary"] = df["license"].map(
            lambda v: 1 if str(v).strip().lower() in {"true", "1", "yes"} else 0
        )
    else:
        df["has_license_binary"] = df["has_license_binary"].fillna(
            df["license"].map(lambda v: 1 if str(v).strip().lower() in {"true", "1", "yes"} else 0)
        )

    return df


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
    logger.info("Received permission recommendation request for new user")
    df = normalize_user_profile(pd.DataFrame([profile.dict()]))
    proba = model.predict_proba(df)

    recommendations = []
    for idx, label in enumerate(PERMISSION_LABELS):
        confidence = proba[idx][0][1]
        if confidence >= 0.6:
            recommendations.append({
                "permission_id": PERMISSION_ID_BY_LABEL.get(label),
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
    logger.info("Received permission recommendation request for job transfer")
    old_df = normalize_user_profile(pd.DataFrame([req.old_profile.dict()]))
    new_df = normalize_user_profile(pd.DataFrame([req.new_profile.dict()]))

    old_proba = model.predict_proba(old_df)
    new_proba = model.predict_proba(new_df)

    old_scores = {
        PERMISSION_LABELS[idx]: old_proba[idx][0][1]
        for idx in range(len(PERMISSION_LABELS))
    }
    new_scores = {
        PERMISSION_LABELS[idx]: new_proba[idx][0][1]
        for idx in range(len(PERMISSION_LABELS))
    }

    old_perms = {label for label, score in old_scores.items() if score >= 0.6}
    new_perms = {label for label, score in new_scores.items() if score >= 0.6}

    def format_permissions(labels, scores):
        items = [
            {
                "permission_id": PERMISSION_ID_BY_LABEL.get(label),
                "permission": label,
                "confidence": round(scores[label], 2)
            }
            for label in labels
        ]
        return sorted(items, key=lambda x: x["confidence"], reverse=True)

    return {
        "type": "JOB_TRANSFER",
        "added_permissions": format_permissions(new_perms - old_perms, new_scores),
        "removed_permissions": format_permissions(old_perms - new_perms, old_scores),
        "retained_permissions": format_permissions(old_perms & new_perms, new_scores),
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
    logger.info("Received rightsizing request with lookback_days=%s", req.lookback_days)
    audit_logs["timestamp"] = pd.to_datetime(audit_logs["timestamp"], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=req.lookback_days)

    recent = audit_logs[
        (audit_logs["timestamp"] >= cutoff) &
        (audit_logs["allowed"] == True)
    ]

    recent = recent.copy()
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
    logger.info("Received anomaly detection request with risk_threshold=%s", req.risk_threshold)
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

    logs = logs.copy()
    logs["hour"] = pd.to_datetime(logs["timestamp"]).dt.hour
    logs["unexpected_resource"] = logs.apply(
        lambda row: row["resource_type"] not in role_allowed.get(row["role"], []),
        axis=1,
    )
    logs["risk_score"] = (
        (logs["unexpected_resource"].astype(int) * 3)
        + (~logs["hour"].between(8, 18)).astype(int) * 2
        + (logs["allowed"] == False).astype(int)
    )

    anomalies = logs[logs["risk_score"] >= req.risk_threshold]
    samples = (
        anomalies.head(20)
        .replace([float("inf"), float("-inf")], pd.NA)
        .where(pd.notnull(anomalies.head(20)), None)
        .to_dict(orient="records")
    )

    return jsonable_encoder({
        "type": "ANOMALY",
        "detected": len(anomalies),
        "samples": samples
    })
