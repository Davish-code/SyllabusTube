# Google Cloud & API Keys Setup Guide

SyllabusTube requires Google Cloud credentials for two functions:
1. **Gemini API Key**: Powers syllabus parsing, OCR fallback, and video match verification.
2. **YouTube Data API v3 Key**: Queries YouTube search, video details, and playlists.
3. **OAuth 2.0 Client Credentials (`client_secret.json`)**: Required if you want to export generated playlists directly to your YouTube account.

---

## 1. Get a Gemini API Key

1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and create a key in a new or existing Google Cloud project.
3. Copy your key and add it to `.env`:
   ```env
   GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
   ```

---

## 2. Set Up Google Cloud Project & YouTube Data API v3

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `SyllabusTube`).
3. In the left navigation, go to **APIs & Services** > **Library**.
4. Search for **YouTube Data API v3** and click **Enable**.

### Create API Key
1. Go to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **API key**.
3. (Recommended) Click **Edit API key**, rename to `YouTube API Key`, and restrict the key to **YouTube Data API v3**.
4. Add the key to `.env`:
   ```env
   YOUTUBE_API_KEY=AIzaSyYourYouTubeApiKeyHere
   ```

---

## 3. Configure OAuth 2.0 for YouTube Playlist Export

If you plan to export playlists directly to your YouTube channel:

### Configure OAuth Consent Screen
1. Go to **APIs & Services** > **OAuth consent screen**.
2. Select User Type: **External** and click **Create**.
3. Fill in required App name (`SyllabusTube`) and your support email.
4. Under **Scopes**, click **Add or Remove Scopes** and select:
   - `https://www.googleapis.com/auth/youtube` (or `https://www.googleapis.com/auth/youtube.force-ssl`).
5. Under **Test users**, click **Add Users** and add your own Google email address.
   > **Note on Token Expiry**: Projects in "Testing" mode have refresh tokens that expire after **7 days**. When expired, the CLI or UI will prompt you to log in again via your browser.

### Create Desktop Client Credentials
1. Go to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **OAuth client ID**.
3. Set Application type to **Desktop app**.
4. Enter Name: `SyllabusTube Desktop`.
5. Click **Create**, then click **Download JSON**.
6. Save the downloaded file as `client_secret.json` in the root of the SyllabusTube repository.

---

## 4. Keep Secrets Out of Git

- `.env`, `client_secret.json`, and `token.json` are listed in `.gitignore`.
- Run diagnostics to confirm your setup:
  ```bash
  python main.py --check-setup
  ```

