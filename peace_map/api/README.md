# Peace Map API

REST API for Peace Map - Global Risk Assessment and Supply Chain Monitoring.

## Features

- **Event Management**: Create, read, update, and delete events
- **Risk Assessment**: Calculate and track risk indices
- **Supplier Management**: Manage supplier data and risk monitoring
- **Alert System**: Configure and manage risk alerts
- **Authentication**: JWT-based authentication and authorization
- **Rate Limiting**: Built-in rate limiting and security
- **Documentation**: Auto-generated API documentation

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd peace_map
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   uvicorn peace_map.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## API Endpoints

### Events

- `GET /api/v1/projects/{project_id}/events` - List events
- `GET /api/v1/projects/{project_id}/events/{event_id}` - Get event
- `POST /api/v1/projects/{project_id}/events` - Create event
- `PUT /api/v1/projects/{project_id}/events/{event_id}` - Update event
- `DELETE /api/v1/projects/{project_id}/events/{event_id}` - Delete event

### Risk Index

- `GET /api/v1/risk-index` - Get risk index data

### Suppliers

- `GET /api/v1/suppliers` - List suppliers
- `GET /api/v1/suppliers/{supplier_id}` - Get supplier
- `POST /api/v1/suppliers` - Create supplier
- `PUT /api/v1/suppliers/{supplier_id}` - Update supplier
- `DELETE /api/v1/suppliers/{supplier_id}` - Delete supplier
- `POST /api/v1/suppliers/upload` - Upload suppliers CSV

### Alerts

- `GET /api/v1/alerts` - List alerts
- `GET /api/v1/alerts/{alert_id}` - Get alert
- `POST /api/v1/alerts` - Create alert
- `PUT /api/v1/alerts/{alert_id}` - Update alert
- `DELETE /api/v1/alerts/{alert_id}` - Delete alert
- `POST /api/v1/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `POST /api/v1/alerts/{alert_id}/resolve` - Resolve alert

## Authentication

The API uses JWT-based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

- Default: 60 requests per minute per IP
- Configurable via `RATE_LIMIT_CALLS_PER_MINUTE` environment variable

## Error Handling

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Error Type",
  "message": "Human-readable error message",
  "details": {} // Optional additional details
}
```

## Development

### Code Style

- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Production Deployment

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `DEBUG`: Set to `false` in production

### Security

- Use HTTPS in production
- Configure proper CORS origins
- Set strong secret keys
- Enable rate limiting
- Use trusted hosts

### Monitoring

- Health check endpoint: `/health`
- Metrics endpoint: `/metrics` (if enabled)
- Structured logging

## License

MIT License - see LICENSE file for details.
