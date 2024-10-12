# **Commit Watcher**

Welcome to **Commit Watcher**! 🎉 

This is a lightweight tool that keeps an eye on your GitHub repository to make sure no one’s accidentally leaking secrets or making suspicious changes. It scans for risky patterns like sensitive keywords (`password`, `token`), sketchy file types (`.env`, `.pem`), or code changes that look... a bit off.

### Why should you use it?  
You know that feeling when you push a commit and realize you accidentally added an API key? 🫠 Commit Watcher helps catch those mistakes *before* they become a problem. It’s like a safety net for your repos!

## **Cool Features**
- **Pattern Detection:** Spots keywords like `password` or `api_key` in commit messages or diffs.
- **Sensitive File Monitoring:** Alerts you if files like `.env` or `.pem` are added.
- **Code Smell Detection:** Flags big, unusual code changes (e.g., hundreds of lines added or deleted).
- **Background Monitoring:** Automatically monitors your repository for new commits at regular intervals.
- **Customizable:** Tweak the rules to your needs!

## **Getting Started**

### **1. What You Need**
- Python 3.7 or above.
- The `requests` and `termcolor` libraries.

### **2. Setting It Up**

1. **Grab the Code:**
   ```bash
   git clone https://github.com/mrwoodlog/commit-watcher.git
   cd commit-watcher
   ```

2. **Install the Required Libraries:**
   ```bash
   pip install -r requirements.txt
   ```

### **3. How to Get a GitHub Token**  
You’ll need a GitHub token to access your repos. Here’s how to get one:

1. **Log into GitHub**: Head over to [GitHub](https://github.com) and sign in.
2. **Go to Developer Settings**: Click your profile picture → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
3. **Generate a New Token**:
   - Click **Generate new token**.
   - Give it a name (e.g., “Commit Watcher Token”).
   - Set **Expiration** to something reasonable (e.g., 30 days).
   - Check the **repo** scope (for public repos). For private ones, add `admin:repo_hook` too.
4. **Create the Token**: Hit the button and **copy** the token—don’t lose it!

### **4. Run the Script!**

When you run the script for the first time, it will ask for your GitHub API token and (optionally) your Discord webhook URL. These values will be saved locally in a configuration file (`config.json`), so you only need to enter them **once**.

It will also prompt you to enter the interval (in seconds) for checking new commits when running in background mode.

After the first run, just use the following command to monitor your repo without providing the token or URL again:

```bash
python commit_watcher.py owner_name repo_name --branch branch_name
```

### **Example**:  
If you want to watch the `main` branch of the `my-repo` repository owned by `my-user`, you’d do:

```bash
python commit_watcher.py my-user my-repo --branch main
```

### **5. Running in Background Mode**  
To enable automatic background monitoring of new commits at a specified interval, use the `--background` flag:

```bash
python commit_watcher.py owner_name repo_name --branch branch_name --background
```

You can also set a custom interval for background checks (e.g., every 300 seconds or 5 minutes). Recommended time with a github token is 60 seconds or every minute (github has a rate limit of 5000 with a token and 60 without one <u>per day</u>).

### **6. Custom Configuration**  
If you need to update the token, webhook URL, or interval, you can manually edit the `config.json` file located in the same directory as the script. Just open it in any text editor and update the values.

## **Customize It!**  
You can fine-tune the rules for patterns or sensitive files by editing the `DEFAULT_PATTERNS` and `SENSITIVE_FILES` lists in `commit_watcher.py`.

Here’s a snippet to get you started:

```python
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
```

## **Want to Contribute?**
Got ideas? Found a bug? Open an issue or submit a pull request! Contributions, feedback, and feature requests are all welcome. 💡