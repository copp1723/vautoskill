#!/bin/bash

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit of vAuto Feature Verification System"

# Add remote repository
git remote add origin https://github.com/copp1723/vautoskill.git

# Set branch to main
git branch -M main

# Push to GitHub
git push -u origin main

echo "Repository initialized and pushed to GitHub!"
