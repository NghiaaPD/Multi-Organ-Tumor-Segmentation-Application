// Automatically generated Diesel schema based on db.sql
// Run `diesel print-schema` for updates if needed
// This file defines table! macros for Diesel ORM

diesel::table! {
	roles (id) {
		id -> Uuid,
		name -> Text,
		description -> Nullable<Text>,
		created_at -> Timestamptz,
	}
}

diesel::table! {
	users (id) {
		id -> Uuid,
		email -> Text,
		password_hash -> Text,
		full_name -> Text,
		phone -> Nullable<Text>,
		is_active -> Bool,
		created_at -> Timestamptz,
		last_login_at -> Nullable<Timestamptz>,
	}
}

diesel::table! {
	user_roles (user_id, role_id) {
		user_id -> Uuid,
		role_id -> Uuid,
	}
}

diesel::table! {
	session (id) {
		id -> Text,
		user_id -> Uuid,
		expires_at -> Timestamptz,
		created_at -> Timestamptz,
		last_seen_at -> Nullable<Timestamptz>,
		ip -> Nullable<Text>,
		user_agent -> Nullable<Text>,
	}
}

diesel::table! {
	verification_tokens (id) {
		id -> Uuid,
		user_id -> Uuid,
		token_hash -> Text,
		type_ -> Text,
		expires_at -> Timestamptz,
		used -> Bool,
		created_at -> Timestamptz,
	}
}

diesel::table! {
	patients (id) {
		id -> Uuid,
		medical_record_number -> Nullable<Text>,
		full_name -> Text,
		date_of_birth -> Nullable<Date>,
		gender -> Nullable<Text>,
		contact_email -> Nullable<Citext>,
		contact_phone -> Nullable<Text>,
		address -> Nullable<Text>,
		metadata -> Nullable<Jsonb>,
		created_at -> Timestamptz,
		updated_at -> Timestamptz,
	}
}

diesel::table! {
	studies (id) {
		id -> Uuid,
		patient_id -> Uuid,
		created_by -> Nullable<Uuid>,
		study_type -> Text,
		study_date -> Nullable<Date>,
		description -> Nullable<Text>,
		status -> Text,
		priority -> Int4,
		metadata -> Nullable<Jsonb>,
		created_at -> Timestamptz,
		updated_at -> Timestamptz,
		is_deleted -> Bool,
	}
}

diesel::table! {
	images (id) {
		id -> Uuid,
		study_id -> Uuid,
		file_name -> Text,
		file_path -> Text,
		file_checksum -> Nullable<Text>,
		content_type -> Nullable<Text>,
		width -> Nullable<Int4>,
		height -> Nullable<Int4>,
		size_bytes -> Nullable<Int8>,
		dicom_metadata -> Nullable<Jsonb>,
		captured_at -> Nullable<Timestamptz>,
		created_at -> Timestamptz,
		is_deleted -> Bool,
	}
}

diesel::table! {
	model_versions (id) {
		id -> Uuid,
		name -> Text,
		version -> Text,
		description -> Nullable<Text>,
		parameters -> Nullable<Jsonb>,
		created_at -> Timestamptz,
	}
}

diesel::table! {
	processing_jobs (id) {
		id -> Uuid,
		study_id -> Uuid,
		triggered_by -> Nullable<Uuid>,
		model_version_id -> Nullable<Uuid>,
		input_images -> Array<Uuid>,
		status -> Text,
		started_at -> Nullable<Timestamptz>,
		finished_at -> Nullable<Timestamptz>,
		error_message -> Nullable<Text>,
		metrics -> Nullable<Jsonb>,
		created_at -> Timestamptz,
	}
}

diesel::table! {
	results (id) {
		id -> Uuid,
		job_id -> Uuid,
		study_id -> Uuid,
		summary_text -> Nullable<Text>,
		structured -> Nullable<Jsonb>,
		attachments -> Nullable<Jsonb>,
		reviewed_by -> Nullable<Uuid>,
		reviewed_at -> Nullable<Timestamptz>,
		status -> Text,
		created_at -> Timestamptz,
	}
}

diesel::table! {
	notifications (id) {
		id -> Uuid,
		result_id -> Nullable<Uuid>,
		to_email -> Citext,
		to_name -> Nullable<Text>,
		subject -> Nullable<Text>,
		body_snippet -> Nullable<Text>,
		sent_at -> Nullable<Timestamptz>,
		status -> Text,
		error_message -> Nullable<Text>,
		created_at -> Timestamptz,
	}
}

diesel::table! {
	audit_chain (id) {
		id -> Int8,
		day -> Date,
		file_path -> Text,
		file_hash -> Text,
		prev_trunk_hash -> Nullable<Text>,
		trunk_hash -> Text,
		total_entries -> Nullable<Int8>,
		generated_at -> Timestamptz,
		metadata -> Nullable<Jsonb>,
	}
}

diesel::table! {
	patient_doctors (patient_id, doctor_id) {
		patient_id -> Uuid,
		doctor_id -> Uuid,
		assigned_at -> Timestamptz,
	}
}

// Foreign key relationships
diesel::joinable!(user_roles -> roles (role_id));
diesel::joinable!(user_roles -> users (user_id));
diesel::joinable!(session -> users (user_id));
diesel::joinable!(verification_tokens -> users (user_id));
diesel::joinable!(studies -> patients (patient_id));
diesel::joinable!(studies -> users (created_by));
diesel::joinable!(images -> studies (study_id));
diesel::joinable!(processing_jobs -> studies (study_id));
diesel::joinable!(processing_jobs -> users (triggered_by));
diesel::joinable!(processing_jobs -> model_versions (model_version_id));
diesel::joinable!(results -> processing_jobs (job_id));
diesel::joinable!(results -> studies (study_id));
diesel::joinable!(results -> users (reviewed_by));
diesel::joinable!(notifications -> results (result_id));
diesel::joinable!(patient_doctors -> patients (patient_id));
diesel::joinable!(patient_doctors -> users (doctor_id));

// Allow tables to appear in same query
diesel::allow_tables_to_appear_in_same_query!(
	roles,
	users,
	user_roles,
	session,
	verification_tokens,
	patients,
	studies,
	images,
	model_versions,
	processing_jobs,
	results,
	notifications,
	audit_chain,
	patient_doctors,
);
