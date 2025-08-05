# Incident Response Chatbot

A professional chatbot interface for incident response that correlates data from multiple monitoring systems to help identify what changed recently and focus troubleshooting efforts.

## Features

- **🤖 AI-Powered Analysis**: OpenAI GPT-4 and Anthropic Claude integration for intelligent incident analysis
- **💬 Natural Language Queries**: Ask complex questions like "Why are we seeing these errors?" or "What should I investigate first?"
- **🧠 Context-Aware Responses**: Maintains conversation history and builds on previous interactions
- **🔄 Real-time Analysis**: Queries multiple monitoring systems simultaneously
- **🔗 Change Correlation**: Identifies relationships between deployments, errors, and alerts
- **🎨 Professional UI**: Clean, responsive chat interface with AI-powered suggestions
- **🔌 Multi-source Integration**: Supports Grafana, Prometheus, Elasticsearch, Nagios, and more
- **📊 Hybrid Approach**: Combines AI intelligence with traditional monitoring data analysis
- **🚀 Mock Data**: Includes sample data for testing without live systems

## Architecture

- **Backend**: FastAPI with async connectors for monitoring systems and LLM integration
- **Frontend**: React with TypeScript, Tailwind CSS, and professional styling
- **AI Layer**: OpenAI/Anthropic integration with specialized incident response prompts
- **Memory**: Conversation persistence and context management
- **Real-time**: WebSocket-ready architecture for live updates and streaming responses

## Installation & Setup

### Prerequisites

- Python 3.11+ 
- Node.js 18+
- npm or yarn

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chatter
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Deployment

#### Quick Start with Docker

```bash
# Clone and setup
git clone <repository-url>
cd chatter

# Create environment file
cp .env.example .env
# Edit .env with your monitoring system URLs and credentials

# Development mode (with live reload)
docker-compose up --build

# Production mode (optimized, with nginx)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

#### Docker Environment Files

- **`.env.example`** - Template with all configuration options
- **`.env`** - Your actual environment variables (create from example)
- **`docker-compose.yml`** - Base configuration  
- **`docker-compose.override.yml`** - Development overrides (auto-loaded)
- **`docker-compose.prod.yml`** - Production overrides

#### Docker Commands

```bash
# Development (with live reload and direct port access)
docker-compose up --build

# Production (with nginx, health checks, and optimizations)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# View logs
docker-compose logs -f [service-name]

# Scale services (production)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3 --scale frontend=2

# Health check status
docker-compose ps

# Stop and cleanup
docker-compose down -v
```

#### SSL/HTTPS Setup

For production HTTPS:

1. **Place SSL certificates** in `nginx/ssl/`:
   ```bash
   # Self-signed for testing
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
   
   # Or copy your real certificates
   cp your-cert.pem nginx/ssl/cert.pem
   cp your-key.pem nginx/ssl/key.pem
   ```

2. **Uncomment HTTPS server block** in `nginx/nginx.conf`

3. **Update domain name** in nginx configuration

### Access Points

- **Development**: 
  - Frontend: http://localhost:3000
  - Backend API: http://localhost:8000
  - API Docs: http://localhost:8000/docs

- **Production**:
  - Application: http://localhost (or your domain)
  - API: http://localhost/api
  - Health Check: http://localhost/health

## Configuration

### LLM Configuration (Required for AI Features)

#### Azure OpenAI (Recommended)

For enterprise deployments with enhanced security and compliance:

```bash
# Azure OpenAI Configuration
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_KEY="your-azure-openai-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4"  # Your deployment name
export AZURE_OPENAI_API_VERSION="2024-02-01"
export LLM_PROVIDER="azure_openai"
```

#### Alternative Providers (Optional)

```bash
# OpenAI Configuration
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-4-turbo-preview"  # or gpt-4, gpt-3.5-turbo

# Anthropic Configuration  
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"  # or claude-3-opus-20240229

# Provider Selection
export LLM_PROVIDER="openai"  # or "anthropic"
```

#### Azure Authentication Options

1. **API Key** (simplest): Set `AZURE_OPENAI_KEY`
2. **Azure CLI**: Run `az login` before starting the application
3. **Managed Identity**: Available when running on Azure infrastructure

### Monitoring Systems Configuration

Set environment variables to connect to your monitoring systems:

```bash
# Grafana
export GRAFANA_URL="http://your-grafana:3000"
export GRAFANA_TOKEN="your-token"

