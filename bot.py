import os
import logging
import threading
import cv2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pdf2image import convert_from_path
import img2pdf
from flask import Flask

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load Telegram Bot Token from environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")

# Initialize Flask App
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Bot is running!"

# Function to process an image (convert to scanned B&W)
async def process_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    processed_text = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 15, 8)
    output_path = image_path.replace(".jpg", "_processed.jpg")
    cv2.imwrite(output_path, processed_text)  # Save processed image
    return output_path

# Function to process a PDF file
async def process_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    processed_images = []
    
    for i, img in enumerate(images):
        image_path = f"page_{i+1}.jpg"
        img.save(image_path, "JPEG")
        processed_image_path = await process_image(image_path)
        processed_images.append(processed_image_path)

    output_pdf_path = "processed_document.pdf"
    with open(output_pdf_path, "wb") as f:
        f.write(img2pdf.convert(processed_images))
    
    # Cleanup temporary images
    for img in processed_images:
        os.remove(img)

    return output_pdf_path

# Function to handle received images
async def handle_image(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]  # Get the highest resolution image
    file = await context.bot.get_file(photo.file_id)
    
    image_path = "received_image.jpg"
    await file.download_to_drive(image_path)  # Download the image
    
    processed_image_path = await process_image(image_path)  # Apply scanning effect
    
    await update.message.reply_photo(photo=open(processed_image_path, "rb"))

    # Cleanup
    os.remove(image_path)
    os.remove(processed_image_path)

# Function to handle received PDFs
async def handle_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    
    pdf_path = "received_document.pdf"
    await file.download_to_drive(pdf_path)  # Download the PDF
    
    processed_pdf_path = await process_pdf(pdf_path)  # Process the PDF
    
    await update.message.reply_document(document=open(processed_pdf_path, "rb"))

    # Cleanup
    os.remove(pdf_path)
    os.remove(processed_pdf_path)

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me an image or a PDF, and I'll return a scanned B&W version!")

# Function to start the bot
def run_telegram_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))  # Handle images
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))  # Handle PDFs

    app.run_polling()

# Start bot in a separate thread
threading.Thread(target=run_telegram_bot, daemon=True).start()

# Start Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
