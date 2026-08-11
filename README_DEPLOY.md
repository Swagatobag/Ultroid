Ultroid Runny deploy notes

Files added in this branch:
- Dockerfile: builds a minimal image with ffmpeg and installs python deps.
- runny.yaml: Runny.ai descriptor asking only for API_ID, API_HASH and SESSION as required secrets.
- .env.sample: placeholders only, safe to commit.

Deployment steps:
1. In Runny dashboard, create a new project and connect your GitHub repo (Swagatobag/Ultroid) and select the runny/deploy branch.
2. Add the following secrets in Runny project settings: API_ID, API_HASH, SESSION. Do NOT add them to the repo.
3. Trigger build/deploy in Runny. Monitor logs for missing optional dependencies or build issues.

Notes:
- With DB env vars absent, Ultroid will use the local file DB (localdb). For persistence, configure a volume mount in Runny or use an external DB
- I have not included any secrets in this commit.
