package emr.authz

# ============================================================
# Defaults
# ============================================================
default allow := false

default decision := {
  "allow": false,
  "policy_id": "DEFAULT_DENY",
  "deny_reasons": [],
  "obligations": [],
  "risk_score": 0
}

# ============================================================
# Data tables (RBAC baseline) - easy to audit
# ============================================================

# Allowed (resource -> actions) per role (baseline, ABAC still applies)
role_perms := {
  "Doctor": {
    "PatientProfile": {"read"},
    "MedicalRecord": {"read", "create", "update"},
    "ClinicalNote": {"read", "create"},
    "VitalSigns": {"read"},
    "Prescription": {"read", "create", "update", "approve"},
    "LabOrder": {"create", "read"},
    "LabResult": {"read"},
    "ImagingOrder": {"create", "read"},
    "ImagingResult": {"read"},
    "AdmissionRecord": {"read"},
    "TransferRecord": {"read"},
    "DischargeSummary": {"create", "read"},
    "MedicalReport": {"read"}
  },

  "Nurse": {
    "PatientProfile": {"read"},
    "MedicalRecord": {"read"},
    "ClinicalNote": {"read"},
    "VitalSigns": {"read", "create", "update"},
    "LabResult": {"read"},          # often limited; ABAC restricts further
    "ImagingResult": {"read"},      # often limited; ABAC restricts further
    "AdmissionRecord": {"read"},
    "TransferRecord": {"read"},
    "DischargeSummary": {"read"}
  },

  "Receptionist": {
    "PatientProfile": {"create", "read", "update"},
    "Appointment": {"create", "read", "update"},
    "AdmissionRecord": {"create", "read"},
    "TransferRecord": {"create", "read"}  # if reception handles transfers; ABAC restricts branch
  },

  "Cashier": {
    "BillingRecord": {"create", "read", "update"},
    "Invoice": {"create", "read", "update"},
    "InsuranceClaim": {"create", "read", "update"},
    "FinancialReport": {"read"}
  },

  "HR": {
    "StaffProfile": {"create", "read", "update"},
    "WorkSchedule": {"create", "read", "update"},
    "TrainingRecord": {"create", "read", "update"},
    "OperationReport": {"read"}
  },

  "Manager": {
    "MedicalReport": {"read"},
    "OperationReport": {"read"},
    "FinancialReport": {"read"},
    "WorkSchedule": {"read"},
    "StaffProfile": {"read"} # ABAC: only own dept/branch
  },

  "ITAdmin": {
    "SystemConfig": {"read", "update"},
    "AccessPolicy": {"read"},
    "AuditLog": {"read"} # ABAC: restricted, usually metadata only
  },

  "SecurityAdmin": {
    "AuditLog": {"read"},
    "IncidentCase": {"create", "read", "update"},
    "AccessPolicy": {"read", "update"},
    "SystemConfig": {"read"}
  }
}

# High-risk actions/resources
high_risk_actions := {"export", "delete"}
high_risk_resources := {"MedicalRecord", "AuditLog", "AccessPolicy", "SystemConfig"}

# ============================================================
# Helpers
# ============================================================

subject := input.subject
resource := input.resource
env := input.environment
action := input.action

resource_type := resource.type

is_off_hours {
  not (env.hour >= 8)
} or {
  not (env.hour <= 18)
}

same_branch {
  subject.branch == resource.branch
}

same_department {
  subject.department == resource.owner_department
}

has_patient {
  resource.patient_id != null
}

patient_assigned {
  has_patient
  resource.patient_id in subject.assigned_patients
}

# RBAC baseline check
rbac_allows {
  role_perms[subject.role][resource_type][action]
}

# Basic risk score (simple + explainable)
risk_score := (
  0 +
  2 * bool_to_int(is_off_hours) +
  3 * bool_to_int(action == "export") +
  2 * bool_to_int(resource.sensitivity == "High") +
  3 * bool_to_int(resource_type in high_risk_resources) +
  2 * bool_to_int(action in high_risk_actions)
)

bool_to_int(b) := 1 if b
bool_to_int(b) := 0 if not b

# ============================================================
# Explicit DENY rules (deny override)
# ============================================================

deny_reasons[r] {
  subject.role == "Receptionist"
  resource_type in {"MedicalRecord", "ClinicalNote", "VitalSigns", "Prescription", "LabResult", "ImagingResult", "DischargeSummary"}
  r := "RECEPTIONIST_NO_CLINICAL_ACCESS"
}

deny_reasons[r] {
  subject.role == "Cashier"
  resource_type in {"MedicalRecord", "ClinicalNote", "VitalSigns", "Prescription", "LabResult", "ImagingResult"}
  r := "CASHIER_NO_CLINICAL_ACCESS"
}

deny_reasons[r] {
  subject.role == "HR"
  resource_type in {"MedicalRecord", "ClinicalNote", "VitalSigns", "Prescription", "LabResult", "ImagingResult", "BillingRecord", "Invoice", "InsuranceClaim"}
  r := "HR_NO_PATIENT_OR_FINANCE_ACCESS"
}

deny_reasons[r] {
  subject.role == "ITAdmin"
  resource_type in {"MedicalRecord", "ClinicalNote", "VitalSigns", "Prescription", "LabResult", "ImagingResult", "PatientProfile"}
  r := "ITADMIN_NO_PATIENT_DATA"
}

# Block delete across most roles (demo): only SecurityAdmin can delete policies/config; no one deletes medical data
deny_reasons[r] {
  action == "delete"
  resource_type in {"MedicalRecord", "ClinicalNote", "VitalSigns", "Prescription", "LabResult", "ImagingResult", "PatientProfile"}
  r := "NO_DELETE_PATIENT_DATA"
}

