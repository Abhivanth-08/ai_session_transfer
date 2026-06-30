# REST API Specification (FastAPI Backend)

The backend exposes a secure REST API for managing cloud synchronization of AISP sessions. All endpoints require a Bearer token (JWT).

## Authentication

### `POST /api/v1/auth/register`
Creates a new user.
- **Body**: `{ "email": "user@example.com", "password": "...", "pub_key": "..." }`
- **Response**: `201 Created`

### `POST /api/v1/auth/login`
- **Body**: `{ "email": "user@example.com", "password": "..." }`
- **Response**: `{ "access_token": "jwt...", "token_type": "bearer" }`

---

## Session Management

### `POST /api/v1/sessions`
Registers a new session for synchronization.
- **Body**: 
  ```json
  {
    "project_name": "MemoryBridge",
    "sync_mode": "full",
    "metadata": { "primary_language": "python" }
  }
  ```
- **Response**: `{ "session_id": "uuid", "status": "registered" }`

### `GET /api/v1/sessions`
Lists all cloud-synchronized sessions for the user.
- **Response**: `[{ "session_id": "...", "project_name": "...", "updated_at": "..." }]`

### `GET /api/v1/sessions/{session_id}/metadata`
Retrieves the latest metadata and current sync hash for a session to determine if local sync is required.
- **Response**: `{ "latest_hash": "abc123def...", "updated_at": "..." }`

---

## Snapshot & Storage Synchronization

### `POST /api/v1/sessions/{session_id}/snapshots/presigned-url`
Requests a pre-signed S3 URL to upload a snapshot (baseline or diff) directly from the client to object storage, bypassing the backend server for large payloads.
- **Body**: `{ "file_name": "diff_123.patch", "size_bytes": 1048576, "md5": "..." }`
- **Response**: `{ "upload_url": "https://s3.amazonaws.com/...", "snapshot_id": "uuid" }`

### `POST /api/v1/sessions/{session_id}/snapshots/confirm`
Confirms that a client successfully uploaded a snapshot to the pre-signed URL.
- **Body**: `{ "snapshot_id": "uuid" }`
- **Response**: `200 OK`

### `GET /api/v1/sessions/{session_id}/snapshots`
Retrieves a list of all snapshots (and download URLs) required to reconstruct the project state on a new device.
- **Response**: 
  ```json
  [
    {
      "type": "baseline",
      "download_url": "https://s3...",
      "timestamp": "2026-06-27T19:00:00Z"
    },
    {
      "type": "diff",
      "download_url": "https://s3...",
      "timestamp": "2026-06-27T19:15:00Z"
    }
  ]
  ```
