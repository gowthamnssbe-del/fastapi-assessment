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

## Optional Sections - Implementation Approach

### 1. AI Integration (If Implemented)

The following approach would be taken to integrate AI capabilities:

#### A. AI-Powered Product Recommendations

**Architecture:**
```
User Request → API Gateway → Recommendation Service → ML Model → Cache → Response
```

**Implementation Steps:**
1. **Create AI Service Module** (`app/services/ai_service.py`):
   - Integrate with OpenAI API or similar LLM provider
   - Implement product recommendation based on user browsing history
   - Add semantic search using embeddings for natural language product queries

2. **Add AI Endpoints** (`app/api/endpoints/ai.py`):
   ```python
   @router.post("/recommendations")
   async def get_recommendations(user_id: str, limit: int = 5):
       # Get user purchase/view history
       # Call AI service for recommendations
       # Cache results for performance
       pass
   
   @router.post("/search/smart")
   async def smart_search(query: str):
       # Use embeddings for semantic search
       # Return relevant products beyond keyword matching
       pass
   ```

3. **Environment Configuration**:
   ```env
   OPENAI_API_KEY=sk-xxx
   AI_MODEL=gpt-4
   EMBEDDING_MODEL=text-embedding-ada-002
   ```

4. **Caching Strategy**:
   - Cache embeddings for products (updated on product changes)
   - Cache recommendation results per user (TTL: 1 hour)

#### B. AI-Powered Product Description Generation

```python
@router.post("/products/{product_id}/generate-description")
async def generate_description(product_id: str):
    """Generate SEO-optimized product description using AI"""
    product = await ProductService.get_by_id(product_id)
    prompt = f"Write a compelling product description for: {product.name}"
    description = await ai_service.generate_content(prompt)
    return {"description": description}
```

---

### 2. CI/CD Pipeline (If Implemented)

A comprehensive CI/CD pipeline using GitHub Actions would be implemented as follows:

#### A. Test Workflow (`.github/workflows/test.yml`)

```yaml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install flake8 black isort mypy
      
      - name: Run linting
        run: |
          flake8 app tests --max-line-length=100
          black --check app tests
          isort --check-only app tests
      
      - name: Run type checking
        run: mypy app --ignore-missing-imports
      
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci-pipeline
        run: |
          pytest --cov=app --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

#### B. Build & Push Docker Image (`.github/workflows/build.yml`)

```yaml
name: Build & Push

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_USERNAME }}/fastapi-assessment
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### C. Deployment Workflow (`.github/workflows/deploy.yml`)

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: fastapi-assessment
  ECS_SERVICE: fastapi-service
  ECS_CLUSTER: production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: task-definition.json
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
      
      - name: Run database migrations
        run: |
          # Connect to ECS task and run migrations
          aws ecs run-task --cluster $ECS_CLUSTER --task-definition migration-task
      
      - name: Health check
        run: |
          curl -f https://api.example.com/health || exit 1
```

#### D. Pipeline Summary

| Stage | Trigger | Actions |
|-------|---------|---------|
| **Test** | Push/PR to main/develop | Lint, type-check, test, coverage |
| **Build** | Push to main, tags | Build Docker image, push to registry |
| **Deploy** | Push to main | Deploy to ECS, run migrations, health check |

#### E. Required GitHub Secrets

```
DOCKER_USERNAME          - Docker Hub username
DOCKER_PASSWORD          - Docker Hub password/token
AWS_ACCESS_KEY_ID        - AWS access key
AWS_SECRET_ACCESS_KEY    - AWS secret key
SECRET_KEY               - Production app secret
DATABASE_URL             - Production database URL
REDIS_URL                - Production Redis URL
```

---

## License

MIT License
