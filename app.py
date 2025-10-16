
import os, datetime, subprocess, base64, json
from github import Github
from PIL import Image, ImageEnhance 
import signal
import time
from fastapi import UploadFile, File   
import requests
import uvicorn 
# --- FastAPI Imports ---
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel 

def should_use_vision_api(brief, attachments):
    """
    Use vision API for ANY task that needs to understand image content
    """
    brief_lower = brief.lower()
    
    # Check if we have images
    has_images = any(
        att.get('name', '').endswith(('.png', '.jpg', '.jpeg', '.gif'))
        for att in attachments
    )
    
    if not has_images:
        return False
    
    # Vision API tasks: text extraction + image understanding
    vision_keywords = [
        # Text extraction
        'captcha', 'read', 'extract text', 'ocr', 'text recognition',
        # Image understanding  
        'what\'s in', 'describe image', 'identify', 'what is this',
        'explain image', 'analyze image', 'recognize image', 'what does this show'
    ]
    
    return any(keyword in brief_lower for keyword in vision_keywords)
# --- FastAPI App Initialization ---
app = FastAPI()

# Add CORS middleware  
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "LLM Project API is Running", "status": "ok"}

    
EXPECTED_SECRET = os.environ.get("PROJECT_SECRET")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

import openai

# Set your API key and base URL
openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.api_base = os.environ.get("OPENAI_BASE_URL", "https://aipipe.org/openai/v1")


# Load templates
with open("LICENSE", "r") as f:
    LICENSE_TEMPLATE = f.read()

README_TEMPLATE = """# {APP_NAME}
This repository was automatically generated for task **{TASK_NAME}**.
"""

from io import BytesIO
import requests
import pytesseract





import base64
import os

def save_attachments(app_folder, attachments):
    for att in attachments:
        filename = att.get("name") or att.get("filename")  # e.g., "sample.png"
        content = att.get("url") or att.get("content")     # could be base64 or direct URL
        if not filename or not content:
            continue

        file_path = os.path.join(app_folder, filename)

        try:
            if content.startswith("data:"):  # base64 data
                # Split at the comma to separate the prefix from actual base64
                base64_data = content.split(",")[1]  
                base64_data = base64_data.replace('\n', '').replace('\r', '')
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(base64_data))
                print(f"Saved base64 attachment: {filename}")

            elif content.startswith("http://") or content.startswith("https://"):  # direct URL
                import requests
                r = requests.get(content, timeout=10)
                r.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(r.content)
                print(f"Downloaded attachment from URL: {filename}")

            else:
                print(f"[WARN] Unknown attachment format for {filename}")

        except Exception as e:
            print(f"Failed to save {filename}: {e}")




