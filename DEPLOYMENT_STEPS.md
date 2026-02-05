# 🚀 Step-by-Step Guide: Deploy & Win!

Follow these exact steps to deploy your Agentic Honeypot and pass the GUVI verification.

---

## 🏗️ Phase 1: Deployment (Hugging Face Spaces)

This puts your code on the internet so GUVI can access it.

1.  **Create Space**:
    *   Go to [Hugging Face Spaces](https://huggingface.co/spaces)
    *   Click **"Create new Space"**
    *   **Name**: `agentic-honeypot` (or similar)
    *   **SDK**: Select **Docker**
    *   **Visibility**: Public

2.  **Upload Files**:
    *   Go to the **"Files"** tab of your new Space.
    *   Upload **ALL** files from your `honeypot` folder:
        *   `Dockerfile`
        *   `requirements.txt`
        *   Directory `app/` (with `main.py`, `schemas.py`, etc.)

3.  **Set Secrets (Environment Variables)**:
    *   Go to **"Settings"** tab -> **"Variables and secrets"**
    *   Add **New Secret**:
        *   Key: `API_KEY`
        *   Value: `my-super-secret-key-123` (or whatever you want)
    *   Add **New Secret**:
        *   Key: `GEMINI_API_KEY`
        *   Value: `your-google-gemini-key`


---

## 🐙 Method 2: Deploy via GitHub (Recommended)

This connects your GitHub repo to Hugging Face for automatic updates.

### 1. Prepare Your Code
1.  **Initialize Git** (run in terminal):
    ```bash
    git init
    git add .
    git commit -m "Initial commit of Agentic Honeypot"
    ```
    *(Note: I've already created a `.gitignore` file so your passwords won't be uploaded!)*

2.  **Push to GitHub**:
    *   Create a new repository on [GitHub.com](https://github.com/new).
    *   Run the commands shown by GitHub to push your code:
        ```bash
        git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
        git branch -M main
        git push -u origin main
        ```

### 2. Connect to Hugging Face
1.  Create a **New Space** on Hugging Face.
2.  Select **"Docker"** as the SDK.
3.  Under **"Source"**, select **"GitHub"**.
    *   Authorize Hugging Face to see your repos.
    *   Select your `honeypot` repo.
4.  **Important**: If your `Dockerfile` is inside the `honeypot/` folder (not at the very top), you must go to **Settings** -> **Dockerfile Path** and change it to `honeypot/`.

### 3. Set Secrets
*   Don't forget to go to **Settings** -> **Variables and secrets** and add:
    *   `API_KEY`
    *   `GEMINI_API_KEY`

---

## 🧪 Phase 2: Testing (GUVI Verification)

Now verify it works using the GUVI Tester tool.

1.  **Get Your URL**:
    *   Your URL will look like: `https://<username>-agentic-honeypot.hf.space`
    *   **Add the endpoint path**: `/api/v1/guvi-honeypot`
    *   **Final URL**: `https://<username>-agentic-honeypot.hf.space/api/v1/guvi-honeypot`

2.  **Enter Details in Tester**:
    *   **Endpoint URL**: (Paste the Final URL from above)
    *   **API Key**: `my-super-secret-key-123` (Must match what you set in Secrets)

3.  **Click "Test Honeypot Endpoint"**

---

## ✅ Phase 3: What Success Looks Like

If successful:
*   The tester will show a **Success** message.
*   It means your API accepted the message and responded correctly.
*   Your API is now **LIVE** and ready for the automated evaluation!

---

## 🆘 Troubleshooting

*   **Tester says "Failed to Custom Fetch"**:
    *   Check if your Space is **Running** (Green).
    *   Check if your **API Key** matches exactly.
    *   Make sure you added `/api/v1/guvi-honeypot` to the URL.

*   **Tester says "CORS Error"**:
    *   We already fixed this! Make sure you uploaded the latest `main.py`.

**Good luck! Go get that win! 🏆**
