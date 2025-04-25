#!/bin/bash
# Script to initialize Git repository for the vAuto Feature Verification System

echo "Initializing Git repository for vAuto Feature Verification System..."

# Initialize Git repository
git init

# Add all files
git add .

echo "Files added to Git staging area."
echo ""
echo "Please enter your Git username:"
read USERNAME

echo "Please enter your Git email:"
read EMAIL

# Configure Git user
git config user.name "$USERNAME"
git config user.email "$EMAIL"

echo "Git user configured successfully."

# Create initial commit
git commit -m "Initial project setup"

echo "Initial commit created successfully."
echo ""
echo "Would you like to connect to a remote repository? (y/n)"
read REMOTE

if [ "$REMOTE" = "y" ] || [ "$REMOTE" = "Y" ]; then
    echo "Please enter the remote repository URL:"
    read REMOTE_URL
    
    git remote add origin $REMOTE_URL
    git branch -M main
    git push -u origin main
    
    echo "Repository connected to remote and pushed successfully."
fi

echo ""
echo "Git initialization complete!"
echo "Next steps are detailed in SETUP.md"
