"""
QR Code Generation Module for ERP-System
Generates QR codes for student ID cards
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

def generate_student_qr(student_data, output_path):
    """
    Generate QR code for student
    student_data: dict with student info
    output_path: where to save the QR code
    """
    # Create QR code data string with better formatting
    qr_data = f"""ERP-System Student Card
ID: {student_data['id']}
Name: {student_data['name']}
Mobile: {student_data['mobile']}
Course: {student_data.get('course', 'N/A')}
Valid Until: {student_data['expiry']}"""
    
    # Generate QR code with better settings for scanning
    qr = qrcode.QRCode(
        version=3,  # Increased version for more data capacity
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=2,  # Reduced border for better scanning
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save(output_path)
    
    return output_path

def generate_student_card(student_data, photo_path, output_path):
    """
    Generate complete student ID card with QR code
    """
    # Create card (600x400 pixels)
    card = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(card)
    
    # Draw border
    draw.rectangle([10, 10, 590, 390], outline='#6366F1', width=3)
    
    # Header
    draw.rectangle([10, 10, 590, 80], fill='#6366F1')
    
    try:
        # Try to use a nice font
        title_font = ImageFont.truetype("arial.ttf", 32)
        text_font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Title
    draw.text((300, 40), "ERP-System", fill='white', 
              font=title_font, anchor='mm')
    
    # Add photo if available
    if photo_path and os.path.exists(photo_path):
        try:
            photo = Image.open(photo_path)
            photo = photo.resize((120, 120))
            card.paste(photo, (30, 100))
        except:
            pass
    
    # Student details
    y_pos = 110
    details = [
        f"Name: {student_data['name']}",
        f"Mobile: {student_data['mobile']}",
        f"Course: {student_data.get('course', 'N/A')}",
        f"Valid Until: {student_data['expiry']}"
    ]
    
    for detail in details:
        draw.text((170, y_pos), detail, fill='black', font=text_font)
        y_pos += 30
                        
    # Generate and add QR code
    qr_path = output_path.replace('.png', '_qr.png')
    generate_student_qr(student_data, qr_path)
    
    try:
        qr_img = Image.open(qr_path)
        qr_img = qr_img.resize((160, 160))  # Increased size for better scanning
        card.paste(qr_img, (415, 210))  # Adjusted position
         
        # QR label
        draw.text((495, 378), "Scan for details", fill='#6366F1', 
                 font=small_font, anchor='mm')
    except Exception as e:
        print(f"Error adding QR code: {e}")
        pass
    
    # Save card
    card.save(output_path)
    
    return output_path
 