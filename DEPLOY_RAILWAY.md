# Deploying to Railway (Docker + Node)

This project is configured for Railway with a root `Dockerfile` and `railway.json`.

## Requirements

- GitHub repository connected to Railway
- Railway account
- Firebase Realtime Database URL
- Firebase service account JSON

`requirements.txt` is **not** used for this Node.js deployment. Railway installs dependencies from `package.json` inside Docker.

## Railway Steps

1. Create a new Railway project from your GitHub repo.
2. Keep default settings; `railway.json` already uses the Dockerfile builder.
3. Add environment variables in Railway:

| Variable | Required | Example |
|---|---|---|
| `PORT` | Auto | `8080` |
| `HOST` | Yes | `0.0.0.0` |
| `CORS_ORIGINS` | Yes | `*` |
| `FIREBASE_DATABASE_URL` | Yes | `https://your-project-default-rtdb.region.firebasedatabase.app` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Yes | raw Firebase service account JSON |

4. Deploy.
5. Open `https://<your-domain>/health` and verify `status: healthy`.

## Notes

- `Dockerfile` runs `npm ci --omit=dev` and starts with `node server.js`.
- `firebase-admin` must be installed in production (already included in `package.json`).
- If `FIREBASE_SERVICE_ACCOUNT_JSON` is invalid or missing, app runs but Firebase RTDB features are disabled.
