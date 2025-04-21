import logging
from pathlib import Path
import sys

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
except Exception as e:
    print(f"Error adjusting sys.path: {e}.", file=sys.stderr)
    sys.exit(1)

from whatsapp_bridge.bot import ApplicationBuilder, MessageHandler, TypeHandler
from whatsapp_bridge.bot import TextFilter

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def log_update(update, context):
    logger.info(f"Received update: {update.message}")
async def echo(update, context):
    if update.message and update.message.get("content"):
        chat_id = update.message.get("chat_jid")
        text = update.message.get("content")
        logger.info(f"Echoing message back to chat {chat_id}: '{text}'")
    else:
        logger.warning(f"Received non-text message or non-message update: {update}")

def main():
    logger.info("Starting WhatsApp Bridge bot...")
    application = ApplicationBuilder().build()
    application.add_handler(TypeHandler(log_update), group=-1)
    echo_handler = MessageHandler(TextFilter(), echo)
    application.add_handler(echo_handler)
    application.run_polling()
    
if __name__ == "__main__":
    main()
