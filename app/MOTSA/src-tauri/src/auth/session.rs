use chrono::{DateTime, Utc};
use diesel::prelude::*;
use diesel::pg::PgConnection;
use uuid::Uuid;

use crate::database::schema::session;

#[derive(Queryable, Insertable, Identifiable, Debug, Clone)]
#[diesel(table_name = session)]
pub struct Session {
    pub id: String, // SHA-256(token) hex
    pub user_id: Uuid,
    pub expires_at: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
    pub last_seen_at: Option<DateTime<Utc>>,
    pub ip: Option<String>,
    pub user_agent: Option<String>,
}

impl Session {
    // Tạo session mới
    pub fn new(token: &str, user_id: Uuid, expires_at: DateTime<Utc>) -> Self {
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(token.as_bytes());
        let id = hex::encode(hasher.finalize());
        Self {
            id,
            user_id,
            expires_at,
            created_at: Utc::now(),
            last_seen_at: None,
            ip: None,
            user_agent: None,
        }
    }
}

// Hàm tạo token ngẫu nhiên (base64url)
pub fn generate_session_token() -> String {
    use rand::RngCore;
    let mut buf = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut buf);
    base64_url::encode(&buf)
}

// Thêm session vào DB
pub fn create_session(conn: &mut PgConnection, token: &str, user_id: Uuid) -> QueryResult<Session> {
    use diesel::insert_into;
    use crate::database::schema::session::dsl;
    use chrono::Duration;
    let expires_at = Utc::now() + Duration::days(30);
    let session = Session::new(token, user_id, expires_at);
    insert_into(dsl::session).values(&session).get_result(conn)
}

// Xác thực session token
pub fn validate_session_token(conn: &mut PgConnection, token: &str) -> QueryResult<Option<Session>> {
    use crate::database::schema::session::dsl;
    use sha2::{Sha256, Digest};
    let mut hasher = Sha256::new();
    hasher.update(token.as_bytes());
    let id = hex::encode(hasher.finalize());
    dsl::session.filter(dsl::id.eq(id)).first::<Session>(conn).optional()
}

// Xoá session
pub fn invalidate_session(conn: &mut PgConnection, session_id: &str) -> QueryResult<usize> {
    use crate::database::schema::session::dsl;
    diesel::delete(dsl::session.filter(dsl::id.eq(session_id))).execute(conn)
}
