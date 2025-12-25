-- Active: 1764333733331@@nghiapd.kiko-acrux.ts.net@7777@medicalapp
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE EXTENSION IF NOT EXISTS citext;

-- 0. Roles (static list)
CREATE TABLE roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    name text NOT NULL UNIQUE, -- e.g. 'admin', 'doctor'
    description text,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 1. Users (bác sĩ, admin)
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    email text NOT NULL UNIQUE,
    password_hash text NOT NULL, -- hashed (bcrypt/argon2)
    full_name text NOT NULL,
    phone text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_login_at timestamptz
);

ALTER TABLE users ALTER COLUMN is_active SET DEFAULT false;

CREATE TABLE user_roles (
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role_id uuid NOT NULL REFERENCES roles (id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Session store (server-side sessions; DB stores hash of token)
CREATE TABLE session (
    id text PRIMARY KEY, -- store SHA-256(token) hex
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz,
    ip text,
    user_agent text
);

CREATE INDEX idx_session_user ON session (user_id);

-- Verification tokens for email confirmation (email link verification)
CREATE TABLE verification_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash text NOT NULL,
    type text NOT NULL,
    expires_at timestamptz NOT NULL,
    used boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_verif_user ON verification_tokens (user_id);

CREATE INDEX idx_verif_tokenhash ON verification_tokens (token_hash);

-- 2. Patients
CREATE TABLE patients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    medical_record_number text, -- MRN của bệnh viện nếu có
    full_name text NOT NULL,
    date_of_birth date,
    gender text,
    contact_email citext, -- dùng để gửi kết quả cho bệnh nhân
    contact_phone text,
    address text,
    metadata jsonb, -- linh hoạt (ví dụ: gender_code, notes)
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- 3. Studies / Cases (1 study = 1 upload session / 1 exam)
CREATE TABLE studies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    patient_id uuid NOT NULL REFERENCES patients (id) ON DELETE CASCADE,
    created_by uuid REFERENCES users (id), -- bác sĩ upload hoặc quien
    study_type text NOT NULL, -- e.g. 'brain_mri', 'chest_ct', 'pancreas_ct'
    study_date date,
    description text,
    status text NOT NULL DEFAULT 'uploaded', -- uploaded, processing, processed, reviewed, finalized
    priority integer NOT NULL DEFAULT 3, -- 1..5
    metadata jsonb, -- DICOM tags, modality etc.
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_studies_patient ON studies (patient_id);

CREATE INDEX idx_studies_status ON studies (status);

CREATE INDEX idx_studies_studytype_date ON studies (study_type, study_date);

-- 4. Images (metadata; file stored in object storage)
CREATE TABLE images (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    study_id uuid NOT NULL REFERENCES studies (id) ON DELETE CASCADE,
    file_name text NOT NULL,
    file_path text NOT NULL, -- e.g. s3://bucket/path or signed URL reference
    file_checksum text, -- e.g. sha256
    content_type text, -- image/png, application/dicom, etc.
    width integer,
    height integer,
    size_bytes bigint,
    dicom_metadata jsonb, -- store DICOM tags if applicable
    captured_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_images_study ON images (study_id);

CREATE INDEX idx_images_checksum ON images (file_checksum);

-- 5. Model versions
CREATE TABLE model_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    name text NOT NULL, -- e.g. 'tumor-seg-v1'
    version text NOT NULL, -- e.g. '1.0.3' or commit hash
    description text,
    parameters jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- 6. Processing jobs (each job runs model on one or more images)
CREATE TABLE processing_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    study_id uuid NOT NULL REFERENCES studies (id) ON DELETE CASCADE,
    triggered_by uuid REFERENCES users (id),
    model_version_id uuid REFERENCES model_versions (id),
    input_images uuid [] NOT NULL, -- array of image ids
    status text NOT NULL DEFAULT 'queued', -- queued, running, succeeded, failed
    started_at timestamptz,
    finished_at timestamptz,
    error_message text,
    metrics jsonb, -- e.g. runtime, memory, inference stats
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_status ON processing_jobs (status);

CREATE INDEX idx_jobs_study ON processing_jobs (study_id);

-- 7. Results (per job; can store masks/bboxes as files + metadata)
CREATE TABLE results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    job_id uuid NOT NULL REFERENCES processing_jobs (id) ON DELETE CASCADE,
    study_id uuid NOT NULL REFERENCES studies (id) ON DELETE CASCADE,
    summary_text text, -- textual report
    structured jsonb, -- e.g. {tumors: [{type, confidence, bbox, volume_mm3}], metrics...}
    attachments jsonb, -- list of object storage paths (segmentation masks, overlays, annotated images)
    reviewed_by uuid REFERENCES users (id),
    reviewed_at timestamptz,
    status text NOT NULL DEFAULT 'auto_generated', -- auto_generated, reviewed, finalized
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_results_job ON results (job_id);

CREATE INDEX idx_results_study ON results (study_id);

CREATE INDEX idx_results_structured_gin ON results USING gin (structured jsonb_path_ops);

-- 8. Notifications (records of emails sent)
CREATE TABLE notifications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid (),
    result_id uuid REFERENCES results (id) ON DELETE SET NULL,
    to_email citext NOT NULL,
    to_name text,
    subject text,
    body_snippet text,
    sent_at timestamptz,
    status text NOT NULL DEFAULT 'pending', -- pending, sent, failed
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_notifications_status ON notifications (status);

CREATE INDEX idx_notifications_toemail ON notifications (to_email);

-- 9. Audit chain metadata (NOT store raw logs)
-- This table stores *one record per day* to track hash-chain integrity.
CREATE TABLE audit_chain (
    id bigserial PRIMARY KEY,
    day date NOT NULL UNIQUE, -- YYYY-MM-DD (ngày của file)
    file_path text NOT NULL, -- MinIO path to DuckDB log file
    file_hash text NOT NULL, -- sha256(file_of_the_day)
    prev_trunk_hash text, -- chain of day-1
    trunk_hash text NOT NULL, -- sha256(prev_trunk_hash + file_hash)
    total_entries bigint, -- số lượng log trong file DuckDB ngày đó
    generated_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb -- optional: size, runtime, generation info
);

CREATE TABLE patient_doctors (
    patient_id uuid NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (patient_id, doctor_id)
);

CREATE INDEX idx_audit_chain_day ON audit_chain (day);

CREATE INDEX idx_audit_chain_trunk ON audit_chain (trunk_hash);

-- 10. Optional: soft deletes / archival flags
ALTER TABLE studies
ADD COLUMN is_deleted boolean NOT NULL DEFAULT false;

ALTER TABLE images
ADD COLUMN is_deleted boolean NOT NULL DEFAULT false;