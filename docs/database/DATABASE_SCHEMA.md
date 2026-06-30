# Database Schema Design

This document outlines the schema for both the **Local SQLite Database** (inside `.ai-session/local.db`) and the **Cloud PostgreSQL Database** (for Mode 2/3 sync).

## 1. Local Database (SQLite)
Optimized for high-speed local indexing and search, packaged within the `.aisession` environment.

### `events`
Stores every immutable action taken in the workspace.
- `id` (UUID, PK)
- `session_id` (UUID)
- `timestamp` (DateTime)
- `event_type` (String) - e.g., 'prompt', 'file_save', 'terminal_cmd', 'cursor_move'
- `payload` (JSON) - Event-specific details.

### `chat_history`
- `id` (UUID, PK)
- `timestamp` (DateTime)
- `role` (String) - 'user' or 'assistant' or 'system'
- `model` (String) - e.g., 'claude-3-opus'
- `content` (Text)
- `tokens` (Integer)

### `tasks`
- `id` (UUID, PK)
- `status` (String) - 'pending', 'in_progress', 'completed'
- `description` (Text)
- `created_at` (DateTime)
- `completed_at` (DateTime, Nullable)

### `snapshots`
- `id` (UUID, PK)
- `timestamp` (DateTime)
- `type` (String) - 'baseline' or 'diff'
- `file_path` (String) - Relative path inside `.ai-session/workspace/`
- `hash` (String) - SHA-256

---

## 2. Cloud Database (PostgreSQL)
Optimized for multi-tenant SaaS, authentication, and session metadata management.

### `users`
- `id` (UUID, PK)
- `email` (String, Unique)
- `password_hash` (String)
- `encryption_pub_key` (String) - For E2E encryption sharing.
- `created_at` (DateTime)

### `devices`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `device_name` (String)
- `last_active` (DateTime)

### `sessions`
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `project_name` (String)
- `sync_mode` (Enum: 'local', 'metadata', 'full')
- `latest_snapshot_hash` (String)
- `updated_at` (DateTime)

### `cloud_snapshots` (Only for Mode 3)
- `id` (UUID, PK)
- `session_id` (UUID, FK -> sessions.id)
- `s3_object_key` (String)
- `size_bytes` (BigInt)
- `is_baseline` (Boolean)
- `created_at` (DateTime)

### `sync_logs`
- `id` (UUID, PK)
- `session_id` (UUID, FK -> sessions.id)
- `device_id` (UUID, FK -> devices.id)
- `status` (String) - 'success', 'conflict', 'failed'
- `timestamp` (DateTime)
