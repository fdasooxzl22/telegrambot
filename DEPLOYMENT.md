# Deployment Guide for Automatic Redeploy

This guide explains how automatic redeployment works and how to set it up for your Telegram bot.

## 🎯 Overview

The bot is configured to **automatically redeploy** whenever changes are pushed to the `main` branch using GitHub Actions.

## 📋 What Happens on Push to Main

1. **GitHub Actions triggers** - The workflow `.github/workflows/deploy.yml` starts automatically
2. **Docker image builds** - A new Docker image is created with your latest code
3. **Image is pushed** - (Optional) The image is pushed to Docker Hub
4. **Deployment happens** - The new version is deployed based on your configuration

## 🚀 Quick Start

### Step 1: Get Your Bot Token

1. Open Telegram and find [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Save your bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Configure GitHub Secrets (Optional)

For Docker Hub integration:

1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:
   - `DOCKER_USERNAME` - Your Docker Hub username
   - `DOCKER_PASSWORD` - Your Docker Hub access token
   - `TELEGRAM_BOT_TOKEN` - Your bot token (if deploying via Actions)

### Step 3: Choose Your Deployment Method

## 🔧 Deployment Options

### Option A: Cloud Platform Deployment (Recommended)

#### Render.com (Free Tier Available)
1. Go to [Render.com](https://render.com)
2. Sign in with GitHub
3. Click **New** → **Web Service**
4. Connect your repository
5. Set environment variable:
   - `TELEGRAM_BOT_TOKEN` = your token
6. Click **Create Web Service**
7. ✅ Done! Render will auto-redeploy on every push to main

#### Google Cloud Run
```bash
gcloud run deploy telegrambot \
  --source . \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1
```

Enable automatic deployments:
```bash
gcloud alpha run deploy telegrambot \
  --source . \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token
```

#### Heroku
```bash
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
git push heroku main
```

Enable auto-deploy:
- Go to Deploy tab in Heroku dashboard
- Enable automatic deploys from main branch

### Option B: VPS/Server with Docker

Add this step to `.github/workflows/deploy.yml` after line 66:

```yaml
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/telegrambot
            git pull origin main
            docker-compose down
            docker-compose build
            docker-compose up -d
            docker system prune -f
```

Then add these secrets to GitHub:
- `SERVER_HOST` - Your server IP address
- `SERVER_USER` - SSH username
- `SSH_PRIVATE_KEY` - Your SSH private key

### Option C: Manual Docker Deployment

On your server:

```bash
# Initial setup
git clone https://github.com/fdasooxzl22/telegrambot.git
cd telegrambot
cp .env.example .env
nano .env  # Add your TELEGRAM_BOT_TOKEN

# Start the bot
docker-compose up -d

# For updates (manual redeploy)
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## 🔄 How to Trigger Redeploy

### Automatic (on code change):
```bash
git add .
git commit -m "Update bot"
git push origin main
```
→ GitHub Actions will automatically build and deploy

### Manual trigger (no code changes):
```bash
# Empty commit to trigger redeploy
git commit --allow-empty -m "Trigger redeploy"
git push origin main
```

Or use GitHub UI:
1. Go to **Actions** tab
2. Select "Build and Deploy Telegram Bot"
3. Click **Run workflow** → **Run workflow**

## 📊 Monitoring Deployments

### Check GitHub Actions
1. Go to repository → **Actions** tab
2. View workflow runs and logs
3. See build status and deployment notifications

### Check Logs

**Docker Compose:**
```bash
docker-compose logs -f telegrambot
```

**Cloud Platform:**
- Render: Check Logs tab
- Google Cloud Run: `gcloud run services logs read telegrambot`
- Heroku: `heroku logs --tail`

## 🛠️ Customizing Auto-Deploy

Edit `.github/workflows/deploy.yml` to:

1. **Change trigger conditions:**
```yaml
on:
  push:
    branches:
      - main
      - production  # Add more branches
  pull_request:    # Also trigger on PR
    branches:
      - main
```

2. **Add tests before deploy:**
```yaml
      - name: Run tests
        run: |
          pip install -r requirements.txt
          python -m pytest tests/
```

3. **Add notifications:**
```yaml
      - name: Notify Telegram
        if: success()
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          message: |
            ✅ Deployment successful!
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
```

## ❓ Troubleshooting

### Workflow not triggering
- Check if GitHub Actions is enabled: Settings → Actions → Allow all actions
- Verify workflow file is in `.github/workflows/` directory
- Check workflow syntax with `yamllint .github/workflows/deploy.yml`

### Docker build fails
- Check Dockerfile syntax
- Verify all files are committed
- Review build logs in Actions tab

### Bot not responding after deploy
- Check environment variables are set correctly
- View application logs
- Test bot token with: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### Manual redeploy on server
```bash
cd /path/to/telegrambot
git pull origin main
docker-compose restart
```

## 📝 Best Practices

1. **Always test locally** before pushing to main
2. **Use branches** for development, merge to main for deployment
3. **Monitor logs** after deployment
4. **Set up notifications** to know when deployments succeed/fail
5. **Use secrets** for sensitive data (tokens, passwords)
6. **Tag releases** for easier rollbacks: `git tag v1.0.0 && git push --tags`

## 🔐 Security Notes

- Never commit `.env` file (it's in `.gitignore`)
- Use GitHub Secrets for sensitive data
- Rotate bot token if accidentally exposed
- Review Actions logs for any exposed secrets

## 🎉 Success!

After completing setup, every push to main branch will:
1. ✅ Trigger GitHub Actions workflow
2. ✅ Build new Docker image
3. ✅ Run any tests (if configured)
4. ✅ Deploy to your platform
5. ✅ Send notifications (if configured)

Your bot will automatically stay up-to-date with the latest code!
