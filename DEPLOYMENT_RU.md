# Руководство по Автоматическому Редеплою

Это руководство объясняет, как работает автоматический редеплой и как настроить его для вашего Telegram бота.

## 🎯 Обзор

Бот настроен на **автоматический редеплой** при любых изменениях в ветке `main` через GitHub Actions.

## 📋 Что Происходит при Push в Main

1. **Запускается GitHub Actions** - Автоматически стартует workflow `.github/workflows/deploy.yml`
2. **Собирается Docker образ** - Создается новый Docker образ с последним кодом
3. **Загружается образ** - (Опционально) Образ загружается в Docker Hub
4. **Происходит деплой** - Новая версия разворачивается согласно вашей конфигурации

## 🚀 Быстрый Старт

### Шаг 1: Получите Токен Бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot` и следуйте инструкциям
3. Сохраните токен бота (выглядит как: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Настройте GitHub Secrets (Опционально)

Для интеграции с Docker Hub:

1. Перейдите в ваш репозиторий на GitHub
2. Откройте: **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте эти секреты:
   - `DOCKER_USERNAME` - Ваше имя пользователя Docker Hub
   - `DOCKER_PASSWORD` - Токен доступа Docker Hub
   - `TELEGRAM_BOT_TOKEN` - Токен вашего бота (если деплоите через Actions)

### Шаг 3: Выберите Метод Деплоя

## 🔧 Варианты Деплоя

### Вариант A: Деплой на Облачную Платформу (Рекомендуется)

#### Render.com (Есть бесплатный тариф)
1. Перейдите на [Render.com](https://render.com)
2. Войдите через GitHub
3. Нажмите **New** → **Web Service**
4. Подключите ваш репозиторий
5. Установите переменную окружения:
   - `TELEGRAM_BOT_TOKEN` = ваш токен
6. Нажмите **Create Web Service**
7. ✅ Готово! Render будет автоматически делать редеплой при каждом push в main

#### Google Cloud Run
```bash
gcloud run deploy telegrambot \
  --source . \
  --set-env-vars TELEGRAM_BOT_TOKEN=ваш_токен \
  --platform managed \
  --allow-unauthenticated \
  --region us-central1
```

Включить автоматические деплои:
```bash
gcloud alpha run deploy telegrambot \
  --source . \
  --set-env-vars TELEGRAM_BOT_TOKEN=ваш_токен
```

#### Heroku
```bash
heroku create имя-вашего-бота
heroku config:set TELEGRAM_BOT_TOKEN=ваш_токен
git push heroku main
```

Включить авто-деплой:
- Перейдите на вкладку Deploy в панели Heroku
- Включите automatic deploys из ветки main

### Вариант B: VPS/Сервер с Docker

Добавьте этот шаг в `.github/workflows/deploy.yml` после строки 66:

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

Затем добавьте эти секреты в GitHub:
- `SERVER_HOST` - IP адрес вашего сервера
- `SERVER_USER` - Имя пользователя SSH
- `SSH_PRIVATE_KEY` - Ваш приватный SSH ключ

### Вариант C: Ручной Docker Деплой

На вашем сервере:

```bash
# Начальная настройка
git clone https://github.com/fdasooxzl22/telegrambot.git
cd telegrambot
cp .env.example .env
nano .env  # Добавьте ваш TELEGRAM_BOT_TOKEN

# Запуск бота
docker-compose up -d

# Для обновлений (ручной редеплой)
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## 🔄 Как Запустить Редеплой

### Автоматически (при изменении кода):
```bash
git add .
git commit -m "Обновление бота"
git push origin main
```
→ GitHub Actions автоматически соберет и задеплоит

### Ручной запуск (без изменения кода):
```bash
# Пустой коммит для запуска редеплоя
git commit --allow-empty -m "Триггер редеплоя"
git push origin main
```

Или через интерфейс GitHub:
1. Перейдите на вкладку **Actions**
2. Выберите "Build and Deploy Telegram Bot"
3. Нажмите **Run workflow** → **Run workflow**

## 📊 Мониторинг Деплоев

### Проверка GitHub Actions
1. Перейдите в репозиторий → вкладка **Actions**
2. Просмотрите запуски workflow и логи
3. Увидите статус сборки и уведомления о деплое

### Проверка Логов

**Docker Compose:**
```bash
docker-compose logs -f telegrambot
```

**Облачная Платформа:**
- Render: Вкладка Logs
- Google Cloud Run: `gcloud run services logs read telegrambot`
- Heroku: `heroku logs --tail`

## 🛠️ Настройка Авто-Деплоя

Отредактируйте `.github/workflows/deploy.yml` чтобы:

1. **Изменить условия запуска:**
```yaml
on:
  push:
    branches:
      - main
      - production  # Добавить больше веток
  pull_request:    # Также запускать на PR
    branches:
      - main
```

2. **Добавить тесты перед деплоем:**
```yaml
      - name: Run tests
        run: |
          pip install -r requirements.txt
          python -m pytest tests/
```

3. **Добавить уведомления:**
```yaml
      - name: Notify Telegram
        if: success()
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_CHAT_ID }}
          token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          message: |
            ✅ Деплой успешен!
            Коммит: ${{ github.sha }}
            Автор: ${{ github.actor }}
```

## ❓ Решение Проблем

### Workflow не запускается
- Проверьте, включен ли GitHub Actions: Settings → Actions → Allow all actions
- Убедитесь, что файл workflow находится в `.github/workflows/`
- Проверьте синтаксис workflow: `yamllint .github/workflows/deploy.yml`

### Ошибка сборки Docker
- Проверьте синтаксис Dockerfile
- Убедитесь, что все файлы закоммичены
- Посмотрите логи сборки во вкладке Actions

### Бот не отвечает после деплоя
- Проверьте правильность переменных окружения
- Посмотрите логи приложения
- Проверьте токен бота: `curl https://api.telegram.org/bot<ТОКЕН>/getMe`

### Ручной редеплой на сервере
```bash
cd /путь/к/telegrambot
git pull origin main
docker-compose restart
```

## 📝 Лучшие Практики

1. **Всегда тестируйте локально** перед push в main
2. **Используйте ветки** для разработки, сливайте в main для деплоя
3. **Мониторьте логи** после деплоя
4. **Настройте уведомления** чтобы знать об успехе/провале деплоя
5. **Используйте секреты** для конфиденциальных данных (токены, пароли)
6. **Делайте теги релизов** для удобного отката: `git tag v1.0.0 && git push --tags`

## 🔐 Заметки по Безопасности

- Никогда не коммитьте файл `.env` (он в `.gitignore`)
- Используйте GitHub Secrets для конфиденциальных данных
- Меняйте токен бота при случайной утечке
- Проверяйте логи Actions на наличие раскрытых секретов

## 🎉 Успех!

После завершения настройки, каждый push в ветку main будет:
1. ✅ Запускать GitHub Actions workflow
2. ✅ Собирать новый Docker образ
3. ✅ Запускать тесты (если настроены)
4. ✅ Деплоить на вашу платформу
5. ✅ Отправлять уведомления (если настроены)

Ваш бот будет автоматически обновляться с последним кодом!
