# 🏈 TradeGrade

**Advanced Fantasy Football Analytics Platform**

TradeGrade is a comprehensive fantasy football analytics tool that combines AI-powered analysis, real-time sentiment tracking, and modern web technologies to help fantasy managers make smarter decisions.

![TradeGrade Dashboard](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🤖 AI-Powered Analysis
- **Trade Analysis**: Comprehensive trade evaluations with Groq LLM integration
- **Sit/Start Decisions**: Smart recommendations based on bench comparisons and position scarcity
- **Player Insights**: Detailed analysis of player performance, matchups, and expert consensus

### 🏆 League Management
- **Private Leagues**: Create and join leagues with friends using invite codes
- **Roster Management**: Build and manage your fantasy roster with real NFL player data
- **Team Analysis**: In-depth team evaluation with strengths, weaknesses, and recommendations
- **Community Board**: League-specific discussion boards for trade requests and strategy

### 📊 Advanced Analytics
- **Real-time Sentiment**: Live market sentiment streaming for all players
- **Position Analysis**: Detailed breakdown of roster composition and balance
- **Depth Evaluation**: Bench strength analysis and depth recommendations
- **Trade Recommendations**: AI-generated trade suggestions and evaluations

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Dark Mode**: Toggle between light and dark themes
- **Real-time Updates**: AJAX-powered roster management without page refreshes
- **Player Headshots**: Real NFL player images from Sleeper API

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/TradeGrade.git
   cd TradeGrade
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   
   # On macOS/Linux:
   source .venv/bin/activate
   
   # On Windows:
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Configuration section)
   ```

5. **Initialize the database:**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application:**
   ```bash
   python run.py
   ```

7. **Access the app:**
   - Open [http://localhost:5050](http://localhost:5050)
   - Register an account and create/join a league

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required: Groq API Key for AI analysis
GROQ_API_KEY=your_groq_api_key_here

# Optional: Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=1

# Optional: Database Configuration
DATABASE_URL=sqlite:///app.db

# Optional: Server Configuration
PORT=5050
```

### API Keys Setup

