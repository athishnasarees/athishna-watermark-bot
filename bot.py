import os
import logging
from PIL import Image, ImageDraw, ImageFont
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# ============================
# EINSTELLUNGEN - Hier anpassen
# ============================
WATERMARK_TEXT = "Athishna Sarees"
WATERMARK_OPACITY = 140         # Transparenz
FONT_SIZE_RATIO = 0.11          # Schriftgröße relativ zur Bildbreite
TEXT_COLOR = (80, 60, 60)       # Dunkelgrau/Braun wie im Beispiel
# ============================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "DEIN_TOKEN_HIER")


def add_watermark(image_bytes: bytes) -> bytes:
    """Fügt ein elegantes, mittig platziertes Wasserzeichen hinzu."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    
    # Bild auf mindestens 1500px Breite hochskalieren damit Wasserzeichen groß genug ist
    min_width = 1500
    if img.width < min_width:
        scale = min_width / img.width
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)
    
    width, height = img.size

    # Transparente Schicht für das Wasserzeichen
    watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # Schriftgröße basierend auf der kleinsten Seite damit es immer groß genug ist
    font_size = int(min(width, height) * 0.12)

    # Versuche eine elegante Schriftart zu laden, sonst Standard
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Text-Größe berechnen für zentrierte Platzierung
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    # Kein Schatten - nur sauberer Text wie im Beispielbild
    draw.text(
        (x, y),
        WATERMARK_TEXT,
        font=font,
        fill=(*TEXT_COLOR, WATERMARK_OPACITY)
    )

    # Zusammenführen
    result = Image.alpha_composite(img, watermark_layer).convert("RGB")

    output = io.BytesIO()
    result.save(output, format="JPEG", quality=95)
    output.seek(0)
    return output.read()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Hallo! Ich bin der Athishna Sarees Wasserzeichen-Bot.\n\n"
        "Schick mir einfach ein Bild und ich füge automatisch das Wasserzeichen hinzu! 📸"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Wasserzeichen wird hinzugefügt...")

    # Höchste Qualität nehmen
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    image_bytes = await file.download_as_bytearray()
    watermarked = add_watermark(bytes(image_bytes))

    await update.message.reply_photo(
        photo=io.BytesIO(watermarked),
        caption="✅ Fertig! Athishna Sarees Wasserzeichen hinzugefügt."
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auch Bilder die als Datei gesendet werden (ohne Komprimierung)"""
    doc = update.message.document
    if doc.mime_type and doc.mime_type.startswith("image/"):
        await update.message.reply_text("⏳ Wasserzeichen wird hinzugefügt...")
        file = await context.bot.get_file(doc.file_id)
        image_bytes = await file.download_as_bytearray()
        watermarked = add_watermark(bytes(image_bytes))
        await update.message.reply_document(
            document=io.BytesIO(watermarked),
            filename="athishna_sarees_watermarked.jpg",
            caption="✅ Fertig! Athishna Sarees Wasserzeichen hinzugefügt."
        )
    else:
        await update.message.reply_text("Bitte schick mir ein Bild! 🖼️")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()
