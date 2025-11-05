# Google Drive Integration Setup

## ⚠️ IMPORTANT: Service Account Limitation

**Service accounts cannot upload to regular Google Drive folders** due to storage quota restrictions. You have two options:

1. **Recommended**: Use **Shared Drives** (Google Workspace only)
2. **Alternative**: Use OAuth with a personal Google account (more complex)

This guide covers the Shared Drive approach.

## Overview
The ACE app can automatically upload completed and partial responses to Google Drive for your team's access. This happens silently in the background - users continue to download their responses normally.

## Setup Steps

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Drive API:
   - Go to APIs & Services > Library
   - Search for "Google Drive API"
   - Click Enable

### 2. Create Service Account
1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "Service Account"
3. Name it "ACE-Bot-Service-Account"
4. Create a key (JSON format)
5. Download the JSON file

### 3. Share Drive Folder
1. Create a folder in your Google Drive called "ACE_Responses"
2. Right-click > Share
3. Add the service account email (from the JSON file) with Editor permissions
4. Copy the folder ID from the URL (e.g., `1abc123def456...`)

### 4. Configure Environment
Add to your `.env` file:
```
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project",...}
```

## File Structure
The app creates this structure automatically:
```
ACE_Responses/
├── completed/
│   ├── CompanyName_20240918_1430_Summary.md
│   ├── CompanyName_20240918_1430_Transcript.csv
│   └── CompanyName_20240918_1430_Audit.json
└── incomplete responses/
    └── CompanyName_20240918_1445_Partial.json
```

## Alternative: Service Account File
Instead of JSON in .env, you can place the JSON file as `service_account.json` in the project root.

## Testing
Run the app - if Google Drive is configured correctly, you'll see debug messages in the console:
```
DEBUG: Google Drive service initialized successfully
DEBUG: Folders ready - completed: xyz, incomplete: abc
DEBUG: Uploaded 3/3 files to Google Drive
```

## Troubleshooting
- Check service account has Drive API access
- Verify folder is shared with service account email
- Ensure folder ID is correct (from Drive URL)
- Check debug messages in console output