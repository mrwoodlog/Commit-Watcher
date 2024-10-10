import requests
import argparse
import re
from termcolor import colored

DEFAULT_PATTERNS = [
    r'password',
    r'secret',
    r'api_key',
    r'client_secret',
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


def color_message(message, severity):
    print(colored(message, SEVERITY_COLORS.get(severity, 'white')))


def get_recent_commits(owner, repo, branch='main', token=None):
    """Fetches recent commits from the specified repository."""
    headers = {'Authorization': f'token {token}'} if token else {}
    url = GITHUB_API_URL.format(owner=owner, repo=repo)
    params = {'sha': branch}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        color_message(f"Failed to fetch commits: {response.status_code}", 'critical')
        return []

    return response.json()


def analyze_commit(commit, patterns=DEFAULT_PATTERNS, sensitive_files=SENSITIVE_FILES):
    commit_message = commit['commit']['message']
    commit_url = commit['html_url']

    for pattern in patterns:
        if re.search(pattern, commit_message, re.IGNORECASE):
            color_message(f"Potential risk in commit message: {commit_message} ({commit_url})", 'warning')
            return True

    files = commit.get('files', [])
    for file in files:
        filename = file['filename']
        # Check if the file name or extension is sensitive
        if any(filename.endswith(ext) for ext in sensitive_files):
            color_message(f"Sensitive file detected: {filename} in commit {commit_url}", 'critical')
            return True

        patch = file.get('patch', '')
        for pattern in patterns:
            if re.search(pattern, patch, re.IGNORECASE):
                color_message(f"Potential risk in file changes: {filename} ({commit_url})", 'warning')
                return True

    return False


def monitor_repository(owner, repo, branch='main', patterns=DEFAULT_PATTERNS, token=None):
    color_message(f"Monitoring repository: {owner}/{repo} on branch {branch}", 'info')
    
    commits = get_recent_commits(owner, repo, branch, token)
    if not commits:
        color_message("No commits found or failed to fetch.", 'info')
        return

    for commit in commits:
        if analyze_commit(commit, patterns):
            color_message(f"Risky commit detected: {commit['commit']['message']} ({commit['html_url']})", 'critical')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor a GitHub repository for risky commits.")
    parser.add_argument("owner", help="Owner of the GitHub repository")
    parser.add_argument("repo", help="Name of the GitHub repository")
    parser.add_argument("--branch", default="main", help="Branch to monitor (default: main)")
    parser.add_argument("--token", help="GitHub API token for private repositories")

    args = parser.parse_args()
    monitor_repository(args.owner, args.repo, args.branch, token=args.token)
