# Nourishly

A modern nutrition and wellness API built with Django and Django Ninja, designed to help users make healthier food choices and track their nutritional intake.

## 🚀 Features

- **Subscription Management**: Comprehensive subscription plans with payment processing
- **User Profiles**: Personalized nutrition goals and dietary preferences with BMI calculations
- **Recipe Services**: Recipe scraping, analysis, and classification services (backend services only)
  - **Recipe Scraping**: Automated recipe extraction from Budget Bytes and other providers
  - **Macro Analysis**: Nutritional analysis using API Ninja and USDA databases
  - **Cuisine Classification**: AI-powered cuisine classification using Hugging Face models
  - **Ingredient Parsing**: Structured ingredient parsing with quantities and units
- **AI Integration**: Hugging Face services for embeddings and text classification
- **Standard Logging**: Python's standard logging module configured through Django settings
- **RESTful API**: Modern API built with Django Ninja for type safety and performance
- **Database Architecture**: Clean architecture with selectors pattern for database queries
- **Development Tools**: Comprehensive development setup with linting, testing, and debugging tools

## 🏗️ Architecture

```
nourishly/
├── api/                 # Main API router (Django Ninja)
├── core/                # Shared utilities, base models, logging system
│   └── services/        # Hugging Face AI services
├── subscriptions/       # Subscription and payment management
├── users/               # User auth and preference profiles
├── recipes/             # Recipe and ingredient management
│   └── services/        # Recipe scraping, macro analysis, cuisine classification
├── planner/             # Meal planning engine (planned)
├── classify/            # Cuisine classification (planned)
├── nourishly/           # Project settings (separated by environment)
├── .cursor/             # AI development rules and patterns
├── docs/                # Project documentation
└── logs/                # Application logs
```

## 🔧 Implemented Services

### Recipe Services
- **Recipe Scraping**: Automated extraction from Budget Bytes and other recipe providers
- **Macro Analysis**: Nutritional analysis using API Ninja and USDA databases
- **Cuisine Classification**: AI-powered cuisine classification using Hugging Face models
- **Ingredient Parsing**: Structured ingredient parsing with quantities and units

See [Recipes App Documentation](./docs/recipes.md) for detailed information about models, services, and usage examples.

### AI Services
- **Hugging Face Integration**: Embeddings generation and text classification
- **Cuisine Classification**: Multi-language cuisine detection with confidence scoring
- **Recipe Analysis**: Natural language processing for recipe understanding

### External API Integrations
- **API Ninja**: Nutrition data and macro analysis
- **USDA Database**: Comprehensive nutritional information
- **Hugging Face**: AI models for classification and embeddings

## 🏛️ Architecture Patterns

### Selectors Pattern
All database queries go through selector classes in `app/selectors.py`:
```python
# ✅ Correct - Use selectors
data = UserSelector.get_by_id(user_id)

# ❌ Incorrect - Direct model queries in services/API
data = User.objects.get(id=user_id)
```

### Service Layer
Business logic goes in service classes:
```python
# ✅ Correct - Use services for business logic
result = UserService.create_user(data)

# ❌ Incorrect - Business logic in API endpoints
user = User.objects.create(**data)
```

### Logging System
Standard Python logging with Django configuration:
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Operation completed - User ID: {user.id}")
logger.error(f"Operation failed - Error: {str(e)}")
```

The project uses a custom logging wrapper (`core.logger`) for consistent logging across the application. See [Logging Documentation](./docs/logging.md) for more details.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.11+ (recommended: 3.13)
- pyenv (for Python version management)
- PostgreSQL (for database)
- Git

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nourishly.git
   cd nourishly
   ```

2. **Set up Python environment**
   ```bash
   pyenv install 3.13.5
   pyenv virtualenv 3.13.5 nourishly-venv
   pyenv activate nourishly-venv
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   **Required Environment Variables:**
   ```bash
   # Django Configuration
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DJANGO_ENV=development
   
   # Database Configuration
   DATABASE_URL=postgresql://user:password@localhost:5432/nourishly_dev
   
   # API Keys for External Services
   HUGGINGFACE_API_TOKEN=your-huggingface-token
   API_NINJA_KEY=your-api-ninja-key
   USDA_API_KEY=your-usda-api-key
   
   # Logging is configured in Django settings (nourishly/settings/base.py)
   # No environment variables needed for logging
   ```

5. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb nourishly_dev
   ```

6. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main app: `http://127.0.0.1:8000`
   - Admin interface: `http://127.0.0.1:8000/admin`
   - API documentation: `http://127.0.0.1:8000/api/docs`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov

# Run tests in watch mode
pytest-watch

# Run specific app tests
pytest subscriptions/
```

## 📦 Building for Production

```bash
# Install production dependencies
pip install -r requirements/production.txt

# Set production environment
export DJANGO_ENV=production

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Start production server
gunicorn nourishly.wsgi:application
```

## 🔧 Development

```bash
# Code formatting
black .
isort .

# Linting
flake8

# Type checking
mypy .

# Run development server
python manage.py runserver
```

## 📚 API Documentation

The API is built with Django Ninja and provides automatic documentation:

- **Development**: Visit `http://127.0.0.1:8000/api/docs` for interactive API documentation (when API is registered in URL configuration)
- **Available Endpoints**:
  - `/api/subscriptions/plans` - Available subscription plans
  - `/api/subscriptions/plans/{plan_id}` - Get specific subscription plan
  - `/api/subscriptions/subscriptions` - List user subscriptions
  - `/api/subscriptions/subscriptions/current` - Get current active subscription
  - `/api/subscriptions/subscriptions` (POST) - Create new subscription
  - `/api/subscriptions/subscriptions/{subscription_id}/cancel` - Cancel subscription
  - `/api/subscriptions/payments` - Payment history
  - `/api/subscriptions/status` - User subscription status
  - `/api/subscriptions/features` - Available subscription features
  - `/api/health` - Health check endpoint

## 🤝 Contributing

We welcome contributions from the community! Please read our contributing guidelines before submitting a pull request.

### Pull Request Templates

We have several pull request templates to help you create better PRs:

- **[Feature PR](.github/PULL_REQUEST_TEMPLATE/feature_request.md)** - For new features and enhancements
- **[Bug Fix PR](.github/PULL_REQUEST_TEMPLATE/bug_report.md)** - For bug fixes and hotfixes
- **[Documentation PR](.github/PULL_REQUEST_TEMPLATE/documentation.md)** - For documentation updates

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the established patterns
4. Add tests for your changes
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow the existing code style and conventions
- Use the selectors pattern for database queries
- Use the service layer for business logic
- Include proper logging for all operations
- Write meaningful commit messages
- Add comments for complex logic
- Ensure all tests pass before submitting

## 📖 Documentation

- [Logging System](./docs/logging.md) - Comprehensive logging documentation
- [Recipes App](./docs/recipes.md) - Complete recipes app documentation including models, services, and usage examples
- [Cursor Rules](./.cursor/README.md) - AI development patterns and rules
- [API Development Rules](./.cursor/rules/api/RULE.md) - Django Ninja API patterns
- [Model Development Rules](./.cursor/rules/models/RULE.md) - Django model patterns

## 🏗️ Project Structure

### Core Apps
- **`core/`** - Shared utilities, base models, logging system, middleware
  - **`services/huggingface/`** - Hugging Face AI services for embeddings and classification
- **`api/`** - Main API router and health check endpoints
- **`users/`** - Custom user model with nutrition-specific fields
- **`subscriptions/`** - Complete subscription and payment management with API endpoints
- **`recipes/`** - Recipe and ingredient management with comprehensive services (backend services only, no API endpoints)
  - **`services/recipe_providers/`** - Recipe scraping from Budget Bytes and other providers
  - **`services/macro_analysis/`** - Nutritional analysis using API Ninja and USDA
  - **`services/cuisine_classifiers/`** - AI-powered cuisine classification

### Planned Apps
- **`planner/`** - Meal planning engine
- **`classify/`** - Additional classification services

### Key Files
- **`.cursor/rules/`** - AI development patterns and conventions
- **`requirements/`** - Environment-specific dependency management
- **`nourishly/settings/`** - Environment-specific Django settings
- **`logs/`** - Application log files

## 🐛 Bug Reports

If you find a bug, please create an issue with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots (if applicable)
- Environment information

## 💡 Feature Requests

We love hearing about new ideas! Please create an issue with:
- A clear description of the feature
- Use cases and benefits
- Mockups or examples (if applicable)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all our contributors
- Built with modern web technologies
- Inspired by the need for better nutrition tracking tools

## 📞 Support

If you need help or have questions:
- Create an issue on GitHub
- Check our [documentation](./docs/)
- Join our community discussions

---

Made with ❤️ by the Nourishly team