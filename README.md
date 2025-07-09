# Nourishly

A modern nutrition and wellness API built with Django and Django Ninja, designed to help users make healthier food choices and track their nutritional intake.

## 🚀 Features

- **Nutrition Tracking**: Log and track your daily food intake
- **Meal Planning**: Plan your meals ahead of time with AI-powered suggestions
- **Recipe Database**: Access to a vast collection of healthy recipes with Edamam integration
- **Cuisine Classification**: AI-powered cuisine classification using Hugging Face
- **User Profiles**: Personalized nutrition goals and dietary preferences
- **RESTful API**: Modern API built with Django Ninja for type safety and performance

## 🏗️ Architecture

```
nourishly/
├── api/                 # Main API router (Django Ninja)
├── recipes/             # Recipe and ingredient management
├── planner/             # Meal planning engine
├── users/               # User auth and preference profiles
├── classify/            # Cuisine classification with Hugging Face
├── core/                # Shared utilities and base models
└── nourishly/           # Project settings (separated by environment)
```

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.11+ (recommended: 3.13)
- pyenv (for Python version management)
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

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Open your browser**
   Navigate to `http://127.0.0.1:8000`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov

# Run tests in watch mode
pytest-watch

# Run specific app tests
pytest recipes/
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

## 🤝 Contributing

We welcome contributions from the community! Please read our contributing guidelines before submitting a pull request.

### Pull Request Templates

We have several pull request templates to help you create better PRs:

- **[Feature PR](.github/pull_request_templates/feature.md)** - For new features and enhancements
- **[Bug Fix PR](.github/pull_request_templates/bugfix.md)** - For bug fixes and hotfixes
- **[Documentation PR](.github/pull_request_templates/documentation.md)** - For documentation updates
- **[Default PR](.github/pull_request_templates/default.md)** - For any other changes

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow the existing code style and conventions
- Write meaningful commit messages
- Add comments for complex logic
- Ensure all tests pass before submitting

## 📚 Documentation

- [API Documentation](./docs/api.md) - Django Ninja API endpoints
- [Developer Guide](./docs/developer-guide.md) - Setup and development workflow
- [Architecture Guide](./docs/architecture.md) - Project structure and design decisions
- [Contributing Guidelines](./docs/contributing.md)

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
- Check our [FAQ](./docs/faq.md)
- Join our community discussions

---

Made with ❤️ by the Nourishly team