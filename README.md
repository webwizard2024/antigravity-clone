# Anti-Gravity IDE

## Why This Project?

Modern development environments are powerful but often heavy and difficult to customize for experimentation. This project explores the idea of a lightweight, browser-based coding environment that combines code editing, execution, and AI-assisted development in a single interface.

Anti-Gravity IDE is designed as a learning and experimentation tool rather than a full replacement for traditional desktop IDEs.

> The goal is to reduce friction between writing code, running it, and improving it with AI assistance.

---

## Context

This application is built using Streamlit and provides a VS Code–like experience inside the browser. It supports file management, code execution, and an AI agent that can generate or fix code directly inside the editor.

The project focuses on clarity, usability, and practical integration of generative AI into the development workflow.

---

## Core Features

- Multi-file code editor with syntax-aware formatting  
- Built-in terminal for executing Python code  
- File creation and deletion inside the IDE  
- AI agent for code generation and error fixing  
- Sidebar-based project and API key management  

---

## How It Works

1. The user writes or edits code in the editor  
2. Code can be executed directly from the interface  
3. Output is displayed in the integrated terminal  
4. The AI agent can modify or generate code on request  
5. Updated code is written back into the active file  

---
## Installation

Install dependencies using:

```bash
pip install -r requirements.txt

```md
## Running the Application

Start the IDE with:

```bash
streamlit run app.py
Add your Gemini API key in the sidebar when prompted.

Limitations

Python code execution only

Internet connection required for AI features

Not intended for large or production-scale projects


