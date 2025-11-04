# Safelift AI - Backend API

**Intelligent AI Assistant for Elevator Troubleshooting & Support**

A Django REST Framework-based backend API that powers an AI-driven troubleshooting system for elevator maintenance and support. The system provides multilingual (English & Swedish) conversational AI, knowledge base management, escalation tracking, and comprehensive analytics.

---

## 🚀 Features

### Core Functionality
- **🤖 AI-Powered Conversations** - Handle customer queries with intelligent responses
- **📚 Knowledge Base Management** - Bilingual (EN/SV) troubleshooting solutions with vector embeddings
- **⚡ Smart Escalations** - Automatic escalation of complex issues to human operators
- **📊 Analytics Dashboard** - Real-time metrics and insights
- **📤 Data Export** - Export conversations, knowledge base, and analytics (CSV, JSON, PDF)
- **🔐 JWT Authentication** - Secure token-based authentication for admin users
- **🌍 Multilingual Support** - English and Swedish language support

### Technical Features
- **Vector Search** - Pinecone integration for semantic search in knowledge base
- **OpenAI Integration** - GPT-powered responses and embeddings
- **RESTful API** - Clean, well-documented REST API
- **Swagger/ReDoc** - Auto-generated API documentation
- **Role-Based Access** - Admin and user role separation
- **Comprehensive Testing** - Test coverage for critical components

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [What's Implemented](#whats-implemented)
- [What's Missing](#whats-missing)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## 💻 System Requirements

- **Python**: 3.12+
- **Database**: SQLite (development) / PostgreSQL (production recommended)
- **External Services**:
  - OpenAI API (for AI responses and embeddings)
  - Pinecone (for vector storage and search)

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Safelift-AI
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the example environment file and configure it:

```bash
# Rename env.example to .env
cp env.example .env
```

Edit `.env` with your actual values (see [Configuration](#configuration) section below).

---

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

### Required Configuration

```env
# Django Core
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT Authentication
JWT_SIGNING_KEY=your-jwt-signing-key-here

# CORS (Frontend origins)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key

# Pinecone Vector Database
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=safelift-knowledge-base
```

### Optional Configuration

```env
# PostgreSQL (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/safelift

# Email (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True
```

---

## 🗄️ Database Setup

### Development (SQLite)

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Follow prompts to create admin account
```

### Production (PostgreSQL)

1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE safelift;
   CREATE USER safelift_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE safelift TO safelift_user;
   ```
3. Update `.env` with DATABASE_URL
4. Run migrations as above

---

## 🚀 Running the Application

### Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

### Access Points

- **API Root**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/

### Main API Endpoints

#### Authentication
```
POST   /api/auth/login/          - Admin login
POST   /api/auth/logout/         - Logout
POST   /api/auth/refresh/        - Refresh JWT token
GET    /api/auth/readyz/         - Readiness probe
GET    /api/auth/livez/          - Liveness probe
```

#### Dashboard
```
GET    /api/dashboard/overview/              - Dashboard metrics
GET    /api/dashboard/language-distribution/ - Language stats
GET    /api/dashboard/quick-actions/         - Quick action items
GET    /api/dashboard/health/                - System health
```

#### Users
```
GET    /api/users/               - List users (admin)
POST   /api/users/               - Create user (admin)
GET    /api/users/{id}/          - Get user details
PUT    /api/users/{id}/          - Update user
PATCH  /api/users/{id}/          - Partial update user
DELETE /api/users/{id}/          - Delete user (admin)
```

#### Conversations
```
GET    /api/conversations/                    - List conversations
POST   /api/conversations/                    - Create conversation
GET    /api/conversations/{id}/               - Get conversation details
PUT    /api/conversations/{id}/               - Update conversation
DELETE /api/conversations/{id}/               - Delete conversation
GET    /api/conversations/stats/              - Conversation statistics
POST   /api/conversations/{id}/escalate/      - Escalate conversation
POST   /api/conversations/{id}/resolve/       - Resolve conversation
GET    /api/conversations/logs/               - Session logs
```

#### Knowledge Base
```
GET    /api/knowledge-base/                   - List entries
POST   /api/knowledge-base/                   - Create entry
GET    /api/knowledge-base/{id}/              - Get entry details
PUT    /api/knowledge-base/{id}/              - Update entry
PATCH  /api/knowledge-base/{id}/              - Partial update
DELETE /api/knowledge-base/{id}/              - Delete entry
POST   /api/knowledge-base/{id}/regenerate_embeddings/ - Regenerate embeddings
POST   /api/knowledge-base/{id}/toggle_status/         - Toggle active/inactive
POST   /api/knowledge-base/search/            - Semantic search
GET    /api/knowledge-base/stats/             - KB statistics
GET    /api/knowledge-base/categories/        - List categories
```

#### Escalations
```
GET    /api/escalations/                      - List escalations
GET    /api/escalations/{id}/                 - Get escalation details
PUT    /api/escalations/{id}/                 - Update escalation
PATCH  /api/escalations/{id}/                 - Partial update
POST   /api/escalations/{id}/set-status/      - Update status
GET    /api/escalations/stats/                - Escalation statistics
```

#### Data Export
```
GET    /api/export-data/                      - List exports
POST   /api/export-data/                      - Create export
GET    /api/export-data/{id}/                 - Get export details
POST   /api/export-data/{id}/retry/           - Retry failed export
GET    /api/export-data/{id}/download/        - Download export file
```

---

## 📁 Project Structure

```
Safelift-AI/
├── apps/
│   ├── authentication/          # JWT authentication & login
│   │   ├── services.py         # Authentication business logic
│   │   ├── serializers.py      # Auth serializers
│   │   ├── views.py            # Auth endpoints
│   │   └── urls.py             # Auth routes
│   │
│   ├── users/                   # User management
│   │   ├── models.py           # Custom User model
│   │   ├── serializers.py      # User serializers
│   │   ├── views.py            # User CRUD endpoints
│   │   ├── permissions.py      # Custom permissions
│   │   └── urls.py             # User routes
│   │
│   ├── conversations/           # Conversation tracking
│   │   ├── models.py           # ConversationHistory, ConversationLogs
│   │   ├── services.py         # Conversation business logic
│   │   ├── serializers.py      # Conversation serializers
│   │   ├── views.py            # Conversation endpoints
│   │   ├── constants.py        # App constants
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── tests/              # Comprehensive test suite
│   │   └── urls.py             # Conversation routes
│   │
│   ├── knowledge_base/          # Knowledge base management
│   │   ├── models.py           # KnowledgeBaseEntry model
│   │   ├── services.py         # Embedding generation & search
│   │   ├── serializers.py      # KB serializers
│   │   ├── views.py            # KB endpoints
│   │   ├── utils.py            # Helper functions
│   │   └── urls.py             # KB routes
│   │
│   ├── escalations/             # Escalation management
│   │   ├── models.py           # Escalation model
│   │   ├── services.py         # Escalation business logic
│   │   ├── serializers.py      # Escalation serializers
│   │   ├── views.py            # Escalation endpoints
│   │   └── urls.py             # Escalation routes
│   │
│   ├── dashboard/               # Dashboard metrics
│   │   ├── models.py           # DashboardMetric, LanguageDistribution
│   │   ├── services.py         # Metrics calculation
│   │   ├── serializers.py      # Dashboard serializers
│   │   ├── views.py            # Dashboard endpoints
│   │   ├── management/         # Management commands
│   │   │   └── commands/
│   │   │       └── update_dashboard_metrics.py
│   │   └── urls.py             # Dashboard routes
│   │
│   └── export_data/             # Data export functionality
│       ├── models.py           # Export model
│       ├── services.py         # Export business logic
│       ├── exporters.py        # Export format handlers
│       ├── serializers.py      # Export serializers
│       ├── views.py            # Export endpoints
│       ├── constants.py        # Export constants
│       ├── exceptions.py       # Export exceptions
│       ├── utils.py            # Export utilities
│       ├── tests.py            # Export tests
│       └── urls.py             # Export routes
│
├── safelift/                    # Project configuration
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI configuration
│   └── asgi.py                 # ASGI configuration
│
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
├── .gitignore                   # Git ignore rules
├── db.sqlite3                   # SQLite database (dev)
└── README.md                    # This file
```

---

## ✅ What's Implemented

### Complete & Functional

#### 1. **Authentication System** ✅
- JWT-based authentication
- Admin login/logout
- Token refresh mechanism
- Role-based access control (Admin/User)
- Readiness & liveness probes

#### 2. **User Management** ✅
- Custom User model with roles
- CRUD operations for users
- Admin-only access controls
- User serializers with validation

#### 3. **Conversation System** ✅
- Full conversation tracking
- Status management (active, resolved, escalated, pending)
- Multilingual support (EN/SV)
- Session-level aggregation
- Filtering & search
- Escalation & resolution actions
- **Comprehensive test suite** (6 test files)

#### 4. **Knowledge Base** ✅
- Bilingual entry management (EN/SV)
- OpenAI embeddings generation
- Pinecone vector storage
- Semantic search
- Category management
- Status toggle (active/inactive)
- Statistics & analytics

#### 5. **Escalation Management** ✅
- Escalation creation from conversations
- Status tracking (pending, in-progress, resolved)
- Priority management (low, medium, high)
- Customer context tracking
- Internal notes
- Summary statistics

#### 6. **Dashboard & Analytics** ✅
- Real-time metrics
- Conversation statistics
- Language distribution
- Response time tracking
- Escalation metrics
- Quick actions

#### 7. **Data Export** ✅
- Multiple formats (CSV, JSON, PDF)
- Multiple data types (conversations, KB, escalations, analytics)
- Date range filtering
- Privacy controls (PII inclusion option)
- Status tracking & retry mechanism
- **Test coverage**

#### 8. **API Documentation** ✅
- Auto-generated Swagger UI
- ReDoc documentation
- DRF Spectacular integration
- Well-documented endpoints

#### 9. **Code Quality** ✅
- Clean Code principles
- Service layer architecture
- Comprehensive serializers
- Custom exceptions
- Constants management
- Logging throughout

---

## ⚠️ What's Missing (Backend-Specific)

### Critical Gaps

#### 1. **Async Task Processing** ❌
**Problem**: Export jobs and embedding generation are synchronous
**Impact**: Long-running operations block HTTP requests
**Solution Needed**:
```python
# Need to implement Celery + Redis
# apps/export_data/tasks.py
from celery import shared_task

@shared_task
def process_export(export_id):
    # Async export processing
    pass
```
**Files to create**:
- `safelift/celery.py` - Celery configuration
- `apps/export_data/tasks.py` - Async export tasks
- `apps/knowledge_base/tasks.py` - Async embedding tasks

**Dependencies to add**:
```txt
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
```

#### 2. **Missing Tests** ❌
Test coverage gaps:
- ❌ `apps/authentication/` - No tests
- ❌ `apps/users/` - No tests
- ❌ `apps/dashboard/` - No tests
- ❌ `apps/escalations/` - No tests
- ❌ `apps/knowledge_base/` - No tests
- ✅ `apps/conversations/` - Complete (reference these!)
- ✅ `apps/export_data/` - Has tests

#### 3. **Database Migrations** ⚠️
**Status**: Migrations exist locally but are gitignored
**Action Required**: 
- Run migrations on new installations
- Consider tracking initial migrations in git
- Document migration process

#### 4. **Production Configuration** ❌
Missing:
- PostgreSQL configuration
- Static file serving (WhiteNoise)
- Gunicorn/uWSGI setup
- nginx configuration
- SSL/HTTPS setup
- Environment-specific settings

#### 5. **API Rate Limiting** ❌
No rate limiting configured - vulnerable to abuse
**Solution**: Add `django-ratelimit` or DRF throttling

#### 6. **Background Job Monitoring** ❌
No monitoring for:
- Embedding generation status
- Export job progress
- Failed task retry logic

### Medium Priority Gaps

#### 7. **Email Notifications** ⚠️
Email configuration exists but not implemented:
- Escalation notifications
- Export completion emails
- System alerts

#### 8. **API Versioning** ❌
No versioning strategy (e.g., `/api/v1/`)

#### 9. **Comprehensive Logging** ⚠️
Basic logging exists but needs:
- Structured JSON logging
- Log aggregation setup
- Error tracking (Sentry integration)

#### 10. **Data Validation** ⚠️
Additional validation needed:
- File upload size limits enforced
- Request payload validation
- Input sanitization

### Nice to Have

#### 11. **Docker Setup** ❌
No containerization:
- `Dockerfile`
- `docker-compose.yml`
- Development & production configs

#### 12. **CI/CD Pipeline** ❌
No automated testing/deployment:
- GitHub Actions
- GitLab CI
- Pre-commit hooks

#### 13. **Code Quality Tools** ❌
Missing:
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks

#### 14. **Performance Optimization** ⚠️
Could improve:
- Database query optimization (select_related, prefetch_related)
- Caching (Redis)
- Connection pooling
- Database indexing review

#### 15. **Security Enhancements** ⚠️
Consider adding:
- API key rotation mechanism
- Password reset functionality
- Two-factor authentication
- Security headers middleware
- CORS refinement

---

## 🧪 Testing

### Test Coverage Status

All backend apps now have comprehensive test coverage:
- ✅ **Authentication** - Login, logout, JWT tokens, probes
- ✅ **Users** - Models, views, serializers, permissions
- ✅ **Dashboard** - Metrics, views, services
- ✅ **Escalations** - Models, views, services, serializers
- ✅ **Knowledge Base** - Models, views, services (with mocking)
- ✅ **Conversations** - Complete test suite (reference implementation)
- ✅ **Export Data** - Export functionality tests

### Run All Tests

```bash
# Run complete test suite
python manage.py test

# Run tests with verbosity
python manage.py test --verbosity=2

# Run tests in parallel (faster)
python manage.py test --parallel
```

### Run Tests for Specific App

```bash
# Authentication tests
python manage.py test apps.authentication

# Users tests
python manage.py test apps.users

# Dashboard tests
python manage.py test apps.dashboard

# Escalations tests
python manage.py test apps.escalations

# Knowledge Base tests
python manage.py test apps.knowledge_base

# Conversations tests
python manage.py test apps.conversations

# Export Data tests
python manage.py test apps.export_data
```

### Run Specific Test File or Class

```bash
# Run specific test file
python manage.py test apps.authentication.tests.test_views

# Run specific test class
python manage.py test apps.authentication.tests.test_views.LoginViewTest

# Run specific test method
python manage.py test apps.authentication.tests.test_views.LoginViewTest.test_login_with_valid_admin_credentials
```

### Test Coverage

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# View coverage report in terminal
coverage report

# Generate detailed HTML coverage report
coverage html

# Open HTML report (will be in htmlcov/index.html)
# On Windows:
start htmlcov/index.html
# On Mac/Linux:
open htmlcov/index.html
```

### Writing Tests

#### Test Structure
Reference existing test files for structure and patterns:

```
apps/<app_name>/tests/
├── __init__.py
├── test_models.py        # Model functionality tests
├── test_serializers.py   # Serializer validation tests
├── test_views.py         # API endpoint tests
├── test_services.py      # Business logic tests
└── test_permissions.py   # Permission tests (if applicable)
```

#### Using Test Helpers

```python
from apps.tests.test_helpers import (
    create_test_user,
    create_admin_user,
    get_auth_token,
    APITestCaseBase
)

class MyTestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.admin = create_admin_user()
        self.user = create_test_user()
        
        # Authenticate
        self.client.force_authenticate(user=self.admin)
    
    def test_something(self):
        # Your test here
        pass
```

#### Mocking External Services

For tests that interact with external APIs (OpenAI, Pinecone):

```python
from unittest.mock import patch, MagicMock

class MyServiceTest(TestCase):
    @patch('apps.knowledge_base.services.OpenAIEmbeddings')
    @patch('apps.knowledge_base.services.Pinecone')
    def test_with_mocks(self, mock_pinecone, mock_openai):
        # Setup mocks
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 1536
        mock_openai.return_value = mock_embeddings
        
        # Run your test
        # ...
```

### Test Best Practices

1. **Isolation**: Each test should be independent
2. **Clear Names**: Test names should describe what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Services**: Don't make real API calls in tests
5. **Test Edge Cases**: Include error scenarios and boundary conditions

### Continuous Testing

For development, you can use test watchers:

```bash
# Install pytest-watch (optional)
pip install pytest-watch

# Watch for changes and rerun tests
ptw --runner "python manage.py test"
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure PostgreSQL database
- [ ] Set up Celery + Redis for background tasks
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set secure `SECRET_KEY` and `JWT_SIGNING_KEY`
- [ ] Configure static file serving
- [ ] Set up nginx reverse proxy
- [ ] Enable HTTPS/SSL
- [ ] Configure proper logging
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Run security checks: `python manage.py check --deploy`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Run migrations: `python manage.py migrate`

### Recommended Production Stack

- **Web Server**: nginx
- **App Server**: Gunicorn
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Process Manager**: Supervisor or systemd
- **Monitoring**: Sentry, Prometheus
- **Logging**: ELK Stack or CloudWatch

---

## 🎯 Priority Action Items

### Immediate (Do First)

1. **Set up environment** - Copy `env.example` to `.env` and configure
2. **Run migrations** - `python manage.py migrate`
3. **Create superuser** - `python manage.py createsuperuser`
4. **Start development server** - Test all endpoints
5. **Write missing tests** - Start with authentication and users

### Short-term (Next Sprint)

6. **Implement Celery** - For async exports and embeddings
7. **Add rate limiting** - Protect API endpoints
8. **Set up Docker** - Containerize application
9. **Add monitoring** - Sentry for error tracking
10. **Write deployment docs** - Production setup guide

### Long-term (Future Improvements)

11. **Performance optimization** - Caching, query optimization
12. **API versioning** - Prepare for v2
13. **Advanced security** - 2FA, API key rotation
14. **Comprehensive monitoring** - APM, metrics dashboards
15. **Auto-scaling setup** - Cloud deployment

---

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Write tests** for your changes
5. **Run tests**: `python manage.py test`
6. **Commit**: `git commit -m 'Add amazing feature'`
7. **Push**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for classes and functions
- Keep functions small and focused (Clean Code principles)
- Use meaningful variable names

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Be descriptive: "Add user authentication tests" not "Add tests"
- Reference issues: "Fix #123: Resolve escalation bug"

---

## 📞 Support & Contact

For questions, issues, or contributions:
- **Issues**: [GitHub Issues](<repository-url>/issues)
- **Discussions**: [GitHub Discussions](<repository-url>/discussions)

---

## 📝 License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

---

## 🙏 Acknowledgments

- Django REST Framework
- OpenAI API
- Pinecone Vector Database
- All contributors and maintainers

---

**Built with ❤️ for safer, smarter elevator maintenance**

