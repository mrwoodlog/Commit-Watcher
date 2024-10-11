
# **Commit Watcher**

Welcome to **Commit Watcher**! 🎉  
This is a lightweight tool that keeps an eye on your GitHub repository to make sure no one’s accidentally leaking secrets or making suspicious changes. It scans for risky patterns like sensitive keywords (`password`, `token`), sketchy file types (`.env`, `.pem`), or code changes that look... a bit off.

### Why should you use it?  
You know that feeling when you push a commit and realize you accidentally added an API key? 🫠 Commit Watcher helps catch those mistakes *before* they become a problem. It’s like a safety net for your repos!

## **Cool Features**
- **Pattern Detection:** Spots keywords like `password` or `api_key` in commit messages or diffs.
- **Sensitive File Monitoring:** Alerts you if files like `.env` or `.pem` are added.
- **Code Smell Detection:** Flags big, unusual code changes (e.g., hundreds of lines added or deleted).
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

After the first run, just use the following command to monitor your repo without providing the token again:

```bash
python commit_watcher.py owner_name repo_name --branch branch_name
```

### **Example**:  
If you want to watch the `main` branch of the `my-repo` repository owned by `my-user`, you’d do:

```bash
python commit_watcher.py my-user my-repo --branch main
```

You can test this project on the `test-commit-watcher` repo:

```bash
python commit_watcher.py mrwoodlog test-commit-checker --branch main
```

### **5. Custom Configuration**  
If you need to update the token or webhook URL, you can manually edit the `config.json` file located in the same directory as the script. Just open it in any text editor and update the values.

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