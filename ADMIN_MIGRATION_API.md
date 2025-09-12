# Admin Migration API Documentation

## 🚀 Quick Admin APIs for Database Migration

Simple REST APIs to handle database migrations manually without the complexity of CI/CD pipelines.

## 📋 Available Endpoints

### 1. **GET** `/admin/database/status`
**Check database status and migration needs**

**Response:**
```json
{
  "connection_status": "connected",
  "connection_error": null,
  "missing_columns": ["relevant_experience", "education"],
  "needs_migration": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. **POST** `/admin/database/migrate`
**Run database migration to add missing columns**

**Response:**
```json
{
  "success": true,
  "message": "Migration completed successfully. Added 6 columns.",
  "missing_columns": ["relevant_experience", "education", "availability", "references", "terms_accepted", "contact_permission"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. **POST** `/admin/database/backup`
**Create database backup**

**Response:**
```json
{
  "success": true,
  "message": "Backup created successfully: backup_20240115_103000.sql",
  "backup_file": "backup_20240115_103000.sql",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. **GET** `/admin/database/test-connection`
**Test database connection**

**Response:**
```json
{
  "success": true,
  "message": "Database connection successful",
  "database_version": "PostgreSQL 15.4 on x86_64-pc-linux-gnu",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 5. **GET** `/admin/dashboard`
**Admin dashboard web interface**

Returns an HTML page with a user-friendly interface for all migration operations.

## 🔐 Authentication

All endpoints require admin authentication:
- **Header:** `Authorization: Bearer <your_jwt_token>`
- **Role:** User must have `role = "admin"`

## 🚀 Quick Usage Examples

### Using curl:

```bash
# 1. Check database status
curl -X GET "http://localhost:8000/admin/database/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Run migration
curl -X POST "http://localhost:8000/admin/database/migrate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Create backup
curl -X POST "http://localhost:8000/admin/database/backup" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Test connection
curl -X GET "http://localhost:8000/admin/database/test-connection" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Using Python requests:

```python
import requests

# Your JWT token
token = "your_jwt_token_here"
headers = {"Authorization": f"Bearer {token}"}
base_url = "http://localhost:8000"

# Check status
response = requests.get(f"{base_url}/admin/database/status", headers=headers)
print(response.json())

# Run migration
response = requests.post(f"{base_url}/admin/database/migrate", headers=headers)
print(response.json())

# Create backup
response = requests.post(f"{base_url}/admin/database/backup", headers=headers)
print(response.json())
```

## 🌐 Web Dashboard

Access the admin dashboard at: `http://localhost:8000/admin/dashboard`

Features:
- ✅ **Visual status display** - See connection and migration status at a glance
- ✅ **One-click migration** - Run migrations with a single button click
- ✅ **Backup creation** - Create backups before making changes
- ✅ **Connection testing** - Test database connectivity
- ✅ **Activity logging** - See all operations in real-time
- ✅ **Error handling** - Clear error messages and success confirmations

## 🔧 What the Migration Does

The migration adds these missing columns to the `applications` table:

```sql
ALTER TABLE applications ADD COLUMN relevant_experience TEXT;
ALTER TABLE applications ADD COLUMN education TEXT;
ALTER TABLE applications ADD COLUMN availability VARCHAR(255);
ALTER TABLE applications ADD COLUMN "references" TEXT;
ALTER TABLE applications ADD COLUMN terms_accepted BOOLEAN DEFAULT FALSE;
ALTER TABLE applications ADD COLUMN contact_permission BOOLEAN DEFAULT FALSE;
```

## 🛡️ Safety Features

- ✅ **Admin-only access** - Only users with admin role can access these endpoints
- ✅ **Automatic rollback** - If migration fails, changes are automatically rolled back
- ✅ **Status checking** - Always check status before running migration
- ✅ **Backup recommendation** - Create backups before making changes
- ✅ **Error handling** - Clear error messages for troubleshooting

## 🚨 Error Handling

Common error responses:

```json
{
  "detail": "Only admin users can access this endpoint"
}
```

```json
{
  "detail": "Migration failed: column 'references' already exists"
}
```

```json
{
  "detail": "Database connection information not configured"
}
```

## 📝 Quick Start

1. **Login as admin** and get your JWT token
2. **Check status**: `GET /admin/database/status`
3. **Create backup**: `POST /admin/database/backup` (recommended)
4. **Run migration**: `POST /admin/database/migrate`
5. **Verify**: `GET /admin/database/status` again

## 🎯 Perfect for:

- ✅ **Quick fixes** - Resolve schema issues immediately
- ✅ **Development** - Test migrations during development
- ✅ **Production** - Handle urgent production issues
- ✅ **Staging** - Test before full deployment
- ✅ **Emergency** - Fix critical database issues quickly

---

**No more complex CI/CD setup needed! Just hit the APIs and get your database fixed! 🚀**
