# Deploying Music Hub Backend to Railway

Railway is the recommended hosting platform for this project because it offers **simple setup**, **generous free usage**, and **seamless GitHub integration**.

## Prerequisites
1.  A [GitHub account](https://github.com/) with this repository pushed.
2.  A [Railway account](https://railway.app/).
3.  Your `firebase-service-account.json` file content.

---

## Step 1: Create Project on Railway

1.  Log in to [Railway](https://railway.app/).
2.  Click **New Project** > **Deploy from GitHub repo**.
3.  Select your repository: `music-hub-backend`.
4.  Click **Deploy Now**. Only the default settings are needed initially.

## Step 2: Configure Environment Variables

The deployment will fail initially because credentials are missing. Fix this by adding variables.

1.  Go to your project dashboard on Railway.
2.  Click heavily on the **Variables** tab.
3.  Add the following variables (copy values from your local `.env`):

| Variable | Value | Description |
|---|---|---|
| `PORT` | `8000` | Railway sets this automatically, but good to add |
| `HOST` | `0.0.0.0` | Required for Docker/Nixpacks visibility |
| `FIREBASE_PROJECT_ID` | `sample-music-65323` | Your Firebase Project ID |
| `FIREBASE_DATABASE_URL` | `...` | Your RTDB URL |
| `CORS_ORIGINS` | `*` | Allow all origins (or your frontend URL) |

### ⚠️ Critical: Firebase Credentials

Railway cannot read your local JSON file. You must provide the file content via a variable.

1.  **Option A: Base64 Encoded (Recommended)**
    - Run this locally: `base64 -w 0 firebase-service-account.json`
    - Copy the output string.
    - Create a variable `FIREBASE_CREDENTIALS_BASE64` with this value.
    - *Note: Backend code needs update to support this. See below.*

2.  **Option B: Raw Content (Simpler)**
    - Copy the **entire content** of `firebase-service-account.json`.
    - Create a variable `FIREBASE_SERVICE_ACCOUNT_JSON` with this value.
    - *Note: Backend code needs update to support this.*

**Since our code currently looks for a file path**, we need a small tweak to write this variable to a file on startup.

### Quick Fix for File-Based Auth
Add this `Pre-Deploy Command` in Railway Settings > Build:
```bash
echo $FIREBASE_SERVICE_ACCOUNT_JSON > firebase-service-account.json
```
*Note: This might expose credentials in build logs. Be careful.*

**Better Approach (Safe):**
Use `echo "$FIREBASE_SERVICE_ACCOUNT_JSON" > /app/firebase-service-account.json` in the start command.

Update your `Procfile` or Start Command in Railway to:
```bash
echo "$FIREBASE_SERVICE_ACCOUNT_JSON" > firebase-service-account.json && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```
And add the variable `FIREBASE_SERVICE_ACCOUNT_JSON` with the file contents.

## Step 3: Verify Deployment

1.  Go to **Settings** > **Networking**.
2.  Click **Generate Domain** to get a public URL (e.g., `music-hub-production.up.railway.app`).
3.  Visit `https://<your-url>/health` to confirm it's running.

---

## Troubleshooting

- **`500 Internal Server Error`**: Likely missing `firebase-service-account.json`. Check logs.
- **`App crashed`**: Check the "Deploy Logs" tab.
- **Slow specific endpoints**: Cold starts or rate limits. Railway prevents cold starts on paid plans.
