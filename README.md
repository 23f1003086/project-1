# LLM Deploy Project

This Flask-based application automates the deployment and evaluation of student submissions via Hugging Face Spaces. It supports task verification, GitHub integration, and dynamic app generation based on JSON POST requests.

---

## 🔧 Setup Instructions

### 1. Activate Python Virtual Environment

#### Linux/macOS
```bash
source venv/bin/activate
```

#### Windows
```bash
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Flask App
```bash
python app.py
```

---

## 📦 Usage

The application expects a JSON POST request with the following fields:

- `email` – Student email ID  
- `secret` – Student-provided secret for verification  
- `task` – Unique task ID  
- `round` – 1 or 2  
- `nonce` – Unique nonce for the request  
- `brief` – Task description  
- `checks` – Evaluation checks  
- `attachments` – Base64-encoded files (images, CSV, JSON)

### ✅ App Workflow

- Secret verification  
- Minimal app generation based on task brief  
- Attachment saving to the app folder  
- GitHub repo creation or update  
- GitHub Pages deployment  
- Evaluation server notification  
- Round 2 updates (modifications/refactoring)

---

## 📤 Example JSON POST Requests

### Round 1
```bash
curl -X POST https://your-space-name.hf.space/api-endpoint \
-H "Content-Type: application/json" \
-d '{
  "email": "student@example.com",
  "secret": "my-college-secret",
  "task": "captcha-solver-001",
  "round": 1,
  "nonce": "abcd-1234",
  "brief": "Create a captcha solver",
  "checks": [
    "Repo has MIT license",
    "Page displays solved captcha"
  ],
  "attachments": [
    {"name": "sample.png", "url": "data:image/png;base64,..."}
  ]
}'
```

### Round 2
```bash
curl -X POST https://your-space-name.hf.space/api-endpoint \
-H "Content-Type: application/json" \
-d '{
  "email": "student@example.com",
  "secret": "my-college-secret",
  "task": "captcha-solver-001",
  "round": 2,
  "nonce": "efgh-5678",
  "brief": "Update app to handle SVG images",
  "checks": [
    "Repo has MIT license",
    "Page displays solved captcha including SVG"
  ],
  "attachments": []
}'
```

---

## 🧠 Code Overview

| File                   | Description                                                                |
| ---------------------- | -------------------------------------------------------------------------- |
| `app.py`               | Flask API handling requests, secret verification, GitHub integration, etc. |
| `requirements.txt`     | Python dependencies (Flask, requests, PyGithub, python-dotenv)             |
| `Dockerfile`           | Optional: Deploy app on Hugging Face Spaces using Docker                   |
| `README.md`            | This file                                                                  |
| `LICENSE`              | MIT License                                                                |
| `templates/index.html` | Basic HTML template for the deployed app                                   |

---

## 📁 Folder Structure

```
llm_deploy_project_23f1003086/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── LICENSE
├── README.md
└── templates/
    └── index.html
```

---

## 📜 License

This project is licensed under the MIT License.

