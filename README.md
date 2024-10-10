
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
   git clone https://github.com/your_username/commit-watcher.git
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

Now you’re ready to roll. Use this command to monitor your repo:

```bash
python commit_watcher.py owner_name repo_name --branch branch_name --token YOUR_GITHUB_TOKEN
```

### **Example**:  
If you want to watch the `main` branch of `my-repo` owned by `my-user`, you’d do:

```bash
python commit_watcher.py my-user my-repo --branch main --token ghp_1234abcd5678efghijklmnopqrstuvwx
```

### **5. Want to Keep Things Secure?**
Instead of typing the token every time, store it in an environment variable:

1. Set the variable:
   ```bash
   export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
   ```

2. Run the script like this:
   ```bash
   python commit_watcher.py owner_name repo_name --branch branch_name --token $GITHUB_TOKEN
   ```

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

## **License**
This project is under the MIT License. Do whatever you want with it!
