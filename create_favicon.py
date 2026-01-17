from PIL import Image, ImageDraw, ImageFont
import os

def create_favicon():
    width = 512
    height = 512
    
    # Create image with gradient
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # Gradient from #0099c6 to #00d2ff (Top to Bottom)
    c1 = (0, 153, 198) # #0099c6
    c2 = (0, 210, 255) # #00d2ff
    
    for y in range(height):
        r = int(c1[0] + (c2[0] - c1[0]) * y / height)
        g = int(c1[1] + (c2[1] - c1[1]) * y / height)
        b = int(c1[2] + (c2[2] - c1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw Text
    try:
        # Try to use Arial or consistent sans-serif
        font = ImageFont.truetype("arial.ttf", 200)
    except IOError:
        font = ImageFont.load_default()
        print("Warning: Arial font not found, using default.")

    text = "ANM"
    
    # Calculate text position to center it
    # getbbox returns (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) / 2
    y = (height - text_height) / 2 - 20 # Adjust up slightly for visual center
    
    draw.text((x, y), text, fill="white", font=font)
    
    # Save
    output_path = 'c:/Users/nelso/AG/AmamiNewsMap/favicon.png'
    image.save(output_path)
    print(f"Favicon saved to {output_path}")

if __name__ == "__main__":
    create_favicon()
