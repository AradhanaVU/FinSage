# FinSage - AI Finance Companion

An intelligent financial assistant platform with AI-powered insights, forecasting, goal planning, risk analysis, and personalized recommendations.

## Features

### Core AI Features
- **Automatic Transaction Categorization**: Uses NLP to automatically categorize transactions
- **Spending Pattern Detection**: Identifies patterns and anomalies in spending behavior
- **Spending Forecasts**: Time-series prediction for future spending trends
- **Goal-Based Planning**: Scenario simulations to help reach financial goals faster
- **Monte Carlo Simulations**: Investment planning with probabilistic outcomes
- **Opportunity Cost Analysis**: Calculates potential gains from investing vs spending
- **Personalized Alerts**: Smart alerts for unusual spending, cash shortages, and milestones
- **AI Financial Coach**: LLM-powered chat interface for financial advice
- **Receipt Intelligence**: OCR-based receipt processing and subscription detection

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **spaCy**: NLP for transaction categorization
- **OpenAI API / GEMINI API**: LLM for financial coaching chat
- **NumPy/Pandas**: Data analysis and forecasting
- **Monte Carlo**: Investment simulations

### Frontend
- **React**: UI framework
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Vite**: Build tool

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

5. Copy env example and edit secrets:
```bash
cp .env.example .env
```

Required values:
```env
DATABASE_URL=sqlite:///./finance_app.db
SECRET_KEY=your-long-random-secret
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ENV=development
GEMINI_API_KEY=   # optional
OPENAI_API_KEY=   # optional
```

6. Run the backend server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy env example (points API at local backend):
```bash
cp .env.example .env
```

4. Run the development server:
```bash
npm run dev
```

Open `http://localhost:3000`, register an account, then sign in. Each user only sees their own data.

## Docker Compose (multi-user production-like)

From the repo root:

```bash
# Optional: export SECRET_KEY and GEMINI_API_KEY
docker compose up --build
```

- App: `http://localhost:3000` (nginx proxies `/api` to the API)
- API direct: `http://localhost:8000`
- Postgres: internal `db:5432`

On startup the API runs `alembic upgrade head`. Set a strong `SECRET_KEY` before any real deploy.

## API Documentation

In development, visit `http://localhost:8000/docs`. Docs are disabled when `ENV=production`.

## Auth

- `POST /api/auth/register` — create account
- `POST /api/auth/login` — OAuth2 form (Swagger)
- `POST /api/auth/login/json` — JSON login for the SPA
- `GET /api/auth/me` — current user (Bearer token)

All finance endpoints require `Authorization: Bearer <token>`.

## Project Structure

```
.
├── docker-compose.yml
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── core/            # settings + JWT/password helpers
│   │   ├── ai/
│   │   ├── routers/         # includes auth.py
│   │   ├── deps.py          # get_current_user
│   │   └── main.py
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── pages/Login.jsx, Register.jsx
│       └── services/auth.jsx, api.js
└── README.md
```

## Usage Examples

### Adding Transactions
After login, transactions are categorized with AI. You can override categories manually; labels stay private to your account.

### Setting Goals
Create goals and run spending-reduction scenarios against your own surplus.

### AI Chat
Ask questions like:
- "How can I save $500 this month?"
- "Am I on track for retirement?"
- "What's my biggest spending category?"

## License

MIT License

