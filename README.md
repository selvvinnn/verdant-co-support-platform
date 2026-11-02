# Verdant & Co. — AI-Powered Customer Support Platform

An AI-assisted customer support platform built with FastAPI, PostgreSQL, React and OpenAI. The application enables customers to submit messages, generates knowledge-base-grounded AI reply suggestions, and allows authorized support agents to review, edit and approve responses.

**AI-generated replies are suggestions only. They are never sent automatically.**

## 1. Features

### Customer Interface
- Submit customer support messages.
- Automatically create or continue an open conversation.
- View conversation history.
- Access conversations through customer-specific authentication tokens.
- View approved agent responses only.

### Agent Interface
- Agent login and invite-code-based registration.
- Authenticated conversation management.
- Search and view customer conversations.
- Review AI-generated reply suggestions.
- Edit and save AI drafts.
- Approve responses and add them to the conversation.
- View AI generation failures.

### AI Integration
- OpenAI-powered reply generation.
- Responses grounded in the Verdant & Co. knowledge base.
- Unknown policy questions are not answered with invented information.
- Medical questions are handled without providing unsupported medical advice.
- Failed AI generation does not prevent customer messages from being saved.

### Webhook Integration
- Receive incoming customer messages through an HTTP webhook.
- Verify requests using HMAC-SHA256 signatures.
- Detect duplicate webhook events.
- Persist incoming events and messages in PostgreSQL.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| UI icons | Lucide React |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| AI | OpenAI API |
| Authentication | JWT |
| API documentation | Swagger / OpenAPI |

## 3. Project Structure

```text
Datastraw/
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AgentView.jsx
│   │   │   └── CustomerView.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── webhook_backend/
│   └── app/
│       ├── ai/
│       │   ├── draft_service.py
│       │   ├── llm_service.py
│       │   └── prompt.py
│       ├── main.py
│       ├── auth.py
│       ├── agent.py
│       ├── customer.py
│       ├── customer_service.py
│       ├── webhooks.py
│       ├── models.py
│       ├── schemas.py
│       └── database.py
│
├── postman/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 4. Prerequisites

Install the following before running the project:

- Python 3.11
- Node.js and npm
- PostgreSQL
- OpenAI API key
- Git

## 5. Backend Setup

### Clone the repository

```bash
git clone (https://github.com/selvvinnn/verdant-co-support-platform.git)
cd Datastraw
```

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Configure the required database credentials, webhook secret, JWT secret, OpenAI API key, model and agent invitation code in `.env`.

### Configure PostgreSQL

Create a PostgreSQL database and update `DATABASE_URL` in `.env` with the appropriate connection string.

### Start the backend

```powershell
cd webhook_backend
uvicorn app.main:app --reload
```

Backend URL:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

## 6. Frontend Setup

Open a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

http://localhost:5173

The Vite development server proxies API requests to the local FastAPI backend.

## 7. Environment Variables

The following environment variables are required:

| Variable | Description |
|---|---|
| DATABASE_URL | PostgreSQL database connection string |
| WEBHOOK_SECRET | Secret used for webhook HMAC verification |
| JWT_SECRET_KEY | Secret used to sign authentication tokens |
| OPENAI_API_KEY | OpenAI API key |
| OPENAI_MODEL | OpenAI model used for draft generation |
| AGENT_INVITE_CODE | Invitation code required for agent registration |

Never commit the actual `.env` file or expose API keys, passwords, JWT secrets or invitation codes.

## 8. Core API Endpoints

### Customer

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/customer/messages` | Submit a customer message |
| GET | `/api/customer/conversations/{conversation_id}` | Retrieve an authenticated customer conversation |

### Agent Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register an agent using an invitation code |
| POST | `/api/auth/login` | Authenticate an agent |
| GET | `/api/agent/me` | Retrieve authenticated agent profile |

### Agent Conversations

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/agent/conversations` | Retrieve conversations |
| GET | `/api/agent/conversations/{conversation_id}` | Retrieve conversation details |
| PATCH | `/api/agent/drafts/{draft_id}` | Update an AI draft |
| POST | `/api/agent/drafts/{draft_id}/approve` | Approve a draft |

### Webhook

| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhooks/messages` | Receive incoming webhook events |

## 9. Webhook Security

Incoming webhook requests are verified using HMAC-SHA256.

The request must include:

```text
X-Signature: sha256=<hex_digest>
```

The digest is calculated using the configured webhook secret and the raw request body.

Invalid signatures are rejected. Duplicate event IDs are detected to prevent repeated processing.

## 10. AI Reply Workflow

1. A customer submits a message.
2. The backend saves the message and associates it with a conversation.
3. The AI service generates a suggested reply using the company knowledge base.
4. The generated draft is stored against the corresponding customer message.
5. An authenticated agent reviews and edits the draft.
6. The agent approves the response.
7. The approved response is stored as an agent message.
8. The customer can view the approved response.

AI drafts are never automatically sent to customers.

If AI generation fails, the customer message remains saved and the failure is recorded for agent review.

## 11. Testing

The application was tested for:

- Successful customer message submission.
- Webhook signature verification.
- Duplicate webhook event detection.
- Agent registration and authentication.
- Invalid invitation codes.
- Duplicate agent registration.
- Invalid and expired JWT authentication.
- Empty customer message validation.
- AI generation failure handling.
- Unknown policy and medical-question handling.
- Draft editing and approval.
- Customer access restrictions.

## 12. Security Considerations

- Secrets are stored in environment variables.
- Webhook requests are authenticated using HMAC-SHA256.
- Agent endpoints require JWT authentication.
- Customer conversation access uses customer-specific tokens.
- AI drafts are hidden from customer-facing conversation responses.
- Agent registration requires an invitation code.
- Duplicate webhook events are handled to prevent repeated processing.

## 13. Current Scope

This project implements an AI-assisted customer support workflow. Approved responses are saved in the conversation; integration with an external messaging provider for actually delivering WhatsApp or other messages is outside the current implementation.

---

**Developed as a take-home software engineering assessment.**
