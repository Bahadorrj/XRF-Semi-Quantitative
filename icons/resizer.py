from PIL import Image

path = r"branch-closed.png"

# Load the image
img = Image.open(path)

# Resize the image
img = img.resize((24, 24), Image.Resampling.LANCZOS)

# Save the resized image
img.save(path)
