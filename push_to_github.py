import os
from pathlib import Path
from dotenv import load_dotenv
import dulwich.porcelain as git

# Load credentials from user home .env or project .env
home_env = Path.home() / '.env'
if home_env.exists():
    load_dotenv(home_env)

project_env = Path(__file__).resolve().parent / '.env'
if project_env.exists():
    load_dotenv(project_env)

token = os.getenv('GITHUB_TOKEN')
if not token:
    print("ERROR: GITHUB_TOKEN not found in ~/.env or project .env.")
    print("Please set your token securely using the prompt command.")
    exit(1)

repo_path = str(Path(__file__).resolve().parent)
remote_url = f"https://mijanur531:{token}@github.com/mijanur531/alz_predictor.git"

print("Connecting to https://github.com/mijanur531/alz_predictor.git...")
try:
    git.push(repo_path, remote_url, 'refs/heads/main')
    print("SUCCESS: Successfully pushed all commits to https://github.com/mijanur531/alz_predictor.git!")
except Exception as e:
    print(f"Push failed: {e}")
    exit(1)
