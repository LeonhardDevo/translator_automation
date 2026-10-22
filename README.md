# AI Translation Service

A comprehensive translation service that leverages Google AI Studio API to convert images to translated documents. The application includes user authentication, admin management, and translation processing capabilities.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [Docker Deployment](#docker-deployment)
- [Project Structure](#project-structure)
- [Admin Features](#admin-features)
- [Client Features](#client-features)
- [Security Features](#security-features)
- [Security Considerations](#security-considerations)
- [Deployment Best Practices](#deployment-best-practices)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Performance Tuning Recommendations](#performance-tuning-recommendations)
- [Translation Workflow](#translation-workflow)
- [API Endpoints](#api-endpoints)
- [Technologies Used](#technologies-used)
- [Monitoring and Observability](#monitoring-and-observability)
- [Operations Guide](#operations-guide)
- [Backup and Recovery](#backup-and-recovery)
- [Disaster Recovery Plan](#disaster-recovery-plan)
- [Scaling Guidelines](#scaling-guidelines)
- [Maintenance Procedures](#maintenance-procedures)
- [Database Migration](#database-migration)
- [License](#license)

## Features

- **User Authentication**: Secure login system with role-based access (user/admin)
- **Liquid-styled UI**: Modern, attractive login forms and dashboards
- **Admin Dashboard**: User management, quota control, and system monitoring
- **Client Dashboard**: Translation statistics and document processing
- **Translation Processing**: Safe integration with Google AI Studio API for document translation
- **Usage Limits**: Daily translation quotas and user restrictions
- **File Upload**: Image-to-document translation workflow with validation
- **Multi-language Support**: Supports Turkmen, Russian, English, German, French, Spanish, Chinese, Japanese, and Arabic
- **API Key Management**: Rotation and distribution across multiple keys
- **Document Validation**: OCR-based validation to ensure documents contain readable text

## Architecture

- **Backend**: FastAPI with SQLModel for database operations
- **Frontend**: React with TypeScript and Vite
- **Database**: SQLite (can be extended to PostgreSQL)
- **Authentication**: JWT tokens with role-based access
- **Translation**: Safe API integration (replaces dangerous code execution)

## Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (recommended) or create an `api_keys.json` file:
```bash
export GEMINI_API_KEYS="your-google-ai-api-key-1,your-google-ai-api-key-2"
export JWT_SECRET_KEY="a-very-long-and-secure-random-key-at-least-32-characters-long"
```

Or create an `api_keys.json` file in the root directory:
```json
{
  "api_keys": [
    "your-google-ai-api-key"
  ]
}
```

3. Run database migrations:
```bash
cd backend
python -m alembic upgrade head
```

4. Start the backend server:
```bash
python -m backend.start_server
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev -- --port 3000
```

## Docker Deployment

The application can be deployed using Docker containers. The following steps outline the process:

### Prerequisites

- Docker Engine
- Docker Compose

### Docker Setup

1. Create a `.env` file in the root directory with your environment variables:
```bash
DB_PASSWORD=your_secure_database_password
JWT_SECRET_KEY=your_very_long_secure_jwt_secret_at_least_32_chars
GEMINI_API_KEYS=your_google_ai_api_key
```

2. Build and start the services:
```bash
docker-compose up -d --build
```

3. The application will be available at:
   - Frontend: `http://localhost`
   - Backend API: `http://localhost/api/` (proxied through nginx)

### Docker Services

The deployment consists of three services:
- **db**: PostgreSQL database container
- **backend**: FastAPI application container
- **frontend**: React application served by Nginx

## Project Structure

```
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py     # Application entry point
│   │   ├── database.py # Database configuration
│   │   ├── security.py # Authentication logic
│   │   ├── models/     # Data models
│   │   ├── routers/    # API routes
│   │   ├── schemas/    # Request/response schemas
│   │   └── utils/      # Utility modules
│   │       └── safe_translator.py # Safe translation implementation
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/ # Reusable components
│   │   ├── pages/      # Page components
│   │   ├── api/        # API utilities
│   │   └── App.tsx     # Main application component
├── backend/start_server.py # Safe startup script
├── config.py            # Configuration settings
├── monitoring/          # Monitoring stack configuration
├── terraform/           # Infrastructure as code
└── DEPLOYMENT_INSTRUCTIONS.md  # Deployment guide
```

## Admin Features

- User management (create, activate/deactivate users)
- Quota management (translation limits, expiration dates)
- System statistics and monitoring
- Auto-generated passwords for new users
- API key management and rotation
- Document validation and processing oversight

## Client Features

- Image upload for translation (with validation)
- Real-time status tracking
- Download translated documents
- View personal translation statistics
- Multi-language selection for translation
- Document preview and validation

## Security Features

- JWT-based authentication with secure secret handling
- Role-based access control
- Password hashing with Argon2
- Rate limiting to prevent abuse
- File upload validation and sanitization
- Secure API communication
- **Critical Fix**: Removed dangerous AI-code-execution functionality
- Input validation and sanitization
- SQL injection prevention
- XSS prevention
- CSRF protection

## Security Considerations

### Authentication & Authorization
- JWT tokens with configurable expiration (default: 60 minutes)
- Secure secret key generation with minimum 32-character requirement
- Role-based access control (user/admin)
- Session management with proper token invalidation

### Input Validation & Sanitization
- File upload validation (type, size, name sanitization)
- Email format validation
- SQL injection prevention through SQLModel/SQLAlchemy
- XSS prevention through proper output encoding

### API Security
- Rate limiting to prevent abuse (default: 100 requests/hour)
- API key rotation support for Google AI services
- Secure communication with HTTPS enforcement
- Proper error handling without information disclosure

### Data Protection
- Passwords hashed with Argon2 algorithm
- Sensitive data encryption in transit
- Secure temporary file handling
- Secure document storage with access controls

## Deployment Best Practices

### Environment Variables
Required environment variables for production:
```bash
JWT_SECRET_KEY="a-very-long-and-secure-random-key-at-least-32-chars"
DB_PASSWORD="your-secure-database-password"
GEMINI_API_KEYS="your-google-ai-api-key"
ENVIRONMENT="production"
DATABASE_URL="postgresql://user:password@host:port/dbname"
```

### Infrastructure Security
- Deploy behind a reverse proxy (Nginx, Apache, or cloud load balancer)
- Use HTTPS with valid certificates
- Implement WAF (Web Application Firewall) if possible
- Use private networks for internal service communication
- Regular security patching of underlying OS and dependencies

### Container Security
- Run containers as non-root user
- Use minimal base images (Alpine Linux preferred)
- Implement read-only filesystems where possible
- Limit resource usage (CPU, memory) to prevent DoS
- Scan images for vulnerabilities before deployment

## Troubleshooting Guide

### Common Issues

#### Startup Issues
- **Database Connection**: Ensure database is accessible and credentials are correct
- **Missing Environment Variables**: Check that all required environment variables are set
- **Port Conflicts**: Verify that ports 7999 (backend) and 3000 (frontend) are available

#### Authentication Issues
- **Invalid Token**: Verify JWT_SECRET_KEY is consistent across deployments
- **Login Failures**: Check email format and password requirements
- **Role Access**: Confirm user roles are properly assigned

#### Translation Issues
- **API Key Errors**: Verify Google AI API keys are valid and have proper permissions
- **File Upload Issues**: Check file size limits and allowed formats
- **Timeout Issues**: Increase timeout values if processing large files
- **Document Validation**: Ensure uploaded documents contain readable text

### Debugging Commands
```bash
# Check application logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env

# Check database connectivity
docker-compose exec backend python -c "from backend.app.database import init_db; init_db()"

# Check application status
curl http://localhost/health

# Check translation status
curl -H "Authorization: Bearer <token>" http://localhost/api/translate/status/<document_id>
```

## Performance Tuning Recommendations

### Backend Optimization
- **Database Connection Pooling**: Configure appropriate connection pool sizes
- **Caching**: Implement Redis caching for frequent operations
- **Background Processing**: Optimize Celery/RQ worker configurations
- **API Rate Limits**: Adjust rate limits based on expected load

### Frontend Optimization
- **Bundle Size**: Minimize bundle size with code splitting
- **Caching**: Implement proper HTTP caching headers
- **CDN**: Serve static assets through CDN for faster delivery

### Infrastructure Optimization
- **Load Balancing**: Distribute load across multiple backend instances
- **Auto-scaling**: Configure auto-scaling based on CPU/memory usage
- **Database Indexing**: Optimize database indexes for common queries
- **Monitoring**: Implement performance monitoring for proactive optimization

## Translation Workflow

1. Client uploads an image file (validated for type and size)
2. System creates a document record with pending status
3. Document is validated to ensure it contains readable text
4. Background process safely translates the document using Google AI Studio
5. Client receives notification when translation completes
6. Client can download the translated document
7. API keys are rotated across different translation requests to prevent rate limiting

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration (admin only)

### User Management (Admin)
- `GET /admin/users` - Get all users
- `POST /admin/users/generate` - Create new user with generated password
- `PUT /admin/users/{id}` - Update user settings
- `DELETE /admin/users/{id}` - Deactivate user
- `POST /admin/users/{id}/activate` - Activate user

### Translation
- `POST /translate/upload` - Upload file for translation
- `GET /translate/status/{id}` - Check translation status
- `GET /translate/download/{id}` - Download translated file

### User Dashboard
- `GET /user/dashboard` - Get user statistics and information

## Technologies Used

- **Backend**: FastAPI, SQLModel, SQLAlchemy, JWT
- **Frontend**: React, TypeScript, Vite, react-router-dom, react-i18next
- **Database**: SQLite (with PostgreSQL compatibility)
- **Authentication**: JWT with Argon2 password hashing
- **Translation**: Google AI Studio API (google-generativeai)
- **Security**: Rate limiting (slowapi), input validation
- **Document Processing**: python-docx
- **Deployment**: Nginx, Gunicorn, systemd, Docker
- **Monitoring**: Prometheus, Grafana, Jaeger, Elasticsearch, Logstash, Kibana
- **Infrastructure**: Terraform for infrastructure as code

## Monitoring and Observability

### Components
- **Application Logging**: Structured JSON logs with correlation IDs
- **Metrics Collection**: Prometheus for system and application metrics
- **Distributed Tracing**: OpenTelemetry integration with Jaeger
- **Alerting System**: Critical, performance, and security alerts
- **Dashboards**: Grafana for metrics, Kibana for logs, Jaeger for traces

### Key Metrics
- **System**: CPU, memory, disk I/O, network I/O
- **Application**: Request rates, response times, error rates, active connections
- **Business**: Translation requests, success/failure rates, API key usage, user activity

### Access Points
- **Grafana**: http://localhost:3000 (admin/admin)
- **Kibana**: http://localhost:5601
- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## Operations Guide

### Pre-deployment Checklist
- [ ] Confirm all tests have passed in staging environment
- [ ] Verify database migration scripts are ready
- [ ] Ensure sufficient capacity in target environment
- [ ] Notify stakeholders of planned maintenance window (if applicable)

### Standard Deployment Process
1. Code promotion to main branch triggers automated deployment
2. CI/CD pipeline runs tests and builds containers
3. Deployment to staging environment for validation
4. Automated promotion to production if staging tests pass

### Monitoring and Alerts
- **Critical Metrics**: API response times < 500ms (95th percentile), error rates < 1%
- **Alert Conditions**: Error rate > 5% for 5+ minutes, response time > 2s for 5+ minutes
- **Escalation**: Level 1 (on-call engineer), Level 2 (senior engineer), Level 3 (management)

### Common Issues and Solutions
- **High Error Rates**: Check application logs, verify database connectivity, review configuration changes
- **Slow Response Times**: Check database performance, verify cache hit ratios, monitor resource utilization
- **Database Connectivity Issues**: Verify database health, check security groups, review connection pools

## Backup and Recovery

### Database Backups
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days locally, 1 year in archival storage
- **Location**: `/backups/database/` on the database server

#### Manual Backup Process
```bash
# For PostgreSQL
pg_dump -h hostname -U username -d database_name > backup_file.sql

# For SQLite (local development)
cp /path/to/translation_app.db /path/to/backup/location/translation_app_backup_$(date +%Y%m%d).db
```

#### Recovery Process
1. Stop the application services
2. Restore the database from backup
3. Restart services
4. Verify data integrity

### Document Storage Backups
Uploaded and translated documents are stored in `/uploads/` and `/output/` directories and should be backed up regularly.

## Disaster Recovery Plan

### Types of Disasters
1. **Hardware Failure**: Server crashes, disk failures
2. **Data Corruption**: Accidental deletions, malicious activity
3. **Network Outages**: Internet connectivity issues
4. **Security Incidents**: Breaches, DDoS attacks
5. **Natural Disasters**: Power outages, floods, fires

### Recovery Objectives
- **RTO (Recovery Time)**: Critical systems in 4 hours, non-critical in 24 hours
- **RPO (Recovery Point)**: Max 1 hour of data loss, max 100 transactions

## Scaling Guidelines

### Horizontal Scaling
The application supports horizontal scaling through:
- **Multiple API Server Instances**: Deploy additional backend containers
- **Load Balancer Configuration**: Configure load balancer for new instances
- **Database Connection Pooling**: Adjust pool sizes based on instance count

#### Scaling Commands
```bash
# Scale backend services
docker-compose up -d --scale backend=3
```

### Vertical Scaling
- **CPU Cores**: Recommended minimum 2 cores per instance
- **RAM**: Minimum 4GB per backend instance
- **Disk Space**: Monitor for upload/processing storage needs

### Auto-scaling Configuration
Configure auto-scaling based on:
- **CPU Utilization**: Scale up at 70% usage
- **Memory Usage**: Scale up at 80% usage
- **Request Queue Length**: Scale up when queue exceeds 50 requests

## Maintenance Procedures

### Routine Maintenance

#### Daily Tasks
- [ ] Check system logs for errors
- [ ] Verify backup completion
- [ ] Monitor disk space usage
- [ ] Review security alerts
- [ ] Check service availability

#### Weekly Tasks
- [ ] Update security patches
- [ ] Review access logs
- [ ] Clean temporary files
- [ ] Update dependency lists
- [ ] Test backup restoration

#### Monthly Tasks
- [ ] Security vulnerability scans
- [ ] Performance optimization
- [ ] Database maintenance
- [ ] Capacity planning
- [ ] Update documentation

### Security Maintenance
- **Certificate Management**: SSL certificates renewed 30 days before expiration
- **API Keys**: Rotate every 90 days
- **JWT Secrets**: Rotate annually or when compromised
- **Patch Management**: Critical patches within 24 hours, security updates within 72 hours

## Database Migration

### Migration Files
Two migration files have been created in `backend/alembic/versions/`:

1. `f1f04095a338_initial_migration.py` - Creates the initial database schema
   - Creates `admin` table for administrators
   - Creates `user` table for regular users
   - Creates `document` table for translation documents

2. `e93ce913eabd_create_initial_admin_user.py` - Creates the initial admin user
   - Creates a system administrator account
   - Sets up initial credentials

### Initial Admin User
An initial admin user has been created with the following credentials:
- **Email**: `admin@translationsystem.com`
- **Full Name**: `System Administrator`
- **Password**: `Admin123!` (meets security requirements: 8+ chars, uppercase, lowercase, digit, special char)
- **Role**: Administrator (can manage users and system)

### Migration Commands
```bash
# Upgrade to latest version
python -m alembic upgrade head

# Check current version
python -m alembic current

# Downgrade to previous version (removes admin user)
python -m alembic downgrade base
```

## Frontend Framework

The frontend is built using React + TypeScript + Vite with the following features:

- HMR (Hot Module Replacement) for fast development
- ESLint configuration with type-aware linting
- React Compiler support (disabled by default due to performance impact)
- Recommended plugin: [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh

### Expanding the ESLint configuration

For production applications, it's recommended to enable type-aware lint rules by updating the configuration:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules.

## Terraform Infrastructure

The application includes Terraform configuration for deploying infrastructure on AWS with the following components:

- **Virtual Private Cloud (VPC)** with public and private subnets
- **Application Load Balancer** to distribute traffic
- **Auto Scaling Group** for the backend application
- **RDS PostgreSQL** managed database service
- **ElastiCache Redis** for caching
- **S3 Buckets** for object storage of documents and frontend assets
- **ECR Repositories** for container image storage
- **Secrets Manager** for secrets management
- **CloudFront CDN** for serving frontend assets
- **CloudWatch** for monitoring and logging

### Prerequisites
- AWS CLI configured with appropriate credentials
- Terraform v1.0 or higher installed
- An AWS account with permissions to create the resources defined in this configuration

### Getting Started
1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Review the example variables in `terraform.tfvars` and update them as needed

4. Optionally review the execution plan:
   ```bash
   terraform plan
   ```

5. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

6. Access the outputs to get connection details:
   ```bash
   terraform output
   ```

### Important Variables
- `project_name`: Name of the project (default: "ai-translation-service")
- `environment`: Environment name (dev, staging, prod) (default: "dev")
- `db_password`: Password for the RDS database (sensitive)
- `gemini_api_keys`: Google Gemini API keys (sensitive)

### Security Features
- Private subnets for application and database resources
- Security groups controlling access between resources
- Encrypted storage for S3 buckets and RDS database
- Secrets Manager for storing sensitive information
- Network segregation between public and private resources

### Clean Up
To destroy all resources created by this configuration:
```bash
terraform destroy
```

**Warning**: This will permanently delete all resources created by this configuration. Make sure to back up any important data before destroying.

## License

MIT — see [LICENSE](LICENSE).

## Contact Information

For support or questions:
- **Operations Team**: ops@aitranslationservice.com
- **Security Issues**: security@aitranslationservice.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Documentation**: For non-security related issues, use the standard support channels

---
