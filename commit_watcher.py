import requests
import argparse
import re
from termcolor import colored
from pathlib import Path
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
GITHUB_BRANCH_API_URL = "https://api.github.com/repos/{owner}/{repo}/branches"
GITHUB_COMPARE_URL = "https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
CONFIG_FILE = "config.json"

STALE_BRANCH_DAYS = 30

def color_message(message, severity):
    print(colored(message, SEVERITY_COLORS.get(severity, 'white')))

def get_extension(file_name):
    if file_name.startswith(".") and len(file_name) > 1:
        return file_name
    else:
        file_path = Path(file_name)
        return file_path.suffix  

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

def get_branches(owner, repo, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = GITHUB_BRANCH_API_URL.format(owner=owner, repo=repo)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        color_message(f"Failed to fetch branches: {response.status_code}", 'critical')
        return []
    return response.json()

def compare_branches(owner, repo, base, head, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = GITHUB_COMPARE_URL.format(owner=owner, repo=repo, base=base, head=head)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        color_message(f"Failed to compare branches: {response.status_code}", 'critical')
        return None
    return response.json()

def analyze_commit(commit, patterns=DEFAULT_PATTERNS, sensitive_files=SENSITIVE_FILES, token=None, max_commit_size=None, restricted_file_types=None):
    commit_message = commit['commit']['message']
    commit_url = commit['html_url']
    color_message(f"Analyzing commit: {commit_message} ({commit_url})", 'info')

    commit_details = get_commit_details(commit['url'], token)
    if not commit_details:
        return False

    files = commit_details.get('files', [])
    reasons = []

    # Check for commit size
    total_lines_changed = sum(file['changes'] for file in files)
    if max_commit_size and total_lines_changed > max_commit_size:
        reasons.append(f"Commit exceeds size limit with {total_lines_changed} lines changed (limit: {max_commit_size})")
        color_message(f"Commit size exceeds the maximum allowed limit: {total_lines_changed} lines (limit: {max_commit_size})", 'critical')

    # Check for restricted file types
    if restricted_file_types:
        for file in files:
            filename = file['filename']
            file_ext = get_extension(filename)
            if file_ext in restricted_file_types:
                reasons.append(f"Restricted file type '{file_ext}' found in '{filename}'")
                color_message(f"Restricted file type found: {filename}", 'critical')

    # Check for risky patterns
    for pattern in patterns:
        if re.search(pattern, commit_message, re.IGNORECASE):
            reasons.append(f"Pattern '{pattern}' found in commit message")
            color_message(f"Pattern '{pattern}' found in commit message: {commit_message} ({commit_url})", 'warning')

    # Check for sensitive files
    for file in files:
        filename = file['filename']
        if any(filename.endswith(ext) for ext in sensitive_files):
            reasons.append(f"Sensitive file '{filename}' detected")
            color_message(f"Sensitive file detected: {filename} in commit {commit_url}", 'critical')

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
    
def monitor_repository(owner, repo, branch='main', patterns=DEFAULT_PATTERNS, token=None, max_commit_size=None, restricted_file_types=None):
    color_message(f"Monitoring repository: {owner}/{repo} on branch {branch}", 'info')
    commits = get_recent_commits(owner, repo, branch, token)
    if not commits:
        color_message("No commits found or failed to fetch.", 'info')
        return

def check_branches(owner, repo, token, stale_days, webhook_url=None):
    branches = get_branches(owner, repo, token)

    reasons = []
    if not branches:
        return

    for branch in branches:
        branch_name = branch['name']
        latest_commit_sha = branch['commit']['sha']
        commit_details = get_commit_details(branch['commit']['url'], token)

        if commit_details:
            commit_date = commit_details['commit']['author']['date']
            commit_timestamp = time.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
            commit_age_in_days = (time.time() - time.mktime(commit_timestamp)) / (60 * 60 * 24)

            if commit_age_in_days > stale_days:
                message = f"**Branch** '[{branch_name}](https://github.com/{owner}/{repo}/tree/{branch_name})' is stale (last commit {int(commit_age_in_days)} days ago)."
                color_message(message, 'warning')
                if webhook_url:
                    reasons.append(message)

        if branch['name'] != 'main':
            comparison = compare_branches(owner, repo, 'main', branch['name'], token)
            if comparison and comparison.get('behind_by', 0) > branch_behind_by: 
                message = f"**Branch** '{branch_name}' is behind main by {comparison['behind_by']} commits. Consider merging."
                color_message(message, 'critical')
                if webhook_url:
                    reasons.append(message)

    if webhook_url and len(reasons) > 0:
        send_branch_notification(webhook_url, repo, reasons)

def send_branch_notification(webhook_url, branch_name, reasons):
    detailed_reasons = "\n".join(f"- {reason}" for reason in reasons)
    data = {
        "content": f"⚠️ **Branch Alert: {branch_name}** ⚠️\n{detailed_reasons}"
    }
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, json=data, headers=headers)
        if response.status_code in [204, 200]:
            color_message(f"Notification for branch '{branch_name}' sent successfully", "info")
        else:
            color_message(f"Failed to send notification: {response.status_code} - {response.text}", 'warning')
    except Exception as e:
        color_message(f"Error sending notification: {e}", "critical")

def monitor_in_background(owner, repo, branch='main', token=None, interval=300, stale_branch_check_interval=86400, stale_days=30, max_commit_size=None, restricted_file_types=None, webhook_url=None):
    color_message(f"Starting background monitoring for repository: {owner}/{repo} on branch {branch}", 'info')
    last_commit_sha = None
    last_stale_check = time.time()

    while True:
        color_message("Checking for new commits...", 'info')
        commits = get_recent_commits(owner, repo, branch, token)

        if commits:
            new_commits = [commit for commit in commits if commit['sha'] != last_commit_sha]
            for commit in reversed(new_commits):
                analyze_commit(commit, token=token, max_commit_size=max_commit_size, restricted_file_types=restricted_file_types)
                last_commit_sha = commit['sha']
            color_message(f"Found {len(new_commits)} new commit(s)", 'info')

        current_time = time.time()
        if current_time - last_stale_check > stale_branch_check_interval:
            check_branches(owner, repo, token, stale_days, webhook_url)
            last_stale_check = current_time

        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor a GitHub repository for risky commits and stale branches.")
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

    max_commit_size = config.get("MAX_COMMIT_SIZE") or input("Enter the maximum allowed commit size (in lines): ").strip()
    config["MAX_COMMIT_SIZE"] = int(max_commit_size)

    restricted_file_types = config.get("RESTRICTED_FILE_TYPES") or input("Enter restricted file types (comma-separated, e.g., .exe,.dll): ").strip()
    restricted_file_types = restricted_file_types if restricted_file_types else []
    config["RESTRICTED_FILE_TYPES"] = restricted_file_types

    stale_days = config.get("STALE_DAYS") or input("Enter the number of days to consider a branch stale: ").strip()
    config["STALE_DAYS"] = int(stale_days)

    stale_branch_check_interval = config.get("STALE_BRANCH_CHECK_INTERVAL") or input("Enter the interval (in seconds) to check for stale branches: ").strip()
    config["STALE_BRANCH_CHECK_INTERVAL"] = int(stale_branch_check_interval)

    branch_behind_by = config.get("BRANCH_BEHIND_BY") or input("Enter the number of commits to check for diverging branches: ").strip()
    config["BRANCH_BEHIND_BY"] = int(branch_behind_by)

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

    if args.background:
        monitor_in_background(args.owner, args.repo, args.branch, token=token, interval=int(interval), stale_branch_check_interval=int(stale_branch_check_interval), stale_days=int(stale_days), max_commit_size=int(max_commit_size), restricted_file_types=restricted_file_types, webhook_url=webhook_url)
    else:
        monitor_repository(args.owner, args.repo, args.branch, token=token, max_commit_size=int(max_commit_size), restricted_file_types=restricted_file_types)
