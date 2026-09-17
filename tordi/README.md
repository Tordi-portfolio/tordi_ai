# Tordi — Petroleum & Engineering AI Assistant

Tordi is a Django-powered, ChatGPT-style AI assistant focused on petroleum
engineering (and general engineering), with:

- Manual signup/login (username, email, password) **and** Google Sign-In
- Per-user dashboard with a sidebar of saved chats
- New chat creation, chat storage in the database
- Text, image, and voice-note input
- Editing & resending messages, copying message text
- Sidebar chat rename / delete / pin
- A light / dark / brown theme toggle
- Fully responsive, professional UI

It uses **Google's Gemini API** as the underlying AI model, wrapped with a
system instruction that gives it the "Tordi" persona and petroleum-
engineering focus (see `chat/ai_service.py`). Gemini was chosen because its
free tier is generous, so it's less likely your users hit a rate limit
mid-conversation.

---

## Table of contents

1. [Requirements](#1-requirements)
2. [Run it on your local machine](#2-run-it-on-your-local-machine)
3. [Get your Gemini API key](#3-get-your-gemini-api-key)
4. [Get your Google Sign-In (OAuth) credentials](#4-get-your-google-sign-in-oauth-credentials)
5. [Voice notes](#5-voice-notes)
6. [Deploy on PythonAnywhere](#6-deploy-on-pythonanywhere)
7. [Project structure](#7-project-structure)
8. [Notes on pinning](#8-notes-on-pinning)

---

## 1. Requirements

- Python 3.11 or newer
- pip
- A free Google account (for both the Gemini API key and, optionally,
  Google Sign-In)

---

## 2. Run it on your local machine

```bash
# 1. Unzip the project, then move into it
cd tordi

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows (PowerShell): venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file
cp .env.example .env
# Now open .env in a text editor and fill in:
#   - GEMINI_API_KEY   (see section 3 below)
#   - GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET  (see section 4 below, optional)

# 5. Create the database tables
python manage.py migrate

# 6. (Optional) create an admin account so you can view /admin/
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser. You'll land on the login
page — click "Create an account" to sign up manually, or use "Continue with
Google" once step 4 is configured.

To stop the server, press `Ctrl+C` in the terminal. Every time you come
back to work on it, you only need to repeat steps 2 (activate the venv) and
7 (runserver) — steps 3-6 are one-time setup.

---

## 3. Get your Gemini API key

This key is what lets Tordi actually answer questions.

1. Go to **https://aistudio.google.com/app/apikey** (Google AI Studio).
2. Sign in with any Google account.
3. Click **"Create API key"**.
   - If you don't already have a Google Cloud project, choose "Create API
     key in new project" — Google sets everything up for you automatically,
     no separate Cloud Console steps needed.
4. Copy the key shown (it looks like `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`).
5. Paste it into your `.env` file:
   ```
   GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   TORDI_MODEL=gemini-2.5-flash
   ```
6. Restart the server (`Ctrl+C`, then `python manage.py runserver` again)
   so it picks up the new key.

**Which model to use?**
- `gemini-2.5-flash` — fast, cheap, generous free-tier quota. Good default
  for a chat app with many users.
- `gemini-2.5-pro` — stronger reasoning for harder calculations, but slower
  and uses quota faster. Use this if answer quality on tricky reservoir/
  drilling calculations matters more than speed.

**About rate limits:** free Gemini API keys are rate-limited per Google
Cloud *project*, shared across everyone who uses your key (i.e. all of
Tordi's users draw from the same pool) — not per individual user. This is
still generally more generous than most competing APIs' free tiers, which
is why it's the right pick for "so users don't hit limits" — but if Tordi
gets real traffic, keep an eye on usage at
**https://aistudio.google.com/app/apikey** or
**https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas**,
and enable billing on that Cloud project if you need higher throughput.

Until a valid key is set, Tordi will tell users politely that it isn't
configured yet, instead of crashing.

---

## 4. Get your Google Sign-In (OAuth) credentials

This step is only needed for the **"Continue with Google"** button. Manual
signup/login works without it.

1. Go to **https://console.cloud.google.com/apis/credentials**.
   - Use the *same* Google Cloud project your Gemini key belongs to, or a
     different one — either works.
2. If prompted, click **"Configure consent screen"** first:
   - User type: **External** (unless you have a Google Workspace org and
     want it internal-only)
   - Fill in an app name ("Tordi"), your support email, and developer
     contact email, then save through the remaining steps (scopes and test
     users can be left at defaults for development).
3. Back on the Credentials page, click **"+ Create Credentials" → "OAuth
   client ID"**.
4. Application type: **Web application**.
5. Under **Authorized redirect URIs**, add:
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```
   (You'll add your live production URL here too once you deploy — see
   section 6.)
6. Click **Create**. Copy the **Client ID** and **Client secret** shown.
7. Paste them into `.env`:
   ```
   GOOGLE_CLIENT_ID=xxxxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxxxxxxxx
   ```
8. Restart the server. The Google button on the login/signup pages now
   works — Tordi reads these values straight from `.env`
   (`SOCIALACCOUNT_PROVIDERS["google"]["APP"]` in `tordi/settings.py`), so
   there's no extra database setup required.

**Note:** while your OAuth consent screen is in "Testing" mode, only Google
accounts you explicitly add as "test users" (on the consent screen page)
can sign in. Click **"Publish app"** on the consent screen when you're
ready for the general public to use Google Sign-In.

---

## 5. Voice notes

Voice input uses the browser's built-in **Web Speech API**
(`webkitSpeechRecognition`), which works in Chrome/Edge and transcribes
speech to text live, right in the message box — no extra API keys or
server-side processing needed. Firefox/Safari currently don't support this
API; the mic button will show a friendly message in those browsers instead
of failing silently.

If you'd rather do server-side transcription (e.g. with a Whisper-style
model), the raw audio file is already captured server-side — you'd wire it
up in `chat/views.send_message`, where `audio = request.FILES.get("audio")`
is read.

---

## 6. Deploy on PythonAnywhere

PythonAnywhere is a good fit for Tordi because it runs Django out of the
box on a persistent server (unlike serverless platforms, your SQLite
database and uploaded images/audio files persist between requests).

### 6.1 Important: outbound internet access

**Free PythonAnywhere accounts only allow outgoing requests to a
whitelist of sites** — Gemini's API domain (`generativelanguage.
googleapis.com`) is often *not* on that free-tier whitelist, which means
Tordi's AI replies could fail with a network error on a free account, even
though the site itself loads fine. Google Sign-In callbacks and the site
itself will still work. To guarantee Gemini calls work, upgrade to any paid
plan (the **$5/month "Hacker" plan** is enough) — paid plans get
unrestricted outbound internet access. Check PythonAnywhere's current
allowlist under **Account → "Beta" tab → "Web app internet access"** before
deciding.

### 6.2 Upload your project

1. Create a free account at **https://www.pythonanywhere.com** (upgrade
   later if needed, per 6.1).
2. Go to the **Files** tab. Upload `tordi.zip` (zip the project folder
   again if needed) into your home directory, e.g. `/home/yourusername/`.
3. Open a **Bash console** (Consoles tab → "Bash") and unzip it:
   ```bash
   cd ~
   unzip tordi.zip
   cd tordi
   ```

### 6.3 Create a virtual environment and install dependencies

Still in the Bash console:
```bash
mkvirtualenv --python=python3.11 tordi-venv
pip install -r requirements.txt
```
(`mkvirtualenv` is a PythonAnywhere helper that also activates the venv.
If you open a new console later, reactivate with `workon tordi-venv`.)

### 6.4 Configure environment variables

```bash
cp .env.example .env
nano .env
```
Fill in `SECRET_KEY` (any long random string), `DEBUG=False`,
`ALLOWED_HOSTS=yourusername.pythonanywhere.com`, your `GEMINI_API_KEY`, and
your `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` if using Google Sign-In.
Save with `Ctrl+O`, then `Ctrl+X` to exit nano.

### 6.5 Run migrations and collect static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6.6 Create the web app

1. Go to the **Web** tab → **"Add a new web app"**.
2. Choose **"Manual configuration"** (not the Django wizard) and pick the
   same Python version as your virtualenv (3.11).
3. Under **Virtualenv**, enter the path PythonAnywhere printed when you ran
   `mkvirtualenv`, typically:
   ```
   /home/yourusername/.virtualenvs/tordi-venv
   ```
4. Under **Code**, set:
   - **Source code**: `/home/yourusername/tordi`
   - **Working directory**: `/home/yourusername/tordi`
5. Click the **WSGI configuration file** link and replace its contents
   with:
   ```python
   import os
   import sys

   path = '/home/yourusername/tordi'
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ['DJANGO_SETTINGS_MODULE'] = 'tordi.settings'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
   (replace `yourusername` with your actual PythonAnywhere username)
6. Under **Static files**, add two mappings:
   | URL | Directory |
   |---|---|
   | `/static/` | `/home/yourusername/tordi/staticfiles` |
   | `/media/` | `/home/yourusername/tordi/media` |
7. Click the big green **Reload** button at the top of the Web tab.

### 6.7 Update your redirect URIs

Back in Google Cloud Console (section 4), add your live URL to both:
- OAuth **Authorized redirect URIs**:
  `https://yourusername.pythonanywhere.com/accounts/google/login/callback/`
- Your app's OAuth consent screen domain settings, if prompted.

### 6.8 Visit your site

`https://yourusername.pythonanywhere.com` — Tordi is now live.

**Whenever you change code**: re-upload/edit the files, then click
**Reload** on the Web tab again (PythonAnywhere doesn't auto-restart on
file changes).

---

## 7. Project structure

```
tordi/
├── tordi/            # Django project settings, root urls
├── accounts/         # Custom user model, signup/login/logout, theme prefs
├── chat/             # Conversation & Message models, chat views, AI service
├── templates/        # base.html, auth pages, chat dashboard
├── static/css/       # styles.css — all 3 themes (light/dark/brown)
├── static/js/        # app.js — chat, uploads, voice, theme toggle logic
├── media/            # uploaded images/audio (created at runtime)
├── requirements.txt
└── .env.example
```

---

## 8. Notes on pinning

The sidebar's pin button pins a chat for the logged-in user viewing it
(each user only ever sees and manages their own conversations — that's the
standard, secure way to do "my saved chats", same as ChatGPT). If you
specifically want a chat pinned globally so *every* user sees it pinned in
their sidebar, that would need a small model change (a shared/broadcast
conversation type) — just ask if that's what you actually meant.
