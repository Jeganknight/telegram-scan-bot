import cv2
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pdf2image import convert_from_path
import img2pdf

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Replace with your Telegram bot token
BOT_TOKEN = "7920251283:AAGdKYLYAd6iZkM82GWqt8gg6CftAU6GPag"

# Function to process an image (convert to scanned B&W)
async def process_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Apply Adaptive Thresholding (Scanned Effect)
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
        
        # Process the image
        processed_image_path = await process_image(image_path)
        processed_images.append(processed_image_path)

    # Convert processed images back to a PDF
    output_pdf_path = "processed_document.pdf"
    with open(output_pdf_path, "wb") as f:
        f.write(img2pdf.convert(processed_images))

    return output_pdf_path

# Function to handle received images
async def handle_image(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]  # Get the highest resolution image
    file = await context.bot.get_file(photo.file_id)
    
    image_path = "received_image.jpg"
    await file.download_to_drive(image_path)  # Download the image
    
    processed_image_path = await process_image(image_path)  # Apply scanning effect
    
    # Send the processed image back to the user
    await update.message.reply_photo(photo=open(processed_image_path, "rb"))

# Function to handle received PDFs
async def handle_pdf(update: Update, context: CallbackContext):
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    
    pdf_path = "received_document.pdf"
    await file.download_to_drive(pdf_path)  # Download the PDF
    
    processed_pdf_path = await process_pdf(pdf_path)  # Process the PDF
    
    # Send the processed PDF back to the user
    await update.message.reply_document(document=open(processed_pdf_path, "rb"))

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me an image or a PDF, and I'll return a scanned B&W version!")

# Main function to run the bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))  # Handle images
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))  # Handle PDFs

    app.run_polling()

if __name__ == "__main__":
    main()
