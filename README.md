# AI-Powered E-Commerce Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-LLM-white?style=for-the-badge)](https://ollama.ai/)

An intelligent e-commerce backend that blends traditional REST API endpoints with an **Autonomous AI Agent**. This project demonstrates how a Local LLM (via Ollama) can perform **Tool Calling** to manage products, check order statuses, and process cancellations through natural language.

---

## Features

- **Autonomous Agent:** Uses a "Reasoning" loop to decide which backend tool to trigger.
- **Hybrid Conversation:** Handles **Tool Actions** (JSON-based) and **Small Talk** (plain text) for a natural user experience.
- **Robust Extraction:** Features Regex-based fallback to capture Order IDs if the LLM forgets them.
- **FastAPI Integration:** Fully documented API routes with automatic Swagger UI.
- **Tool-Based Architecture:** Modular design where AI logic is separated from business logic.

---

## System Architecture

The workflow follows a **Request -> Reason -> Act** pattern:

1. **User Input:** "Can you cancel my order 1001?"
2. **LLM Reasoning:** The Agent identifies the `cancel_order` intent.
3. **Structured Output:** The LLM generates a JSON tool call: `{"tool": "cancel_order", "args": {"order_id": "1001"}}`.
4. **Tool Execution:** The backend function updates the "In-Memory" database.
5. **Human-Friendly Response:** The system returns the success message to the user.

---

## 📂 Project Structure

```bash
ai-agent-ecommerce-backend/
├── agent/
│   └── agent.py          # The 'Brain': LLM logic, JSON parsing, and retries
├── backend/
│   └── server.py         # The 'Doorway': FastAPI app and Web endpoints
├── models/
│   ├── order.py          # Pydantic data models for Orders
│   └── product.py        # Pydantic data models for Products
├── tools/
│   └── order_tools.py    # The 'Hands': Logic for interacting with the data
├── tests/
│   └── test_api.py       # API testing scripts
├── requirements.txt      # Dependencies (FastAPI, Requests, etc.)
└── README.md             # Documentation