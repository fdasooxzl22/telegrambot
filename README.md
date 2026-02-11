# Telegram Bot

Simple Telegram echo bot with automatic deployment on push to main branch.

## Features

- 🤖 Echo bot - responds to messages
- 🔄 Automatic deployment via GitHub Actions when main branch is updated
- 🐳 Docker containerization for easy deployment
- 📝 Logging and error handling

## Prerequisites

- Python 3.11+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- Docker and Docker Compose (optional, for containerized deployment)

## Setup

### 1. Get a Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### 2. Local Development

```bash
# Clone the repository
git clone https://github.com/fdasooxzl22/telegrambot.git
cd telegrambot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your token
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN

# Run the bot
python bot.py
```

### 3. Docker Deployment

```bash
# Copy environment template
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN

# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## Automatic Deployment

The bot is configured for automatic deployment through GitHub Actions.

### How it works:

1. **Push to main branch** → Automatically triggers the deployment workflow
2. **GitHub Actions** builds the Docker image
3. **Docker Hub** (optional) receives the new image
4. **Deployment** happens automatically (customize in `.github/workflows/deploy.yml`)

### Setup GitHub Actions Deployment:

1. **Add Docker Hub credentials** (optional, for pushing images):
   - Go to repository Settings → Secrets and variables → Actions
   - Add `DOCKER_USERNAME` - your Docker Hub username
   - Add `DOCKER_PASSWORD` - your Docker Hub access token

2. **Customize deployment** in `.github/workflows/deploy.yml`:
   - Add SSH deployment to your server
   - Configure cloud platform deployment (Google Cloud Run, AWS, Render, etc.)
   - Add webhook notifications

### Manual Redeploy Triggers:

1. **Push any change to main branch**:
   ```bash
   git commit --allow-empty -m "Trigger redeploy"
   git push origin main
   ```

2. **Use GitHub Actions UI**:
   - Go to Actions tab → Select "Build and Deploy Telegram Bot"
   - Click "Run workflow" button

3. **Update on your server** (if using Docker):
   ```bash
   cd /path/to/telegrambot
   git pull origin main
   docker-compose pull
   docker-compose up -d
   ```

## Bot Commands

- `/start` - Start the bot and see welcome message
- `/help` - Display help information
- Send any text message - Bot will echo it back

## Configuration

Environment variables:
- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather (required)

## Project Structure

```
telegrambot/
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions workflow for automatic deployment
├── bot.py                  # Main bot application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Docker Compose configuration
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Deployment Options

### Option 1: Docker on VPS/Server

```bash
# On your server
git clone https://github.com/fdasooxzl22/telegrambot.git
cd telegrambot
cp .env.example .env
# Edit .env with your token
docker-compose up -d
```

### Option 2: Cloud Platforms

#### Google Cloud Run
```bash
gcloud run deploy telegrambot \
  --source . \
  --set-env-vars TELEGRAM_BOT_TOKEN=your_token \
  --allow-unauthenticated
```

#### AWS ECS/Fargate
- Push Docker image to ECR
- Create ECS task definition with environment variables
- Deploy service with task definition

#### Render
- Connect GitHub repository
- Set environment variable `TELEGRAM_BOT_TOKEN`
- Auto-deploys on push to main

### Option 3: GitHub Actions with SSH

Add to `.github/workflows/deploy.yml`:

```yaml
- name: Deploy to server
  uses: appleboy/ssh-action@master
  with:
    host: ${{ secrets.SERVER_HOST }}
    username: ${{ secrets.SERVER_USERNAME }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      cd /path/to/telegrambot
      git pull origin main
      docker-compose pull
      docker-compose up -d
```

## Troubleshooting

### Bot doesn't respond
- Check if bot token is correct in `.env`
- Verify bot is running: `docker-compose ps`
- Check logs: `docker-compose logs -f`

### Deployment not triggering
- Verify GitHub Actions is enabled in repository settings
- Check workflow file syntax
- View Actions tab for workflow run details

### Docker issues
- Ensure Docker daemon is running
- Check port conflicts
- Verify environment variables are set

## Contributing

Feel free to open issues or submit pull requests!

## License

MIT License - feel free to use this project as you wish.
