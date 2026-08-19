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
```
TUAS-Grp3-APTRA/
├── app/                           # Application source code
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   ├── services/
│   │   └── llm_service.py
│   ├── static/
│   └── templates/
│
├── tests/                         # Test source code
│   ├── test_llm_service.py       # LLM service unit tests
│   └── test_routes.py            # Route, integration, and boundary tests
│
├── run.py                         # Flask application entry point
├── run_tests.py                   # Test runner with reporting
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
├── .env.example                   # Environment template
└── README.md                       # Main project README
```
## QA/QC Testing

See [DATA_FLOW_ARCHITECTURE.md](DATA_FLOW_ARCHITECTURE.md) for the system data-flow and request-sequence diagrams.

### Running Tests

From Git Bash on Windows, run the full QA/QC suite with the formatted test report:

```bash
# Run all tests using the project virtual environment
./.venv/Scripts/python.exe run_tests.py

# Run a specific test category
./.venv/Scripts/python.exe -m unittest tests.test_llm_service -v
./.venv/Scripts/python.exe -m unittest tests.test_routes -v
./.venv/Scripts/python.exe -m unittest tests.test_routes.IndexRouteBoundaryTest -v
```

The custom runner groups tests by category, marks every test as `PASS`, `FAIL`,
`ERROR`, or `SKIP`, displays execution times, and prints failure details in a
separate section. It returns exit code `0` when all tests pass and `1` when the
suite contains a failure or error, making it suitable for both local QA and CI.

Example successful summary:

```text
SUMMARY
========================================================================
  Total: 54  |  Passed: 54  |  Failed: 0  |  Errors: 0  |  Skipped: 0

RESULT: ALL TESTS PASSED
```

### Test Coverage

**54 automated tests** covering:

- 26 LLM service prompt-building, privacy-masking, and response-generation tests
- Route integration and complete workflow tests
- 6 boundary tests for the 10,000/5,000-character limits
- Required-field, whitelist, and case-normalization validation
- Configuration, generation, and network error handling
- HTML escaping and UI control hooks
- AI reasoning suppression and generated-output cleanup
- Private-information masking before AI processing and before webpage output
- Recovery of the completed email draft when a reasoning model exhausts its
  token budget before emitting its labelled final output

### Test Categories

| Category | Tests | Coverage |
|----------|-------|----------|
| LLM Service | 26 | Prompt construction, privacy masking, Groq configuration, and clean reply output |
| Integration | 4 | Valid form submissions and service interaction |
| Input Validation | 8 | Tone/length/required fields |
| Boundary Tests | 6 | Limits at ±1 character |
| Error Handling | 4 | Safe configuration, API, and network error messages |
| Features | 4 | End-to-end workflow, output escaping, special characters, and input preservation |
| UI Hooks | 2 | Speech controls and preservation of selected options |

### Key Test Scenarios

- **Prompt length:** At 10,000 chars (accept) vs 10,001 chars (reject)
- **Context length:** At 5,000 chars (accept) vs 5,001 chars (reject)
- **Tone validation:** All 5 tones accepted (professional, casual, formal, friendly, diplomatic)
- **Length validation:** All 3 lengths accepted (short, medium, long)
- **Error handling:** Configuration/API/network errors show generic messages (no details leaked)
- **Security:** API keys never exposed, form data preserved on error
- **Output isolation:** The webpage receives only the generated email response, not AI reasoning, checklists, labels, or automated test output
- **Reasoning models:** Qwen reasoning is disabled for email generation and known reasoning wrappers are removed defensively
- **Privacy masking:** Credit-card, passport, NRIC/FIN, phone, and payment-card identifiers are replaced with editable placeholders before Groq processing and final display; email addresses remain unchanged

---

## Example route

The app includes a home page where a user enters an email, and the backend sends a reply-writing prompt to the configured Groq model.