#### Groq API (Required)
1. Visit [Groq Console](https://console.groq.com/)
2. Create an account and generate an API key
3. Add the key to your `.env` file as `GROQ_API_KEY`

#### Optional APIs
- **OpenAI API**: Alternative LLM provider
- **News API**: Enhanced news sentiment analysis
- **Twitter API**: Social sentiment tracking

## 📁 Project Structure

```
TradeGrade/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── extensions.py            # Flask extensions setup
│   ├── models.py               # Database models
│   ├── seed.py                 # Database seeding
│   ├── auth/                   # Authentication blueprint
│   │   └── routes.py
│   ├── league/                 # League management blueprint
│   │   └── routes.py
│   ├── roster/                 # Roster management blueprint
│   │   └── routes.py
│   ├── trades/                 # Trade analysis blueprint
│   │   └── routes.py
│   ├── board/                  # Community board blueprint
│   │   └── routes.py
│   ├── api/                    # API endpoints blueprint
│   │   └── routes.py
│   ├── services/               # Business logic
│   │   ├── analysis.py         # AI analysis services
│   │   ├── players.py          # Player data services
│   │   └── sentiment.py        # Sentiment analysis
│   └── templates/              # Jinja2 templates
│       ├── base.html           # Base template
│       ├── index.html          # Homepage
│       ├── auth/               # Authentication templates
│       ├── league/             # League templates
│       ├── roster/             # Roster templates
│       ├── trades/             # Trade templates
│       └── board/              # Board templates
├── config.py                   # Configuration classes
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🗄️ Database Schema

### Core Models

- **User**: User accounts with authentication
- **League**: Fantasy leagues with invite codes
- **Membership**: User-league relationships
- **Player**: NFL player data from Sleeper API
- **RosterEntry**: User roster assignments
- **Trade**: Trade analysis history
- **BoardPost**: Community board posts

### Key Relationships
- Users can belong to multiple leagues
- Each league has multiple members
- Users can have multiple roster entries per league
- Trades are linked to specific leagues

## 🔧 Development

### Tech Stack
- **Backend**: Flask 3.0+, SQLAlchemy, Flask-Migrate
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Real-time**: Flask-SocketIO
- **AI/ML**: Groq API, OpenAI API
- **Database**: SQLite (development), PostgreSQL (production)
- **Styling**: Pico.css framework with custom CSS

### Development Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up pre-commit hooks (optional):**
   ```bash
   pre-commit install
   ```

3. **Run in development mode:**
   ```bash
   export FLASK_ENV=development
   export FLASK_DEBUG=1
   python run.py
   ```

### Code Organization

- **Blueprints**: Feature-based organization (auth, league, roster, trades, board)
- **Services**: Business logic separated from routes
- **Models**: SQLAlchemy models with relationships
- **Templates**: Jinja2 templates with inheritance
- **Static Files**: CSS, JavaScript, and images

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_analysis.py
```

### Test Structure
```
tests/
├── conftest.py              # Test configuration
├── test_auth.py            # Authentication tests
├── test_league.py          # League management tests
├── test_roster.py          # Roster management tests
├── test_trades.py          # Trade analysis tests
└── test_analysis.py        # Analysis service tests
```

## 🚀 Deployment

### Production Deployment

1. **Set production environment variables:**
   ```env
   FLASK_ENV=production
   DATABASE_URL=postgresql://user:pass@host:port/dbname
   GROQ_API_KEY=your_production_key
   ```

2. **Install production dependencies:**
   ```bash
   pip install gunicorn psycopg2-binary
   ```

3. **Run database migrations:**
   ```bash
   flask db upgrade
   ```

4. **Start the application:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]
```

## 📊 API Documentation

### Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### League Endpoints
- `GET /league/dashboard` - User dashboard
- `POST /league/create` - Create new league
- `POST /league/join` - Join existing league
- `GET /league/<id>/members` - View league members
- `GET /league/<id>/team/<user_id>` - Team analysis

### Roster Endpoints
- `GET /roster/<league_id>` - View roster
- `POST /roster/<league_id>/add` - Add player
- `POST /roster/<league_id>/toggle/<entry_id>` - Toggle starter/bench
- `POST /roster/<league_id>/remove/<entry_id>` - Remove player
- `GET /roster/<league_id>/sitstart/<player_id>` - Sit/start analysis

### Trade Endpoints
- `GET /trades/<league_id>/analyze` - Trade analysis form
- `POST /trades/<league_id>/analyze` - Submit trade for analysis
- `GET /trades/<league_id>/result/<trade_id>` - View trade results

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes and add tests**
4. **Commit your changes:**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push to the branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Sleeper API** for comprehensive NFL player data
- **Groq** for fast AI inference capabilities
- **Pico.css** for the beautiful CSS framework
- **Flask** community for the excellent web framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/TradeGrade/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/TradeGrade/discussions)
- **Email**: support@tradegrade.com

## 🔮 Roadmap

### Upcoming Features
- [ ] **Mobile App**: React Native mobile application
- [ ] **Advanced Analytics**: More sophisticated player projections
- [ ] **League Scoring**: Custom scoring systems
- [ ] **Draft Assistant**: AI-powered draft recommendations
- [ ] **Waiver Wire**: Automated waiver wire suggestions
- [ ] **League History**: Historical performance tracking
- [ ] **Social Features**: Enhanced community features
- [ ] **API Access**: Public API for third-party integrations

### Version History
- **v1.0.0** - Initial release with core features
- **v1.1.0** - Added team analysis and improved UI
- **v1.2.0** - Enhanced trade analysis with better AI integration
- **v1.3.0** - Real-time sentiment analysis and community features

---

**Made with ❤️ for fantasy football enthusiasts**