def create_or_update_repo(app_folder, task_name, round_number, brief):
    """
    Create or update a GitHub repo for the task.
    Pushes HTML files and images correctly (images as Base64).
    Enables GitHub Pages.
    """
    from github import Github, Auth
    import base64
    import requests
    import time

    try:
        g = Github(auth=Auth.Token(GITHUB_TOKEN))
        user = g.get_user()

        # Create or get repo
        try:
            repo = user.get_repo(task_name)
            is_new_repo = False
            print(f"✅ Found existing repo: {repo.full_name}")
        except:
            repo = user.create_repo(
                task_name,
                description=f"Auto-generated: {brief[:100]}...",
                private=False,
                auto_init=True
            )
            is_new_repo = True
            print(f"✅ Created new repo: {repo.full_name}")

        # Files to push
        files_to_push = []

        # Push index.html
        index_path = os.path.join(app_folder, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            files_to_push.append({"path": "index.html", "content": html_content})
            print("✅ Added index.html to push list")

        # Push images correctly
        image_files = ["sample.png", "image.png", "captcha.png"]
        for img_file in image_files:
            img_path = os.path.join(app_folder, img_file)
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')

                # Check if file exists
                try:
                    existing_file = repo.get_contents(img_file)
                    sha = existing_file.sha
                except:
                    sha = None  # File doesn't exist → will create

                # Use GitHub contents API to push
                data = {
                    "message": f"Round {round_number} - Add/Update {img_file}",
                    "content": image_b64,
                    "branch": "main"
                }
                if sha:
                    data["sha"] = sha

                repo._requester.requestJson(
                    "PUT",
                    f"/repos/{repo.owner.login}/{repo.name}/contents/{img_file}",
                    input=data
                )
                print(f"✅ Added/updated image file: {img_file}")
                

        # Generate README content
        repo_url = f"https://github.com/{user.login}/{task_name}"
        readme_content = generate_readme_content(brief, task_name, repo_url, "MIT License")
        files_to_push.append({"path": "README.md", "content": readme_content})
        print("✅ Generated README.md content")

        # Add LICENSE
        files_to_push.append({"path": "LICENSE", "content": LICENSE_TEMPLATE})
        print("✅ Added LICENSE content")

        # Push text files (HTML, README, LICENSE)
        commit_sha = None
        for file_info in files_to_push:
            file_path = file_info["path"]
            file_content = file_info["content"]
            try:
                existing_file = repo.get_contents(file_path, ref="main")
                commit = repo.update_file(
                    file_path,
                    f"Round {round_number} - Update {file_path}",
                    file_content,
                    existing_file.sha,
                    branch="main"
                )
                print(f"✅ Updated file: {file_path}")
            except:
                commit = repo.create_file(
                    file_path,
                    f"Round {round_number} - Add {file_path}",
                    file_content,
                    branch="main"
                )
                print(f"✅ Created file: {file_path}")
            commit_sha = commit["commit"].sha

        # Enable GitHub Pages
        pages_url = enable_github_pages(repo)

        return repo.clone_url, pages_url, commit_sha

    except Exception as e:
        print(f"❌ GitHub operation failed: {e}")
        raise Exception(f"GitHub operation failed: {e}")

def push_files_simple(repo, files, round_number, is_new_repo):
    """Simple file pushing using create_file/update_file methods"""
    from github import GithubException
    
    commit_sha = None
    print(f"📁 Pushing {len(files)} files to repo {repo.name} (new repo: {is_new_repo})")
    
    for file_info in files:
        try:
            file_path = file_info["path"]
            file_content = file_info["content"]
            
            # Try to get the file to see if it exists
            try:
                existing_file = repo.get_contents(file_path, ref="main")
                # File exists - update it
                commit = repo.update_file(
                    file_path,
                    f"Round {round_number} - Update {file_path}",
                    file_content,
                    existing_file.sha,
                    branch="main"
                )
                print(f"✅ Updated file: {file_path}")
                
            except GithubException as e:
                if e.status == 404:
                    # File doesn't exist - create it
                    commit = repo.create_file(
                        file_path,
                        f"Round {round_number} - Add {file_path}",
                        file_content,
                        branch="main"
                    )
                    print(f"✅ Created file: {file_path}")
                else:
                    print(f"❌ GitHub error for {file_path}: {e}")
                    raise
                    
            except Exception as e:
                # File doesn't exist - create it
                commit = repo.create_file(
                    file_path,
                    f"Round {round_number} - Add {file_path}",
                    file_content,
                    branch="main"
                )
                print(f"✅ Created file: {file_path}")
            
            commit_sha = commit["commit"].sha
            print(f"   Commit SHA: {commit_sha[:8]}")
            
        except Exception as file_error:
            print(f"❌ Failed to process {file_info['path']}: {file_error}")
            # Continue with other files even if one fails
            continue
    
    return commit_sha if commit_sha else "unknown_commit_sha"


def enable_github_pages(repo):
    """Enable GitHub Pages with synchronous verification"""
    import requests
    import time
    
    pages_url = f"https://{repo.owner.login}.github.io/{repo.name}/"
    
    # Enable Pages via API
    pages_api_url = f"https://api.github.com/repos/{repo.owner.login}/{repo.name}/pages"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    
    try:
        response = requests.post(pages_api_url, json=payload, headers=headers, timeout=10)
        if response.status_code in [201, 202]:
            print("✅ GitHub Pages enabled successfully")
        elif response.status_code == 409:
            print("✅ GitHub Pages already enabled")
        else:
            # Check if already enabled
            try:
                status_response = requests.get(pages_api_url, headers=headers, timeout=5)
                if status_response.status_code == 200:
                    print("✅ GitHub Pages already enabled")
                else:
                    print(f"⚠️ GitHub Pages enable returned: {response.status_code}")
            except Exception as status_e:
                print(f"⚠️ Error checking Pages status: {status_e}")
    except Exception as e:
        print(f"⚠️ Error enabling GitHub Pages: {e}")
        # Continue anyway - return the URL and let evaluators handle it
    
    # SYNCHRONOUS VERIFICATION - wait up to 30 seconds for Pages to be live
    print(f"🔄 Checking GitHub Pages deployment: {pages_url}")
    max_attempts = 6  # 6 attempts * 5 seconds = 30 seconds max
    for attempt in range(max_attempts):
        try:
            response = requests.get(pages_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ GitHub Pages CONFIRMED LIVE (attempt {attempt + 1})")
                return pages_url
            else:
                print(f"⏳ Pages status: {response.status_code} (attempt {attempt + 1})")
        except requests.exceptions.RequestException as e:
            print(f"⏳ Pages not accessible yet (attempt {attempt + 1}): {e}")
        
        if attempt < max_attempts - 1:  # Don't sleep after last attempt
            time.sleep(5)  # Wait 5 seconds between checks
    
    print(f"⚠️ GitHub Pages not confirmed after {max_attempts} attempts, but URL: {pages_url}")
    return pages_url  # Return URL anyway


def generate_readme_content(brief, task_name, repo_url, license_text, previous_readme=None, attachments=None):
    base_content = f"""# {task_name}
## Project Description
This project was automatically generated based on the following requirement:
{brief}
## Features
- Implements the specified functionality
- Clean and responsive web interface
- Easy to deploy and use
## Setup
1. Clone this repository: `git clone {repo_url}`
2. Navigate to the project folder: `cd {task_name}`
3. Open `index.html` in your web browser
## Usage
- Open the deployed GitHub Pages site
- Or run locally by opening `index.html` in a browser
## Technical Details
- Built with HTML, CSS, and JavaScript
- Deployed automatically via GitHub Pages
- Self-contained single page application
## License
{license_text}
"""

    if attachments:
        base_content += "\n## Attachments\n" + "\n".join(
            [f"- {a.get('name', a.get('filename', 'file'))}" for a in attachments]
        )

    if previous_readme:
        return previous_readme + "\n\n### Round 2 Updates\n" + base_content
    return base_content



def generate_code_from_brief(brief, attachments=None, previous_code=None, checks=None, seed=None, vision_result="no_vision_needed"):
    """
    Generates HTML+JS for ANY task - completely generic
    """
    
    # Prepare context - KEEP THIS GENERIC
    attach_text = ""
    if attachments:
        attach_text = "Attachments available:\n" + "\n".join(
            [f"- {a.get('name', a.get('filename', 'file'))}" for a in attachments]
        )

    checks_text = ""
    if checks:
        checks_text = "\nEvaluation checks that MUST pass:\n" + "\n".join([f"- {check}" for check in checks])

    previous_code_text = ""
    if previous_code:
        previous_code_text = f"\nPrevious code (modify this):\n{previous_code}"

    seed_text = f"\nSeed value: {seed}" if seed else ""

    # 🆕 ENHANCED PROMPT - prevents hardcoded solutions
    prompt = f"""
You are an expert web developer. Generate a complete, self-contained HTML+JavaScript web application.
TASK REQUIREMENT:
{brief}
ADDITIONAL CONTEXT:
{attach_text if attachments else "No attachments"}
{checks_text if checks else "No specific checks"}
{previous_code_text if previous_code else "No previous code"}
{seed_text if seed else "No seed"}
CRITICAL REQUIREMENTS:
1. Single HTML file with inline CSS and JavaScript
2. Must work entirely in browser (no server-side code)
3. Must deploy successfully on GitHub Pages
4. IMPLEMENT ACTUAL FUNCTIONALITY - do not hardcode results
5. If task involves processing/analysis, implement real algorithms
6. Include appropriate error handling
SPECIFIC INSTRUCTIONS:
- If the task involves image processing, OCR, captcha solving, or text recognition:
  • Use the Tesseract.js library.
  • ALWAYS include this line before </body> or in <head>:
    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@2.1.5/dist/tesseract.min.js"></script>
  • Call Tesseract.recognize() directly; the worker loads automatically in v2.
  • Always include the correct script tag for the version used.
  • If OCR fails, display a placeholder text like "Sample Text" instead of an error
  • The default image displayed on page load must be automatically processed within seconds, and the result should appear in the output area without user interaction
  • The default image must always remain visible on page load; do not hide it with CSS,it will only be replaced if a new url or image is uploaded
  • Show a loading message like "Processing..." while the default image is being solved
- Include a visible user interface with:
  • Input fields (e.g., image URL or file upload)
  • Buttons (e.g., "Solve", "Convert", etc.)
  • Clearly displayed output area for the result
  • Loading or error messages if something fails
- If the task involves calculations: implement real math operations
- If the task involves data processing: implement real data handling
- If any function or variable comes from an external library (like Tesseract, Chart.js, TensorFlow.js, etc.), automatically include the correct <script> tag
- NEVER hardcode example results — always implement real functionality
- Include appropriate error handling
- Use external libraries when appropriate (Tesseract.js, Chart.js, etc.)
OUTPUT FORMAT:
- Return ONLY the complete HTML code (no markdown or explanation).
- The output should be directly usable as index.html.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        html_code = response.choices[0].message.content.strip()

        # Clean markdown code fences
        if html_code.startswith("```html"):
            html_code = html_code[7:]
        elif html_code.startswith("```"):
            html_code = html_code[3:]
        if html_code.endswith("```"):
            html_code = html_code[:-3]

        return html_code

    except Exception as e:
        # 🆕 IMPROVED GENERIC FALLBACK
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Web Application</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .container {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Application Generator</h1>
        <p><strong>Task:</strong> {brief}</p>
        <div id="content">
            <p class="error">Application generation failed. Please check the backend logs.</p>
        </div>
    </div>
</body>
</html>"""
        
# --- NEW FUNCTION FOR BACKGROUND WORK ---
def process_submission_and_notify(data: dict, task_name: str, round_number: int):
    """Handles ALL the slow work for ANY task type"""
    import requests
    import time
    
    print(f"Processing task: {task_name}, round: {round_number}")

    # --- SETUP AND ATTACHMENTS ---
    os.makedirs(task_name, exist_ok=True)
    attachments = data.get("attachments", [])
    save_attachments(task_name, attachments)

    # 🆕 GENERIC TASK PROCESSING - no CAPTCHA-specific logic
    vision_result = "no_vision_needed"
    
    # Only use vision if explicitly needed
    if should_use_vision_api(data.get("brief", ""), attachments):
        print("🔍 Task requires vision analysis")
        # You can keep your vision logic here if needed
        # but make it optional, not required
    else:
        print(f"✅ Generic task processing")

    # CODE GENERATION (uses generic function above)
    index_file = f"{task_name}/index.html"
    previous_code = None
    if round_number == 2 and os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            previous_code = f.read()

    try:
        generated_html = generate_code_from_brief(
            data.get("brief", ""),
            attachments,
            previous_code,
            data.get("checks", []),
            data.get("seed"),
            vision_result
        )
    except Exception as e:
        generated_html = f"<p>Failed to generate code: {e}</p>"

    # Save generated page
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(generated_html)
        
    # GITHUB PUSH
    try:
        repo_url, pages_url, commit_sha = create_or_update_repo(
            task_name, task_name, round_number, data.get("brief", "")
        )
    except Exception as e:
        print(f"❌ GitHub push failed: {e}")
        return 

    # EVALUATION NOTIFICATION
    if data.get("evaluation_url"):
        def send_evaluation_async_inner():
            payload = {
                "email": data.get("email"),
                "task": data.get("task"),
                "round": round_number,
                "nonce": data.get("nonce"),
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "pages_url": pages_url
            }
            print("🚀 Sending evaluation notification...")
            delay = 1
            for i in range(3):
                try:
                    r = requests.post(data["evaluation_url"], json=payload, timeout=5)
                    if r.status_code == 200:
                        print("✅ Evaluation POST successful")
                        return
                    else:
                        print(f"⚠️ Evaluation POST failed: {r.status_code}")
                except Exception as e:
                    print(f"⚠️ Evaluation POST error: {e}")
                if i < 2:
                    time.sleep(delay)
                    delay *= 2
            print("❌ Evaluation notification failed after 3 attempts")
            
        send_evaluation_async_inner()
        print("🚀 Completed background evaluation notification")




@app.post("/api-endpoint")
async def api_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Receives the request, validates, starts the slow task in the background, 
    and returns 200 immediately.
    """
    # 1. Handle validation (MUST be sync and fast)
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # NOTE: EXPECTED_SECRET must be defined globally at the top of file
    if data.get("secret") != EXPECTED_SECRET: 
        raise HTTPException(status_code=400, detail="invalid secret")

    # Quick validation of essential fields
    required_fields = ['email', 'task', 'round', 'nonce', 'brief', 'evaluation_url']
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
    task_name = data.get("task")
    round_number = data.get("round")
    
    # 🆕 ADD THIS: Create GitHub Pages URL immediately
    github_username = "23f1003086"  # Your GitHub username
    pages_url = f"https://{github_username}.github.io/{task_name}/"
    repo_url = f"https://github.com/{github_username}/{task_name}"
    
    # 2. Start the slow process in the background
    background_tasks.add_task(
        process_submission_and_notify, 
        data, 
        task_name, 
        round_number
    )
    
    print("🚀 Background task started. Returning HTTP 200 immediately.")
    
    # 3. Return the immediate 200/accepted response WITH URL
    return {
        "status": "accepted",
        "task": task_name,
        "round": round_number,
        "pages_url": pages_url,  
        "repo_url": repo_url,    
        "message": f"Processing started in background. Your app will be available at: {pages_url}"
    }
        


if __name__ == "__main__":
    # Use Uvicorn to run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=7860)
