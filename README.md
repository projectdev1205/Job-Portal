# Job Portal API

A comprehensive FastAPI-based job portal backend with authentication, job management, and application tracking.

## 🚀 Features

### Authentication & Authorization
- **User Registration/Login** with email/password
- **Google OAuth Integration** (optional)
- **JWT Token-based Authentication**
- **Role-based Access Control** (business vs applicant users)

### Job Management
- **CRUD Operations** for job postings (business users only)
- **Job Search & Filtering** by title, company, location, type, tags
- **Pagination** for efficient data loading
- **Comprehensive Job Details** with company info, requirements, offerings

### Application System
- **Job Applications** with cover letters
- **Application Status Tracking** (applied, shortlisted, hired, rejected)
- **Business Dashboard** to view and manage applications
- **Applicant Dashboard** to track submitted applications

### Security & Performance
- **Secure CORS Configuration**
- **Session Management** for OAuth
- **Database Connection Pooling**
- **Comprehensive Error Handling**
- **Input Validation** with Pydantic schemas

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database
- (Optional) Google OAuth credentials

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-portal-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   
   Create a `.env` file in the root directory:
   ```env
   # Database Configuration
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_HOST=localhost
   DB_NAME=job_portal

   # JWT Configuration
   JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
   JWT_EXPIRE_MINUTES=60

   # Google OAuth (Optional)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

   # Application Configuration
   FRONTEND_URL=http://localhost:3000
   ENVIRONMENT=development
   DEBUG=true

   # AWS S3 Configuration (for production file storage)
   USE_S3=false
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=job-portal-files
   S3_FOLDER_PREFIX=uploads/
   MAX_FILE_SIZE_MB=5
   ```

4. **Database Setup**
   
   Create PostgreSQL database and run:
   ```bash
   python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
   ```

5. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

## 🔗 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/google/login` - Initiate Google OAuth
- `GET /auth/google/callback` - Google OAuth callback

### Jobs
- `GET /jobs/` - List jobs with filtering and pagination
- `POST /jobs/` - Create job (business users only)
- `GET /jobs/{job_id}` - Get job details
- `PUT /jobs/{job_id}` - Update job (owner only)
- `DELETE /jobs/{job_id}` - Delete job (owner only)

### Applications
- `POST /applicant/business/{job_id}/apply` - Apply to job with comprehensive form and resume upload
- `GET /applicant/business/applications/my` - Get user's applications
- `GET /applicant/business/files/{file_path}` - Get file URL (S3 presigned URL or local path)

## 💾 Database Schema

### Users
- `id` (Primary Key)
- `name`, `email`, `password_hash`
- `role` (business/applicant)
- `created_at`, `updated_at`

### Jobs
- `id` (Primary Key)
- `posted_by` (Foreign Key to Users)
- `title`, `company_name`, `description`
- `location_*` fields
- `job_type`, `tags`
- `requirements`, `offerings`, `responsibilities`
- `posted_date`, `created_at`, `updated_at`

### Applications
- `id` (Primary Key)
- `user_id`, `job_id` (Foreign Keys)
- `status`, `cover_letter`
- `applied_at`, `updated_at`
- Unique constraint on (user_id, job_id)

## 🔧 Configuration Options

### Environment Variables
- `DB_*`: Database connection settings
- `JWT_*`: JWT token configuration
- `GOOGLE_*`: OAuth credentials (optional)
- `FRONTEND_URL`: Frontend redirect URL
- `ENVIRONMENT`: development/production
- `DEBUG`: Enable debug mode

### CORS Configuration
Configure allowed origins in `app/config.py`:
```python
cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
```

## 🏗️ Architecture

```
app/
├── auth/               # Authentication module
│   ├── auth_routes.py  # Auth endpoints
│   ├── auth_service.py # Auth business logic
│   └── auth_deps.py    # Auth dependencies
├── jobs/               # Jobs module
│   ├── jobs_routes.py  # Job endpoints
│   └── jobs_service.py # Job business logic
├── utils/              # Utilities
│   └── security.py     # Security functions
├── main.py             # FastAPI app setup
├── config.py           # Configuration management
├── database.py         # Database setup
├── models.py           # SQLAlchemy models
└── schemas.py          # Pydantic schemas
```

## 🧪 Usage Examples

### Register a Business User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@company.com",
    "password": "securepass123",
    "role": "business"
  }'
```

### Create a Job Posting
```bash
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "company": {
      "name": "Tech Corp",
      "address": "123 Tech St",
      "description": "Leading tech company"
    },
    "type": ["full-time", "remote"],
    "location": {
      "city": "San Francisco",
      "state": "CA"
    },
    "tags": ["python", "fastapi", "postgresql"],
    "description": "Join our engineering team...",
    "key_responsibilities": ["Develop APIs", "Code reviews"],
    "requirements_qualifications": ["3+ years Python", "Bachelor's degree"],
    "offerings": ["Competitive salary", "Health insurance"],
    "job_details": {"salary_range": "$80k-120k"}
  }'
```

### Search Jobs
```bash
curl "http://localhost:8000/jobs/?search=python&location=san%20francisco&limit=10"
```

## 🔒 Security Features

- **Password Hashing** with bcrypt
- **JWT Token Authentication** with configurable expiration
- **Role-based Route Protection**
- **CORS Security** with configurable origins
- **SQL Injection Prevention** via SQLAlchemy ORM
- **Input Validation** with Pydantic
- **Error Information Sanitization**

## 📁 File Storage

### Local Storage (Development)
By default, files are stored locally in the `uploads/` directory. This is suitable for development and testing.

### AWS S3 Storage (Production)
For production deployments, configure S3 storage:

1. **Set up AWS S3 bucket** with appropriate permissions
2. **Configure environment variables**:
   ```env
   USE_S3=true
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your-bucket-name
   S3_FOLDER_PREFIX=uploads/
   MAX_FILE_SIZE_MB=5
   ```

3. **S3 Bucket Policy** (example):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "AllowFileUploads",
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::YOUR_ACCOUNT:user/YOUR_USER"
         },
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject"
         ],
         "Resource": "arn:aws:s3:::your-bucket-name/uploads/*"
       }
     ]
   }
   ```

### File Organization
Files are organized into folders:
- **Resumes**: `uploads/resumes/` (S3) or `uploads/resumes/` (local)

### File Access
- **S3 Mode**: Files are accessed via presigned URLs (expire after 1 hour)
- **Local Mode**: Files are served directly from the uploads directory
- **API Endpoint**: `GET /applicant/business/files/{file_path}` returns the appropriate URL

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t job-portal-api .

# Run container
docker run -p 8000:8000 \
  -e DB_USER=your_user \
  -e DB_PASS=your_pass \
  -e DB_HOST=your_host \
  -e DB_NAME=your_db \
  job-portal-api
```

### Production Considerations
1. **Set strong JWT_SECRET**
2. **Configure proper CORS_ORIGINS**
3. **Use environment-specific database**
4. **Set DEBUG=false**
5. **Set up proper logging**
6. **Configure HTTPS**
7. **Set up database migrations with Alembic**

## 📝 Recent Improvements

✅ **Security Enhancements**
- Removed hardcoded OAuth credentials
- Secured CORS configuration
- Added proper authentication to all protected routes

✅ **Database Improvements**
- Added proper foreign key relationships
- Added user tracking for job postings
- Added timestamps and application tracking

✅ **Feature Additions**
- Job search and filtering capabilities
- Pagination for better performance
- Complete application management system
- Error handling middleware

✅ **Code Quality**
- Centralized configuration management
- Improved service layer architecture
- Comprehensive input validation
- Better error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
