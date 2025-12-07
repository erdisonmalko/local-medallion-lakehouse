#!/usr/bin/env bash

set -euo pipefail

# User configuration
GIT_USERNAME="username"
GIT_EMAIL="user@example.com"
SSH_KEY_PATH="$HOME/.ssh/id_ed25519"

# Configure Git
git config --global user.name "$GIT_USERNAME"
git config --global user.email "$GIT_EMAIL"

echo "Configured Git username and email."

# Generate SSH key
if [ ! -f "$SSH_KEY_PATH" ]; then
    ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$SSH_KEY_PATH" -N ""
    echo "SSH key generated at $SSH_KEY_PATH"
else
    echo "SSH key already exists at $SSH_KEY_PATH, skipping generation."
fi

# Set permissions
chmod 600 "$SSH_KEY_PATH"
chmod 644 "$SSH_KEY_PATH.pub"

# Start SSH agent and add key
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY_PATH"

echo "Private key added to SSH agent."

# Output public key for GitHub
echo "\nCopy this public key to GitHub:"
cat "$SSH_KEY_PATH.pub"

echo "\nTest SSH connection with: ssh -T git@github.com"