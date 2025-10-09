from flask import Flask, request, jsonify
import os, datetime, subprocess, base64
from github import Github

app = Flask(__name__)

EXPECTED_SECRET = os.environ.get("PROJECT_SECRET")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Load templates
with open("LICENSE", "r") as f:
    LICENSE_TEMPLATE = f.read()

with open("README_template.md", "r") as f:
    README_TEMPLATE = f.read()

def save_attachments(app_folder, attachments):
    """
    Save attachments (base64 encoded) into the app folder
    """
    for att in attachments:
        filename = att.get("name")
        data_url = att.get("url")
        if not filename or not data_url:
            continue
        try:
            base64_data = data_url.split(",")[1]
            file_path = os.path.join(app_folder, filename)
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(base64_data))
            print(f"Saved attachment: {filename}")
        except Exception as e:
            print(f"Failed to save {filename}: {e}")

def create_or_update_repo(app_folder, task_name, round_number):
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repo_name = task_name
    try:
        repo = user.get_repo(repo_name)
        is_new_repo = False
    except:
        repo = user.create_repo(repo_name, private=False)
        is_new_repo = True

    subprocess.run(["git", "init"], cwd=app_folder, check=True)
    subprocess.run(["git", "add", "."], cwd=app_folder, check=True)
    subprocess.run(["git", "commit", "-m", f"Round {round_number} update"], cwd=app_folder, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=app_folder, check=True)
    subprocess.run(["git", "remote", "add", "origin", repo.clone_url], cwd=app_folder, check=False)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=app_folder, check=True)

    if is_new_repo:
        repo.create_file("LICENSE", "Add MIT License", LICENSE_TEMPLATE, branch="main")
        repo.create_file("README.md", "Add README", README_TEMPLATE.format(APP_NAME=repo_name, TASK_NAME=repo_name), branch="main")

    pages_url = f"https://{user.login}.github.io/{repo_name}/"
    commit_sha = repo.get_commits()[0].sha
    return repo.clone_url, pages_url, commit_sha

@app.route("/api-endpoint", methods=["POST"])
def api_endpoint():
    data = request.get_json(force=True)
    if data.get("secret") != EXPECTED_SECRET:
        return jsonify({"error": "invalid secret"}), 400

    task_name = data.get("task", f"app_{datetime.datetime.utcnow().timestamp()}")
    round_number = data.get("round", 1)
    os.makedirs(task_name, exist_ok=True)

    # Save attachments
    attachments = data.get("attachments", [])
    save_attachments(task_name, attachments)

    # Create/update index.html
    content = f"<h1>Generated App for {task_name} - Round {round_number}</h1>"
    if "brief" in data:
        content += f"<p>Brief: {data['brief']}</p>"
    with open(f"{task_name}/index.html", "w") as f:
        f.write(content)

    # Push to GitHub
    try:
        repo_url, pages_url, commit_sha = create_or_update_repo(task_name, task_name, round_number)
    except Exception as e:
        return jsonify({"error": "GitHub push failed", "details": str(e)}), 500

    # Notify evaluation server
    if data.get("evaluation_url"):
        import requests
        payload = {
            "email": data.get("email"),
            "task": data.get("task"),
            "round": round_number,
            "nonce": data.get("nonce"),
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }
        try:
            r = requests.post(data["evaluation_url"], json=payload, timeout=10)
            print("Evaluation POST:", r.status_code, r.text)
        except Exception as e:
            print("Failed to notify evaluator:", e)

    return jsonify({
        "status": "ok",
        "task": task_name,
        "round": round_number,
        "repo_url": repo_url,
        "pages_url": pages_url
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
