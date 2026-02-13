"""
Telegram Bot for Solana Wallet Copy Trading Analysis
Helps users analyze if a SOL wallet is worth copy trading
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

from sol_analyzer import SolanaWalletAnalyzer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize analyzer
analyzer = SolanaWalletAnalyzer()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = """
👋 Добро пожаловать в Solana Wallet Analyzer Bot!

Этот бот помогает анализировать Solana кошельки для копитрейдинга.

📝 **Команды**:
/start - Показать это сообщение
/help - Справка по использованию
/analyze <адрес> - Анализировать кошелек

💡 **Как использовать**:
1. Используйте команду `/analyze` с адресом кошелька
2. Или просто отправьте адрес кошелька

**Пример**:
`/analyze 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`

⚠️ Бот анализирует:
• Историю транзакций
• Торговую активность
• Баланс кошелька
• Стабильность торговли

И предоставляет рекомендацию, стоит ли копитрейдить этот кошелек.
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
📖 **СПРАВКА**

**Как анализировать кошелек**:
1. Используйте команду: `/analyze <адрес_кошелька>`
2. Или просто отправьте адрес кошелька (44 символа)

**Пример**:
`/analyze 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`

**Что анализирует бот**:
• Количество транзакций
• Период активности
• Частоту торговли
• Текущий баланс SOL
• Последнюю активность

**Оценка кошелька**:
🟢 70-100: Рекомендуется для копитрейдинга
🟡 40-69: Средняя перспективность
🔴 0-39: Не рекомендуется

⚠️ **Важно**: Всегда проводите дополнительное исследование перед копитрейдингом!
"""
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def analyze_wallet_command(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Analyze a Solana wallet when /analyze command is issued."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Пожалуйста, укажите адрес кошелька.\n\n"
            "**Пример**: `/analyze 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    wallet_address = context.args[0]
    await analyze_wallet(update, wallet_address)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages that might be wallet addresses."""
    text = update.message.text.strip()
    
    # Check if the message looks like a Solana wallet address (base58, ~44 chars)
    if len(text) >= 32 and len(text) <= 44 and text.replace(' ', '').isalnum():
        await analyze_wallet(update, text)
    else:
        await update.message.reply_text(
            "🤔 Не распознан как адрес кошелька.\n\n"
            "Используйте `/analyze <адрес>` или отправьте корректный адрес Solana кошелька.",
            parse_mode=ParseMode.MARKDOWN
        )


async def analyze_wallet(update: Update, wallet_address: str) -> None:
    """Perform wallet analysis and send results."""
    # Send "analyzing" message
    processing_msg = await update.message.reply_text(
        f"🔍 Анализирую кошелек `{wallet_address[:8]}...{wallet_address[-8:]}`\n"
        "⏳ Пожалуйста, подождите...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Generate analysis report
        report = await analyzer.generate_analysis_report(wallet_address)
        
        # Send the report
        await processing_msg.edit_text(
            report,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error analyzing wallet: {e}")
        await processing_msg.edit_text(
            f"❌ Ошибка при анализе кошелька:\n{str(e)}\n\n"
            "Пожалуйста, проверьте адрес и попробуйте снова.",
            parse_mode=ParseMode.MARKDOWN
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )


async def shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    await analyzer.close()


def main() -> None:
    """Start the bot."""
    # Get token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analyze", analyze_wallet_command))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Register shutdown handler
    application.post_shutdown = shutdown
    
    # Start the bot
    logger.info("Starting Solana Wallet Analyzer Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
