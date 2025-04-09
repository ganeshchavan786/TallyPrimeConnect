import os
from PIL import Image, ImageDraw

# Define the base directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define asset directories
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')

# Ensure directories exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)

# Define image details: path: (width, height)
# Using sizes mentioned or inferred from code
images_to_create = {
    os.path.join(ASSETS_DIR, 'logo.png'): (24, 24),
    os.path.join(ICONS_DIR, 'company.png'): (20, 20),
    os.path.join(ICONS_DIR, 'add_company.png'): (20, 20),
    os.path.join(ICONS_DIR, 'settings.png'): (20, 20),
    os.path.join(ICONS_DIR, 'profile.png'): (20, 20),
    os.path.join(ICONS_DIR, 'system_info.png'): (20, 20),
    os.path.join(ICONS_DIR, 'tutorial.png'): (20, 20),
    os.path.join(ICONS_DIR, 'support.png'): (20, 20),
    os.path.join(ICONS_DIR, 'wifi.png'): (16, 16), # Smaller size used in status bar
    # Add any other missing icons here if needed
}

# Simple colors to cycle through for distinction
colors = [
    (255, 100, 100, 255), # Reddish
    (100, 255, 100, 255), # Greenish
    (100, 100, 255, 255), # Blueish
    (255, 255, 100, 255), # Yellowish
    (100, 255, 255, 255), # Cyanish
    (255, 100, 255, 255), # Magentish
    (200, 200, 200, 255), # Gray
    (150, 100, 200, 255), # Purplish
    (255, 150, 100, 255)  # Orangish
]
color_index = 0

print("Generating placeholder images...")

for img_path, size in images_to_create.items():
    try:
        # Create a new image with RGBA mode (allows transparency)
        # Using solid colors from the list
        img = Image.new('RGBA', size, colors[color_index % len(colors)])
        draw = ImageDraw.Draw(img) # Can draw text/shapes if needed later

        # Example: Add filename initials (optional, font might be small)
        # filename = os.path.basename(img_path)
        # initials = "".join([s[0] for s in filename.split('.')[0].split('_')]).upper()
        # try:
        #    # Default font is tiny, might need specific font path for better results
        #    # font = ImageFont.truetype("arial.ttf", 10) # Example
        #    font = ImageFont.load_default()
        #    draw.text((2, 2), initials[:2], fill=(0,0,0,255), font=font) # Black text
        # except IOError:
        #    draw.text((2, 2), "?", fill=(0,0,0,255)) # Fallback if font fails

        # Save the image as PNG
        img.save(img_path, 'PNG')
        print(f"  Created: {img_path} ({size[0]}x{size[1]})")

        color_index += 1 # Cycle color

    except Exception as e:
        print(f"  ERROR creating {img_path}: {e}")

print("Placeholder image generation complete.")
print("Please replace these placeholders with your actual desired images later.")