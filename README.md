# TradeGrade

Advanced fantasy football analytics platform with AI-powered trade analysis, sit/start decisions, and real-time sentiment tracking.

## Features

- **AI-Powered Trade Analysis**: Comprehensive trade evaluations with Groq LLM integration
- **Smart Sit/Start Decisions**: Bench comparison analysis with position scarcity detection
- **Real-time Sentiment**: Live market sentiment streaming for all players
- **League Management**: Private leagues with roster management and community boards
- **Modern UI**: Responsive design with dark mode support

## Setup

1. **Clone and install dependencies:**
   ```bash
   git clone <repository>
   cd TradeGrade
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Initialize database:**
   ```bash
   flask db upgrade
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

5. **Access the app:**
   - Open http://localhost:5050
   - Register an account and create/join a league

## Environment Variables

Required:
- `GROQ_API_KEY`: Your Groq API key for LLM analysis

Optional:
- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `DATABASE_URL`: Database connection string
- `PORT`: Server port (default: 5050)

See `.env.example` for all available configuration options.

## API Keys

- **Groq API**: Required for AI-powered trade and sit/start analysis
- **OpenAI API**: Alternative LLM provider (optional)
- **News API**: For enhanced news sentiment (optional)
- **Twitter API**: For social sentiment analysis (optional)

## Development

The app uses Flask with SQLAlchemy, Socket.IO for real-time features, and Groq for AI analysis. The codebase is organized with blueprints for different features (auth, league, roster, trades, board).