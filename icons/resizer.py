from PIL import Image

path = r"icons/branch-open.png"

# Load the image
img = Image.open(path)

# Resize the image
img = img.resize((12, 12), Image.Resampling.LANCZOS)

# Save the resized image
img.save(path)
