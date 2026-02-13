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
| `PORT` | `8000` | Railway sets this automatically |
| `HOST` | `0.0.0.0` | Required for visibility |
| `FIREBASE_PROJECT_ID` | `sample-music-65323` | Your Firebase Project ID |
| `FIREBASE_DATABASE_URL` | `...` | Your RTDB URL |
| `CORS_ORIGINS` | `*` | Allow all origins |

### 🔑 Critical: Firebase Credentials

The backend now supports reading your service account key directly from environment variables. **No file system hacks required.**

Update your **Start Command** in Railway Settings to (or leave it to use the `Procfile`):
```bash
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

### How to set the Credentials Variable:
Add the variable **`FIREBASE_SERVICE_ACCOUNT_JSON`** with the **raw content** of your `firebase-service-account.json`.

> [!TIP]
> If your JSON content causes issues in the dashboard dashboard, encode it to Base64 first and use the variable name **`FIREBASE_SERVICE_ACCOUNT_BASE64`** instead.

## Step 3: Verify Deployment

1.  Go to **Settings** > **Networking**.
2.  Click **Generate Domain** to get a public URL (e.g., `music-hub-production.up.railway.app`).
3.  Visit `https://<your-url>/health` to confirm it's running.

---

## Troubleshooting

- **`Firebase initialization failed: Invalid certificate`**: Ensure you copied the FULL content of the Service Account key (starts with `{ "type": "service_account" ... }`). **Do NOT use `google-services.json`**.
- **`App crashed`**: Check the "Deploy Logs" tab in Railway.
- **`403 Forbidden`**: Check your Firebase Rules (RTDB must be open to valid authenticated users).
