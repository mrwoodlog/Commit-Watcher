import requests
import argparse
import re
from termcolor import colored
import os
import json
import time

DEFAULT_PATTERNS = [
    r'pass(?:word)?',
    r'secret',
    r'api[_-]?key',
    r'client[_-]?secret',
    r'token'
]

SENSITIVE_FILES = [
    '.env',
    '.pem',
    '.key',
    '.crt',
    '.pfx'
]

SEVERITY_COLORS = {
    'info': 'cyan',
    'warning': 'yellow',
    'critical': 'red'
}

GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/commits"
CONFIG_FILE = "config.json"

def color_message(message, severity):
    print(colored(message, SEVERITY_COLORS.get(severity, 'white')))

def get_commit_details(url, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        color_message(f"Failed to fetch commit details: {response.status_code}", 'critical')
        return None
    return response.json()

def get_recent_commits(owner, repo, branch='main', token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = GITHUB_API_URL.format(owner=owner, repo=repo)
    params = {'sha': branch}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        color_message(f"Failed to fetch commits: {response.status_code}", 'critical')
        return []
    return response.json()

def analyze_commit(commit, patterns=DEFAULT_PATTERNS, sensitive_files=SENSITIVE_FILES, token=None):
    commit_message = commit['commit']['message']
    commit_url = commit['html_url']
    color_message(f"Analyzing commit: {commit_message} ({commit_url})", 'info')

    commit_details = get_commit_details(commit['url'], token)
    if not commit_details:
        return False

    files = commit_details.get('files', [])
    reasons = []

    for pattern in patterns:
        if re.search(pattern, commit_message, re.IGNORECASE):
            reasons.append(f"Pattern '{pattern}' found in commit message")
            color_message(f"Pattern '{pattern}' found in commit message: {commit_message} ({commit_url})", 'warning')

    for file in files:
        filename = file['filename']
        if any(filename.endswith(ext) for ext in sensitive_files):
            reasons.append(f"Sensitive file '{filename}' detected")
            color_message(f"Sensitive file detected: {filename} in commit {commit_url})", 'critical')

        patch = file.get('patch', '')
        for pattern in patterns:
            if re.search(pattern, patch, re.IGNORECASE):
                reasons.append(f"Pattern '{pattern}' found in file '{filename}'")
                color_message(f"Pattern '{pattern}' found in file changes: {filename} ({commit_url})", 'warning')

    if reasons:
        send_notification(commit, reasons)
        return True
    return False

def send_notification(commit, reasons):
    webhook_url = config["WEBHOOK_URL"]
    if webhook_url:
        commit_message = commit['commit']['message']
        commit_url = commit['html_url']
        author = commit['commit']['author']['name']
        detailed_reasons = "\n".join(f"- {reason}" for reason in reasons)
        data = {
            "content": f"⚠️ **Risky Commit Detected!** ⚠️\n**Author:** {author}\n**Reasons:**\n{detailed_reasons}\n**Commit:** [{commit_message}]({commit_url})"
        }
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(webhook_url, json=data, headers=headers)
            if response.status_code in [204, 200]:
                color_message("Notification sent successfully", "info")
            else:
                color_message(f"Failed to send notification: {response.status_code} - {response.text}", 'warning')
        except Exception as e:
            color_message(f"Error sending notification: {e}", "critical")

def check_rate_limit(token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    if response.status_code == 200:
        rate_info = response.json()
        remaining = rate_info['rate']['remaining']
        reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(rate_info['rate']['reset']))
        color_message(f"GitHub API rate limit: {remaining} requests remaining. Reset at {reset_time}.", 'info')
        return remaining
    else:
        color_message(f"Failed to check rate limit: {response.status_code}", 'critical')
        return None

def monitor_in_background(owner, repo, branch='main', patterns=DEFAULT_PATTERNS, token=None, interval=300):
    color_message(f"Starting background monitoring for repository: {owner}/{repo} on branch {branch}", 'info')
    last_commit_sha = None

    while True:
        color_message("Checking for new commits...", 'info')
        remaining_requests = check_rate_limit(token)
        if remaining_requests is not None and remaining_requests < 5:
            color_message("API rate limit is low. Waiting until reset.", 'critical')
            time.sleep(interval * 2)
            continue

        commits = get_recent_commits(owner, repo, branch, token)
        if not commits:
            color_message("No commits found or failed to fetch.", 'info')
            time.sleep(interval)
            continue

        new_commits = []
        for commit in commits:
            if commit['sha'] == last_commit_sha:
                break
            new_commits.append(commit)

        if new_commits:
            color_message(f"Found {len(new_commits)} new commit(s) to analyze.", 'info')
            for commit in reversed(new_commits):
                analyze_commit(commit, patterns, token=token)
            last_commit_sha = new_commits[0]['sha']

        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor a GitHub repository for risky commits.")
    parser.add_argument("owner", help="Owner of the GitHub repository")
    parser.add_argument("repo", help="Name of the GitHub repository")
    parser.add_argument("--branch", default="main", help="Branch to monitor (default: main)")
    parser.add_argument("--background", action="store_true", help="Enable background monitoring mode")

    args = parser.parse_args()

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
    else:
        config = {}

    token = config.get("GITHUB_TOKEN") or input("Enter your GitHub API token: ").strip()
    config["GITHUB_TOKEN"] = token

    webhook_url = config.get("WEBHOOK_URL") or input("Enter your Discord webhook URL (optional): ").strip()
    if webhook_url:
        config["WEBHOOK_URL"] = webhook_url

    interval = config.get("INTERVAL") or input("Enter the interval (in seconds) for background checks: ").strip()
    config["INTERVAL"] = int(interval)

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

    if args.background:
        monitor_in_background(args.owner, args.repo, args.branch, token=token, interval=int(interval))
