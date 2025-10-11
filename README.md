# Flask Full-Featured Blog

This is a full-featured Flask blogging platform (Linda-Ikeji-inspired) scaffolded with many features:
- Authentication (users, admin)
- Posts with media (image/video/audio)
- Categories & Tags
- Drafts & scheduled publishing
- Comments with edit/delete and moderation
- Search, pagination, related posts, views counter
- Admin dashboard, REST API endpoints
- Dockerfile + docker-compose (example)


**Note:** Some features (email, analytics) require external services/configuration. See `.env.example`.

Run locally:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
export FLASK_ENV=development
flask db upgrade  # after configuring DB
flask run
```
Default admin created on first run: `admin@example.com` / `adminpass123`