# Prometheus
export PROMETHEUS_URL="http://your-prometheus:9090"

# Elasticsearch
export ELASTICSEARCH_URL="http://your-elasticsearch:9200"
export ELASTICSEARCH_USERNAME="elastic"
export ELASTICSEARCH_PASSWORD="your-password"

# Nagios
export NAGIOS_URL="http://your-nagios/nagios"
export NAGIOS_USERNAME="nagiosadmin"
export NAGIOS_PASSWORD="your-password"
```

## Sample Queries

### AI-Powered Queries (with LLM configured)

**Intelligent Analysis:**
- "Why are we seeing these errors in the user-service?"
- "What should I investigate first based on the current alerts?"
- "Analyze the correlation between recent deployments and error spikes"
- "Explain the impact of the database connection issues"
- "What are the recommended next steps to resolve this incident?"

**Root Cause Analysis:**
- "What might have caused the response time increase?"
- "How do these errors relate to the recent deployment?"
- "Is this a cascading failure across multiple services?"

### Traditional Queries (always available)

**Data Retrieval:**
- "What changed in the last 2 hours?"
- "Show me error details"
- "Check active alerts"
- "What changed since 15:30?"
- "Analyze recent deployments"

The chatbot automatically chooses between AI-powered analysis and traditional responses based on query complexity and LLM availability.

## Extending

The system is designed to be easily extended:

1. **Add new connectors**: Implement the `MonitoringConnector` base class
2. **Custom correlation**: Modify the `analyze_correlation` method
3. **New data sources**: Add connectors in the `connectors/` directory
4. **UI customization**: Modify React components in `frontend/src/`
5. **LLM customization**: Modify prompts in `llm_service.py` for domain-specific analysis
6. **New LLM providers**: Extend `LLMService` class to support additional AI providers

## LLM Integration Details

### Supported Providers
- **Azure OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo (Enterprise-grade with enhanced security)
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Anthropic**: Claude-3 Opus, Claude-3 Sonnet, Claude-3 Haiku

### AI Features
- **Specialized Prompts**: Incident response expert persona with monitoring context
- **Context Injection**: Automatically includes recent changes, alerts, and correlations
- **Conversation Memory**: Maintains context across multiple interactions
- **Smart Routing**: Automatically chooses AI vs traditional responses
- **Fallback Handling**: Graceful degradation when LLM APIs are unavailable
- **Token Management**: Automatic token counting and conversation truncation

### Cost Optimization
- Intelligent query routing reduces unnecessary LLM calls
- Conversation history truncation keeps token usage reasonable
- Provider selection allows cost vs quality optimization
- Fallback to traditional responses when LLM isn't needed

## Production Deployment

For production use:

1. Replace mock data with real API calls to your monitoring systems
2. Add authentication and authorization
3. Implement rate limiting and caching
4. Add monitoring and logging
5. Use HTTPS and secure headers

## 📊 Architecture & Diagrams

Comprehensive visual documentation is available in the [`docs/`](./docs/) directory:

- **[System Architecture](./docs/architecture-diagrams.md)** - Complete system overview, components, and data flow
- **[Process Flowcharts](./docs/system-flowchart.md)** - Detailed workflows and decision trees  
- **[Documentation Guide](./docs/README.md)** - Quick navigation to all diagrams

### Key Diagrams
- 🏗️ [System Overview](./docs/architecture-diagrams.md#system-overview) - High-level architecture
- 🤖 [LLM Integration Flow](./docs/architecture-diagrams.md#llm-integration-flow) - AI processing workflow
- 🐳 [Docker Architecture](./docs/architecture-diagrams.md#docker-architecture) - Container deployment
- 🔄 [Request Flow](./docs/architecture-diagrams.md#request-flow-architecture) - API interaction sequence
- 📁 [File Structure](./docs/architecture-diagrams.md#file-structure-diagram) - Project organization

All diagrams use Mermaid syntax and render automatically on GitHub! 🎯