# Export controls: only SecurityAdmin in emergency OR special approval flag
deny_reasons[r] {
  action == "export"
  resource_type == "MedicalRecord"
  not env.emergency_mode
  not env.export_approved
  r := "EXPORT_REQUIRES_APPROVAL_OR_EMERGENCY"
}

deny_reasons[r] {
  action == "export"
  resource_type == "MedicalRecord"
  subject.role != "SecurityAdmin"
  env.emergency_mode
  r := "ONLY_SECURITYADMIN_CAN_EXPORT_IN_EMERGENCY"
}

# Branch mismatch deny for non-cross-branch roles (simplified)
deny_reasons[r] {
  subject.role in {"Doctor", "Nurse", "Receptionist", "Cashier", "HR"}
  not same_branch
  r := "BRANCH_MISMATCH"
}

deny {
  count(deny_reasons) > 0
}

# ============================================================
# ABAC CONDITIONS per resource family
# ============================================================

# Clinical resources usually need patient assignment + (often) dept check
clinical_resource := resource_type in {"MedicalRecord", "ClinicalNote", "VitalSigns", "Prescription", "LabResult", "ImagingResult", "DischargeSummary"}

clinical_abac_ok {
  # Doctor: assigned patient is enough (dept optional)
  subject.role == "Doctor"
  patient_assigned
}

clinical_abac_ok {
  # Nurse: assigned patient AND same department
  subject.role == "Nurse"
  patient_assigned
  same_department
}

# Admin patient profile: branch-scoped; doctors/nurses can read, receptionist can CRUD
patient_profile_abac_ok {
  resource_type == "PatientProfile"
  same_branch
}

# Appointment: branch-scoped
appointment_abac_ok {
  resource_type == "Appointment"
  same_branch
}

# Admission/Transfer: branch-scoped; reception can create; clinical can read
admission_transfer_abac_ok {
  resource_type in {"AdmissionRecord", "TransferRecord"}
  same_branch
}

# Billing: branch-scoped; cashier; manager read
billing_abac_ok {
  resource_type in {"BillingRecord", "Invoice", "InsuranceClaim"}
  same_branch
}

# Staff: HR full, Manager limited to dept/branch
staff_abac_ok {
  resource_type in {"StaffProfile", "WorkSchedule", "TrainingRecord"}
  same_branch
  subject.role == "HR"
}

staff_abac_ok {
  resource_type in {"StaffProfile", "WorkSchedule"}
  same_branch
  subject.role == "Manager"
  # limit manager to own department
  resource.owner_department == subject.department
}

# Reports: branch/dept scoping
report_abac_ok {
  resource_type in {"MedicalReport", "OperationReport", "FinancialReport"}
  same_branch
}

report_abac_ok {
  resource_type == "MedicalReport"
  subject.role in {"Manager", "Doctor"}
  # for Manager: only own department’s report
  subject.role != "Manager" or resource.owner_department == subject.department
}

# System/Security: strict
system_security_abac_ok {
  resource_type in {"SystemConfig", "AccessPolicy", "AuditLog", "IncidentCase"}
  subject.role in {"ITAdmin", "SecurityAdmin"}
}

# ============================================================
# SoD (Segregation of Duties) - basic demo controls
# Requires resource metadata: created_by / approved_by
# ============================================================

deny_reasons[r] {
  action == "approve"
  resource_type in {"Invoice", "InsuranceClaim", "Prescription"}
  resource.created_by == subject.user_id
  r := "SOD_CREATOR_CANNOT_APPROVE"
}

# ============================================================
# Main PERMIT decision
# ============================================================

abac_ok {
  # Clinical
  clinical_resource
  clinical_abac_ok
}

abac_ok {
  patient_profile_abac_ok
}

abac_ok {
  appointment_abac_ok
}

abac_ok {
  admission_transfer_abac_ok
}

abac_ok {
  billing_abac_ok
}

abac_ok {
  staff_abac_ok
}

abac_ok {
  report_abac_ok
}

abac_ok {
  system_security_abac_ok
}

# Allow if:
# 1) RBAC baseline allows
# 2) ABAC conditions pass for the resource family
# 3) No deny reasons
allow {
  rbac_allows
  abac_ok
  not deny
}

# ============================================================
# Obligations (what app must enforce)
# ============================================================

obligations[o] {
  allow
  is_off_hours
  o := {"type": "step_up_mfa", "reason": "off_hours"}
}

# Mask sensitive fields for non-clinical roles or when viewing admin profile
obligations[o] {
  allow
  resource_type == "PatientProfile"
  subject.role != "Receptionist"
  o := {"type": "mask_fields", "fields": ["national_id", "address"], "reason": "privacy_minimization"}
}

# For high-risk actions, require additional logging and review
obligations[o] {
  allow
  action in high_risk_actions
  o := {"type": "log_high_risk", "reason": "high_risk_action"}
}

# Export requires ticket/approval reference in env (even if allowed)
obligations[o] {
  allow
  action == "export"
  o := {"type": "require_approval_ref", "field": "environment.approval_ticket_id"}
}

# Rate limit for search endpoints / bulk read (service sets env.is_bulk = true)
obligations[o] {
  allow
  env.is_bulk
  o := {"type": "rate_limit", "limit_per_minute": 60, "reason": "bulk_access_control"}
}

# ============================================================
# Policy ID selection (for audit)
# ============================================================

policy_id := "ALLOW_" + subject.role + "_" + resource_type + "_" + action {
  allow
}

# ============================================================
# Final decision object
# ============================================================

decision := {
  "allow": allow,
  "policy_id": policy_id,
  "deny_reasons": deny_reasons,
  "obligations": obligations,
  "risk_score": risk_score
}