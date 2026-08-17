# Flask Groq Email Reply App

A lightweight Flask web app that uses Groq to draft email replies.

## Features
- Flask app factory pattern
- Environment-based configuration
- Groq integration service
- HTML form to submit a prompt
- Simple results page
- Ready for extension with auth, database, and user management

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Add your Groq API key in `.env` as `GROQ_API_KEY`.

5. Run the app:
   ```bash
   flask run
   ```
   or
   ```bash
   python run.py
   ```

## Project structure

```text
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   ├── services/
│   │   └── llm_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── result.html
│   └── static/
│       └── css/
│           └── styles.css
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── .env
```

## Example route

The app includes a home page where a user enters an email, and the backend sends a reply-writing prompt to the configured Groq model.

## Notes
- Keep your API key in `.env` and do not commit it.
- Use a `services` layer to isolate LLM logic from route handlers.
- Add database models and authentication later if required.
