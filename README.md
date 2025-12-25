# TAG_API - Themed Alias Game Backend

A robust, scalable REST API backend for **Themed Alias Game (TAG)**, a modern web-based implementation of the popular word-guessing game Alias. This API manages authentication, theme management, game state, and multiplayer game sessions.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
  - [Running the API](#running-the-api)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Themes Management](#themes-management)
  - [Games Management](#games-management)
- [Database](#database)
- [Architecture](#architecture)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🎮 Overview

TAG_API is the backend service powering the Themed Alias Game. It provides comprehensive REST API endpoints for:

- User authentication via Google OAuth 2.0
- Theme creation, management, and discovery
- Game lifecycle management (creation, updates, history)
- Game state persistence and resumption
- Real-time game synchronization

## ✨ Features

### 🔐 Authentication & Authorization

- **Google OAuth 2.0 Integration**: Seamless sign-in via Google accounts
- **JWT-based Token System**: Secure session management with custom JWT tokens
- **User Profiles**: Automatic user creation and profile management
- **Admin Panel Support**: Admin-level operations for theme verification and moderation

### 🎨 Theme Management

#### Theme Creation
- Create custom word themes with curated word lists
- Mark themes as public or private
- Support for multiple languages (ISO 639-1 alpha-2 codes)
- Difficulty levels (1-5 scale)
- Rich descriptions with metadata support

#### Theme Import
- Import themes from external sources
- Support for JSON-based theme imports
- Bulk theme creation capabilities

#### Theme Discovery & Filtering
- **By Language**: Filter themes by language (e.g., en, ru, fr)
- **By Difficulty**: Filter themes from Very Easy (1) to Very Hard (5)
- **My Themes**: View only themes you created
- **Favorites**: Access your favorite themes with one click
- **Verified Status**: Filter between verified and unverified community themes
- **Full-Text Search**: Search themes by name or description

#### Theme Ordering & Sorting
- Sort by creation date (newest/oldest first)
- Sort by popularity (play count)
- Alphabetical sorting (A-Z, Z-A)
- Custom ordering with pagination support

#### Theme Engagement
- Mark themes as favorites for quick access
- Track theme popularity via play counts
- Last played tracking for history

### 🎮 Game Management

#### Game Creation & Configuration
- Create games with custom configurations
- Set required points to win (target score)
- Configure round timer (15-300 seconds)
- Enable/disable skip penalties
- Assign starting teams and players

#### Game Lifecycle
- Track game state from creation to completion
- Support for multiplayer teams
- Real-time game info updates
- Word guessing and skipping tracking

#### Game History & Resumption
- Complete game history with final scores
- Resume unfinished games from last state
- Track words guessed and skipped per game
- Game statistics and performance metrics

#### Round Result Confirmation
- Server-side validation of round results
- Word classification (guessed/skipped) tracking
- Score accuracy verification
- Immutable game records post-confirmation

### 🔄 Game State Synchronization

- Automatic game state persistence
- Optimized database queries with pagination
- Redis caching for frequently accessed data
- Efficient synchronization between client and server

## 🏗️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast Python web framework
- **Database**: PostgreSQL with async SQLAlchemy support
- **ORM**: [SQLModel](https://sqlmodel.tiangolo.com/) - Combines SQLAlchemy and Pydantic
- **Cache**: [Redis](https://redis.io/) - For session management and caching
- **Authentication**: Google OAuth 2.0, JWT with cryptographic signing
- **Async**: AsyncIO with AsyncPG for non-blocking database operations
- **Validation**: Pydantic v2 for data validation and serialization
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Pagination**: FastAPI-Pagination for efficient list handling
- **Migrations**: Alembic for database schema versioning
- **Package Manager**: [UV](https://github.com/astral-sh/uv) - Fast Python package manager
- **Code Quality**: Ruff for linting and formatting
- **Pre-commit**: Git hooks for automated code checks

## 🚀 Getting Started

### Prerequisites

- Python 3.14+
- PostgreSQL 15+
- Redis 7+
- Google OAuth credentials (Client ID and Secret)
- UV package manager (installation: `pip install uv`)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd TAG_API
```

2. **Set up Python virtual environment**:
```bash
uv venv .venv --python python3.14
source .venv/bin/activate
# On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
uv sync
```

4. **Install pre-commit hooks** (optional but recommended):
```bash
uv pip install ruff pre-commit
pre-commit install
```

### Environment Setup

1. **Create `.env` file in the project root**:
```bash
cp .env.example .env
```

2. **Configure environment variables** in `.env`:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=password
DB_NAME=tag_db
DB_SSL_MODE=disable

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASS=
REDIS_NAME=0

# Google OAuth Configuration
OAUTH_GCLOUD_ID=your-google-client-id.apps.googleusercontent.com
OAUTH_GCLOUD_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/auth/token

# Frontend URL
FE_URL=http://localhost:5173

# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN_DAYS=30
```

3. **Obtain Google OAuth Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google+ API
   - Create OAuth 2.0 credentials (Web application)
   - Add authorized redirect URIs and JavaScript origins
   - Copy Client ID and Client Secret to `.env`

### Running the API

1. **Start PostgreSQL and Redis** (using Docker):
```bash
docker-compose up -d
```

2. **Run database migrations**:
```bash
alembic upgrade head
```

3. **Start the API server**:
```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive API Documentation

The API provides comprehensive OpenAPI/Swagger documentation that is automatically generated and interactive.

**Access the API documentation at**:
- **Swagger UI**: `http://localhost:8000/docs` - Interactive API explorer
- **ReDoc**: `http://localhost:8000/redoc` - Alternative API documentation viewer
- **OpenAPI JSON**: `http://localhost:8000/openapi.json` - Raw OpenAPI specification

The Swagger UI allows you to:
- View all available endpoints
- See request/response schemas
- Test endpoints directly in the browser
- Authenticate and make real API calls
- Explore error responses and status codes

### Available Endpoints

The API provides three main endpoint groups:

- **`/auth`** - Authentication and OAuth login flow
- **`/themes`** - Theme management (CRUD, filtering, favorites)
- **`/games`** - Game management (CRUD, history, state synchronization)

For detailed information about specific endpoints, their parameters, request bodies, and response formats, please refer to the interactive Swagger documentation.

## 🗄️ Database

### Schema Overview

#### Users Table
- `id`: Primary key
- `email`: Unique email address
- `picture`: User profile picture URL
- `admin`: Admin flag for moderation
- `last_login`: Last login timestamp
- `created_at`: Account creation time
- `updated_at`: Last update time

#### Themes Table
- `id`: Primary key
- `name`: Unique theme name
- `language`: ISO 639-1 language code
- `description`: JSON metadata
- `difficulty`: Level 1-5
- `verified`: Admin verification status
- `public`: Public/private visibility
- `played_count`: Usage statistics
- `last_played`: Last game timestamp
- `created_by`: Creator user ID
- `created_at`: Theme creation time
- `updated_at`: Last modification time

#### Games Table
- `id`: Primary key
- `theme_id`: Associated theme
- `started_by`: Starting user ID
- `started_at`: Game start time
- `ended_at`: Game completion time (null if ongoing)
- `points`: Target score to win
- `round`: Round timer in seconds
- `skip_penalty`: Boolean configuration
- `info`: JSON game state (teams, scores, etc.)
- `words_guessed`: JSON array of correctly guessed words
- `words_skipped`: JSON array of skipped words
- `created_at`: Game creation time
- `updated_at`: Last state update

#### Auth Table
- `user_id`: Foreign key to users
- `access_token`: Google OAuth access token
- `id_token`: Google OAuth ID token
- `created_at`: Token creation time
- `updated_at`: Token refresh time

#### User Favorite Themes (Link Table)
- `user_id`: User foreign key
- `theme_id`: Theme foreign key

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

View migration history:
```bash
alembic current
```

## 🏛️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│      API Layer (FastAPI routers)        │
│   (/api/auth, /api/themes, /api/games)  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Business Logic Layer (schemas)      │
│  Request/response validation & transform│
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Data Access Layer (dal.py)             │
│  Database queries & business logic      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Data Layer (db.py - SQLModel)        │
│    ORM models & database connection     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     PostgreSQL Database                 │
└─────────────────────────────────────────┘
```

### Key Components

- **API Routers** (`src/api/`): Request handlers and route definitions
- **Schemas** (`src/schemas/`): Pydantic models for validation
- **DAL** (`src/dal.py`): Database access logic
- **Models** (`src/db.py`): SQLModel ORM definitions
- **Cache** (`src/cache.py`): Redis client management
- **Utils** (`src/utils/`): Helper functions (OAuth, JWT)
- **Middleware**: CORS configuration, error handling

## 🛠️ Development

### Code Quality

The project uses automated code quality tools:

#### Ruff Configuration
- Line length: 120 characters
- Linting rules: E, W, F, I, N, UP, B, C4, SIM, RUF
- Auto-formatting enabled

#### Pre-commit Hooks
Pre-commit hooks automatically run before each git commit:

```bash
pre-commit run --all-files
```

Hooks include:
- Code formatting (black)
- Import sorting (isort)
- Linting (ruff)
- Type checking (mypy - optional)

### Project Structure

```
TAG_API/
├── src/
│   ├── api/              # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── game.py       # Game management endpoints
│   │   └── theme.py      # Theme management endpoints
│   ├── schemas/          # Pydantic validation models
│   │   ├── game.py       # Game schemas
│   │   ├── theme.py      # Theme schemas
│   │   └── user.py       # User schemas
│   ├── utils/            # Utility functions
│   │   └── oauth.py      # OAuth and JWT utilities
│   ├── cache.py          # Redis cache management
│   ├── conf.py           # Configuration & settings
│   ├── dal.py            # Database access layer
│   ├── db.py             # SQLModel definitions
│   ├── errors.py         # Custom exceptions
│   ├── log.py            # Logging configuration
│   ├── main.py           # FastAPI app initialization
│   └── validators.py     # Data validators
├── migrations/           # Alembic database migrations
├── tests/                # Test suite
├── docker-compose.yaml   # Docker services configuration
├── alembic.ini          # Alembic configuration
├── pyproject.toml       # Project metadata & dependencies
├── uv.lock              # Dependency lock file
└── README.md            # This file
```

### Running Tests

```bash
pytest
```

Run specific test:
```bash
pytest tests/test_ping.py -v
```

Run with coverage:
```bash
pytest --cov=src
```

### Debugging

Enable SQL debug logging:
```python
engine = create_async_engine(DATABASE_URL, echo=True)
```

### Common Commands

```bash
# Format code
ruff format .

# Check for linting issues
ruff check .

# Fix linting issues
ruff check . --fix

# Type checking
mypy src/

# Database shell
psql -U postgres -d tag_db -h localhost

# Redis CLI
redis-cli -n 0

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## 🔐 Security Considerations

1. **Environment Variables**: Never commit `.env` file. Use `.env.example` template.
2. **OAuth Credentials**: Keep Client Secret secure. Rotate periodically.
3. **JWT Secret**: Use strong secret in production. Generate with: `openssl rand -hex 32`
4. **CORS**: Whitelist only trusted frontend URLs in production
5. **HTTPS**: Always use HTTPS in production
6. **SQL Injection**: Protected by SQLModel ORM and Pydantic validation

## 🚢 Deployment

### Docker

Build Docker image:
```bash
docker build -t tag-api:latest .
```

Run container:
```bash
docker run -p 8000:8000 --env-file .env tag-api:latest
```

### Production Checklist

- [ ] Set `DEBUG = false`
- [ ] Update `CORS_ORIGINS` to production frontend URL
- [ ] Use strong `JWT_SECRET` (32+ random characters)
- [ ] Set up HTTPS with SSL certificates
- [ ] Enable PostgreSQL SSL connections
- [ ] Set up Redis password

## 📞 Support & Issues

For issues, feature requests, or questions:
1. Check existing issues on GitHub
2. Provide detailed error messages and reproduction steps
3. Include system and environment information

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI framework and ecosystem
- SQLModel for elegant ORM integration
- Google OAuth for authentication
- PostgreSQL and Redis communities
