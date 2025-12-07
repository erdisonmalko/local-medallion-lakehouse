# GitHub SSH Setup Guide

This document contains detailed steps for setting up SSH access to a GitHub repository, along with a script to automate key creation and configuration. Use the script with caution, as it generates and modifies SSH keys.

---

## **Step-by-Step Instructions**

### 1. Configure Git with your identity

```bash
# Set your Git username
git config --global user.name "username"

# Set your Git email
git config --global user.email "username@gmail.com"

# Verify the configuration
git config --list
```

### 2. Generate an SSH key pair

```bash
ssh-keygen -t ed25519 -C "username@gmail.com"
```

- Accept the default path when prompted.
- Optionally set a passphrase.

### 3. Set correct permissions on the keys

```bash
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

### 4. Add the private key to the SSH agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 5. Add your public key to GitHub

1. Copy the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

2. Go to GitHub → **Settings → SSH and GPG keys → New SSH key**.
3. Paste the key and give it a title.
4. Click **Add SSH key**.

### 6. Test the SSH connection

```bash
ssh -T git@github.com
```

Expected message:
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### 7. Change Git remote to SSH

```bash
git remote set-url origin git@github.com:username/repo.git
```

### 8. Push / Pull with SSH

```bash
git push origin develop
git pull origin develop
```