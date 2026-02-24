# FastAPI Developer Assessment

A comprehensive FastAPI application demonstrating clean architecture, authentication, caching, and Docker deployment.

## Features

- **FastAPI** with async/await support
- **Clean Architecture** with multi-layer structure
- **Authentication & Authorization**: OAuth2 password flow with JWT tokens, RBAC
- **Redis Caching**: Cache lists, details, search results with automatic invalidation
- **Docker**: Multi-stage Dockerfile with production-ready configuration
- **Testing**: Pytest async tests for auth, CRUD, cache, and RBAC

## Project Structure

```
app/
├── api/
│   ├── endpoints/
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── products.py     # Product CRUD endpoints
│   │   └── users.py        # User management endpoints
│   └── router.py           # API router aggregation
├── core/
│   ├── config.py           # Application settings
│   ├── security.py         # JWT and password handling
│   └── middleware.py       # Logging and error handling
├── db/
│   └── database.py         # Async SQLAlchemy setup
├── models/
│   ├── base.py             # Base model with UUID and soft delete
│   ├── user.py             # User model with RBAC
│   ├── product.py          # Product model
│   └── schemas.py          # Pydantic schemas
├── services/
│   ├── user_service.py     # User business logic
│   └── product_service.py  # Product business logic with caching
├── cache/
│   ├── redis_client.py     # Redis client wrapper
│   └── cache_service.py    # Product caching service
├── utils/
│   └── auth.py             # Auth dependencies
└── main.py                 # Application entry point

tests/
├── conftest.py             # Test fixtures
├── test_auth.py            # Authentication tests
├── test_products.py        # Product CRUD tests
├── test_cache.py           # Caching tests
└── test_rbac.py            # RBAC tests
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for development)
- Redis

### Local Development

1. **Clone and setup virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the application**
   ```bash
   # Development mode with hot reload
   uvicorn app.main:app --reload
   
   # Or run directly
   python -m app.main
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Deployment

1. **Start all services**
   ```bash
   # Development
   docker-compose up -d
   
   # Production
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f api
   ```

3. **Stop services**
   ```bash
   docker-compose down
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::TestLogin::test_login_success -v
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | None |
| POST | `/api/v1/auth/login` | OAuth2 login | None |
| POST | `/api/v1/auth/login/json` | JSON login | None |
| POST | `/api/v1/auth/refresh` | Refresh tokens | None |
| GET | `/api/v1/auth/me` | Get current user | Required |

### Products

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/products` | List products (paginated, filtered, sorted) | None |
| GET | `/api/v1/products/search` | Search products | None |
| GET | `/api/v1/products/{id}` | Get product by ID | None |
| POST | `/api/v1/products` | Create product | Admin |
| PUT | `/api/v1/products/{id}` | Update product | Admin |
| DELETE | `/api/v1/products/{id}` | Delete product (soft) | Admin |

### Users (Admin Only)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/users` | List all users | Admin |
| GET | `/api/v1/users/{id}` | Get user by ID | Admin/Self |
| PUT | `/api/v1/users/{id}` | Update user | Admin/Self |
| DELETE | `/api/v1/users/{id}` | Delete user | Admin |
| PUT | `/api/v1/users/{id}/role` | Update user role | Admin |

## Query Parameters

### Product List Filtering

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)
- `name`: Filter by name (partial match)
- `category`: Filter by category
- `min_price`: Minimum price
- `max_price`: Maximum price
- `in_stock_only`: Only show in-stock items
- `sort_by`: Sort field (name, price, created_at, stock)
- `sort_order`: Sort order (asc, desc)

### Example Requests

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user1", "password": "SecurePass123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user1&password=SecurePass123"

# Get products with filtering
curl "http://localhost:8000/api/v1/products?category=Electronics&min_price=10&sort_by=price&sort_order=asc"

# Create product (admin only)
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": 29.99, "sku": "SKU-001"}'
```

## Database Models

### User
- UUID primary key
- Email (unique)
- Username (unique)
- Hashed password (bcrypt)
- Role (admin/user)
- Soft delete support

### Product
- UUID primary key
- Name, description
- Price (decimal precision)
- Stock quantity
- Category
- SKU (unique)
- Soft delete support

## Caching Strategy

- **Product Lists**: Cached with page, page_size, and filter hash
- **Product Details**: Cached by product ID
- **Search Results**: Cached by query hash
- **Cache Invalidation**: Automatic on create/update/delete operations

## RBAC (Role-Based Access Control)

| Role | Permissions |
|------|-------------|
| user | View products, manage own profile |
| admin | All user permissions + manage products, manage all users |

## CI/CD Pipeline (Explanation)

For production deployment, implement:

### 1. Automated Tests Pipeline
```yaml
# .github/workflows/test.yml
- Run linting (flake8, black, isort)
- Run type checking (mypy)
- Run unit tests with coverage
- Upload coverage report
```

### 2. Docker Image Publishing
```yaml
# .github/workflows/build.yml
- Build Docker image
- Tag with version/sha
- Push to Docker Hub/ECR
```

### 3. Deployment Workflow
```yaml
# .github/workflows/deploy.yml
- Deploy to staging on develop branch
- Deploy to production on main branch
- Run database migrations
- Health check after deployment
```

## License

MIT License
