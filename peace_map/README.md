# Peace Map - Global Risk Intelligence Platform

A comprehensive platform for monitoring global events, assessing regional risks, and managing supply chain vulnerabilities through real-time data ingestion, NLP analysis, and interactive mapping.

## 🎯 Overview

Peace Map provides a unified view of global risk factors by aggregating data from multiple sources, analyzing events through NLP, and presenting actionable intelligence through interactive maps and dashboards.

## 🏗️ Architecture

### Core Components

1. **Data Ingestion Layer**
   - RSS/Atom feed connectors
   - GDELT 2.0 event data integration
   - ACLED-style CSV import system
   - Maritime advisories JSON parser

2. **NLP Processing Pipeline**
   - Event deduplication
   - Category classification (protest, cyber, kinetic)
   - Geocoding with Nominatim
   - Text embedding generation

3. **Geographic Intelligence**
   - Country/region heatmaps
   - Port chokepoints visualization
   - Shipping lanes overlay
   - Risk zone mapping

4. **Risk Scoring Engine**
   - Daily composite risk index (0-100)
   - Weighted feature analysis
   - Event count aggregation
   - Sentiment analysis integration
   - Proximity-based risk assessment

5. **Supply Chain Management**
   - Supplier CSV upload
   - Regional risk correlation
   - Threshold-based alerting
   - Risk badge system

## 🚀 Features

### Data Sources
- **RSS/Atom Feeds**: News and information feeds
- **GDELT 2.0**: Global event database
- **ACLED**: Armed Conflict Location & Event Data
- **Maritime Advisories**: Shipping and port information

### Analytics
- **Event Classification**: Automatic categorization of events
- **Geocoding**: Location extraction and mapping
- **Deduplication**: Remove duplicate events
- **Sentiment Analysis**: Risk sentiment scoring
- **Anomaly Detection**: Unusual pattern identification

### Visualization
- **Interactive Maps**: Multi-layer geographic visualization
- **Time Slider**: Historical data exploration
- **Risk Heatmaps**: Regional risk intensity
- **Supply Chain Overlay**: Supplier location mapping

### Alerting
- **Threshold Alerts**: Risk level notifications
- **Anomaly Alerts**: Unusual activity detection
- **Supply Chain Alerts**: Supplier risk notifications
- **Custom Rules**: User-defined alert conditions

## 📊 API Endpoints

### Events
- `GET /projects/{id}/events` - List events with filtering
- `GET /projects/{id}/events/{event_id}` - Get specific event
- `POST /projects/{id}/events/query` - Advanced event query

### Risk Assessment
- `GET /projects/{id}/risk-index` - Get risk index data
- `GET /projects/{id}/risk-index/{region}` - Regional risk data
- `POST /projects/{id}/risk-index/calculate` - Trigger risk calculation

### Supply Chain
- `GET /projects/{id}/suppliers` - List suppliers
- `POST /projects/{id}/suppliers` - Add supplier
- `PUT /projects/{id}/suppliers/{id}` - Update supplier
- `DELETE /projects/{id}/suppliers/{id}` - Remove supplier
- `POST /projects/{id}/suppliers/upload` - Bulk upload CSV

### Alerts
- `GET /projects/{id}/alerts` - List alerts
- `POST /projects/{id}/alerts` - Create alert rule
- `PUT /projects/{id}/alerts/{id}` - Update alert rule
- `DELETE /projects/{id}/alerts/{id}` - Delete alert rule

## 🔧 Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/peace_map
REDIS_URL=redis://localhost:6379

# External APIs
NOMINATIM_API_URL=https://nominatim.openstreetmap.org
GDELT_API_URL=https://api.gdeltproject.org/api/v2
OPENAI_API_KEY=your_openai_key

# Background Jobs
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (for frontend)

### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start background workers
celery -A peace_map worker -l info
```

### Frontend Setup
```bash
cd frontend
npm install
npm run build
```

## 📈 Usage

### Basic Event Monitoring
```python
from peace_map.core import PeaceMapClient

# Initialize client
client = PeaceMapClient(project_id="your-project-id")

# Get recent events
events = client.get_events(
    date_range=("2024-01-01", "2024-01-31"),
    region="Europe",
    event_types=["protest", "cyber"]
)

# Get risk index
risk_data = client.get_risk_index(region="Europe")
```

### Supply Chain Management
```python
# Upload supplier data
suppliers = client.upload_suppliers("suppliers.csv")

# Set up risk alerts
alert = client.create_alert(
    name="High Risk Suppliers",
    condition="risk_score > 70",
    suppliers=suppliers
)
```

### Custom Analytics
```python
# Custom risk calculation
risk_factors = {
    "event_count": 0.4,
    "sentiment": 0.3,
    "proximity_to_ports": 0.3
}

risk_score = client.calculate_risk(
    region="Middle East",
    factors=risk_factors
)
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/unit/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### End-to-End Tests
```bash
python -m pytest tests/e2e/
```

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [User Manual](docs/user_manual.md)
- [Developer Guide](docs/developer_guide.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for legitimate risk assessment and supply chain management purposes only. Users are responsible for:
- Complying with data privacy regulations
- Using the tool ethically and responsibly
- Respecting data source terms of service
- Following applicable laws and regulations
