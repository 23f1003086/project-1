# LLM Deploy Project

This FastAPI-based application automates the generation, deployment, and evaluation of web applications based on JSON task briefs. It handles:

- Receiving and verifying task requests with secrets
- Dynamic app generation using LLM-assisted code
- GitHub repository creation, updates, and MIT license enforcement
- GitHub Pages deployment and validation (200 OK)
- Posting task metadata to an evaluation server
- Handling multiple rounds of updates/refactoring based on new task briefs

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

### 3. Run the FastAPI App
```bash
uvicorn app:app --reload

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
curl -X POST https://s23f1003086-llm-project-23f1003086.hf.space/api-endpoint \
-H "Content-Type: application/json" \
-d '{
  "email": "student@example.com",
  "secret": "fakesecret",
  "task": "captcha-solver-001",
  "round": 1,
  "nonce": "abcd-1234",
  "brief": "Create a captcha solver",
  "checks": [
    "Repo has MIT license",
    "Page displays solved captcha"
  ],
  "evaluation_url": "https://evaluator.example.com/notify",
  "attachments": [
    {"name": "sample.png", "url": "data:image/png;base64,..."}
  ]
}'
```

### Round 2
```bash
curl -X POST https://s23f1003086-llm-project-23f1003086.hf.space/api-endpoint \
-H "Content-Type: application/json" \
-d '{
  "email": "student@example.com",
  "secret": "fakesecret",
  "task": "captcha-solver-001",
  "round": 2,
  "nonce": "efgh-5678",
  "brief": "Update app to handle SVG images",
  "checks": [
    "Repo has MIT license",
    "Page displays solved captcha including SVG"
  ],
  "evaluation_url": "https://evaluator.example.com/notify",
  "attachments": []
}'
```

---

## 🧠 Code Overview

| File                   | Description                                                                |
| ---------------------- | -------------------------------------------------------------------------- |
| `app.py`               | Fast API handling requests, secret verification, GitHub integration, etc. |
| `apt.txt`              |                                                                            |
| `requirements.txt`     | all dependencies                                                           |
| `Dockerfile`           | Optional: Deploy app on Hugging Face Spaces using Docker                   |
| `README.md`            | This file                                                                  |
| `LICENSE`              | MIT License                                                                |


---

## 📁 Folder Structure

```
llm_deploy_project_23f1003086/
│
├── app.py
├── requirements.txt
├── apt.txt
├── Dockerfile
├── LICENSE
├── README.md
└── templates/
    └── index.html
```

---

## 📜 License

This project is licensed under the MIT License.

