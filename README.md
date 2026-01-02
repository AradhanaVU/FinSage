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
- **OpenAI API**: LLM for financial coaching chat
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

5. Create a `.env` file in the backend directory:
```env
DATABASE_URL=sqlite:///./finance_app.db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional: Chat features work with fallback if not provided
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Note**: The OpenAI API key is optional. The chat feature will work with a fallback response system if no API key is provided. However, for the best experience with the AI Financial Coach, provide your OpenAI API key.

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

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── ai/              # AI modules
│   │   │   ├── categorizer.py
│   │   │   ├── pattern_detector.py
│   │   │   ├── forecaster.py
│   │   │   ├── llm_chat.py
│   │   │   ├── simulations.py
│   │   │   └── alert_generator.py
│   │   ├── routers/         # API endpoints
│   │   │   ├── transactions.py
│   │   │   ├── goals.py
│   │   │   ├── ai_insights.py
│   │   │   ├── chat.py
│   │   │   ├── alerts.py
│   │   │   ├── simulations.py
│   │   │   └── receipts.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Usage Examples

### Adding Transactions
Transactions are automatically categorized using AI. Simply add a transaction with a description, and the system will:
- Categorize it based on merchant/description
- Assign a confidence score
- Detect patterns and anomalies

### Setting Goals
Create financial goals and use scenario simulations to see how spending reductions can help you reach goals faster.

### AI Chat
Ask questions like:
- "How can I save $500 this month?"
- "Am I on track for retirement?"
- "What's my biggest spending category?"

### Insights
View:
- Spending analysis by category
- 30-day spending forecasts
- Detected anomalies
- Spending patterns

## Future Enhancements

- User authentication and multi-user support
- Bank account integration
- Advanced receipt OCR with better parsing
- More sophisticated forecasting models
- Investment portfolio tracking
- Budget templates and recommendations
- Export reports (PDF, CSV)

## License

MIT License

