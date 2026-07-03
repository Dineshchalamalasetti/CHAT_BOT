# AI Chat Assistant

A full-stack chatbot application powered by OpenAI, designed as an intelligent assistant for coding, data science, SQL, interviews, debugging, and technical learning.

## Features

- Modern chat UI with markdown and code block rendering
- Conversation history with context across messages
- System prompt tuned for step-by-step explanations, interview prep, and tutoring
- REST API built with FastAPI
- Configurable model and history length via environment variables

## Project Structure

```
Chat_Bot/
├── app/
│   ├── main.py          # FastAPI application and routes
│   ├── chat_service.py  # OpenAI integration
│   ├── prompts.py       # Assistant behavior and capabilities
│   └── config.py        # Environment configuration
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
└── .env.example
```

## AI Provider Options

| Provider | Cost | API Key | Best for |
|----------|------|---------|----------|
| **Gemini** (default) | Free tier | Yes | Google's free API |
| **Groq** | Free tier | Yes | Fast cloud responses |
| **OpenAI** | Paid | Yes | Best quality, requires billing |

### Google Gemini (default)

1. Get a free key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. In `.env`, set:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_key_here
   ```

### Groq (free cloud API)

1. Get a free key at [https://console.groq.com/keys](https://console.groq.com/keys)
2. In `.env`, set:
   ```env
   AI_PROVIDER=groq
   GROQ_API_KEY=your_groq_key_here
   ```

## Setup

1. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:

   ```bash
   copy .env.example .env
   ```

   Edit `.env` and choose a provider (see options above).

4. **Run the server**:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open the app**:

   Visit [http://localhost:8000](http://localhost:8000)

## API Endpoints

| Method | Endpoint      | Description                    |
|--------|---------------|--------------------------------|
| GET    | `/`           | Chat web interface             |
| GET    | `/api/health` | Health check                   |
| GET    | `/api/info`   | Assistant capabilities & status |
| POST   | `/api/chat`   | Send messages and get a reply  |

### Example chat request

```json
{
  "messages": [
    { "role": "user", "content": "Explain quicksort with Python code." }
  ]
}
```

## Environment Variables

| Variable               | Default              | Description                          |
|------------------------|----------------------|--------------------------------------|
| `AI_PROVIDER`          | `gemini`             | `gemini`, `groq`, or `openai`        |
| `GEMINI_API_KEY`       | —                    | Google Gemini API key (free)         |
| `GROQ_API_KEY`         | —                    | Groq API key (free)                  |
| `OPENAI_API_KEY`       | —                    | OpenAI API key (paid)                |
| `MAX_HISTORY_MESSAGES` | `20`                 | Max conversation turns sent to model   |
| `CORS_ORIGINS`         | localhost origins    | Allowed CORS origins                 |

## License

MIT
