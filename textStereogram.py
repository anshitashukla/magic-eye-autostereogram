from flask import Flask, render_template, request, send_file
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

def generate_depth_map_from_text(text, size=(400, 400)):
    """
    Generate a depth map from user-provided text.
    """
    depth_map = np.zeros(size, dtype=np.uint8)
    img = Image.fromarray(depth_map)
    draw = ImageDraw.Draw(img)

    # Use a default font or a custom one
    font = ImageFont.load_default()

    # Calculate text size using font.getbbox
    text_bbox = font.getbbox(text)  # Returns (x_min, y_min, x_max, y_max)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Center the text in the image
    text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(text_position, text, fill=255, font=font)

    return np.array(img)

def generate_stereogram(depth_map, pattern_size=(50, 50)):
    """
    Generate a stereogram based on the provided depth map.
    """
    # Get dimensions from the depth map
    height, width = depth_map.shape

    # Ensure depth_map is uint8
    if depth_map.dtype != np.uint8:
        depth_map = depth_map.astype(np.uint8)

    # Generate random pattern
    pattern = np.random.randint(0, 256, pattern_size, dtype=np.uint8)
    stereogram = np.tile(pattern, (height // pattern_size[1], width // pattern_size[0]))

    # Create the stereogram by shifting pixels based on the depth map
    for y in range(height):
        for x in range(width):
            shift = int(depth_map[y, x]) // 10  # Ensure shift is an integer
            target_x = x + shift
            if target_x < width:  # Ensure no out-of-bounds access
                stereogram[y, target_x] = stereogram[y, x]

    # Convert stereogram to a PIL RGB image for compatibility
    stereogram_image = Image.fromarray(stereogram.astype(np.uint8)).convert("RGB")
    return stereogram_image


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get user input
        user_text = request.form.get("text", "")
        uploaded_file = request.files.get("file")

        if user_text:
            depth_map = generate_depth_map_from_text(user_text, size=(400, 400))
        elif uploaded_file:
            uploaded_image = Image.open(uploaded_file).convert("L")
            depth_map = np.array(uploaded_image.resize((400, 400)))
        else:
            return "Please provide text or upload an image!"

        # Generate stereogram
        stereogram = generate_stereogram(depth_map)

        # Save image to buffer
        buffer = io.BytesIO()
        stereogram.save(buffer, format="PNG")
        buffer.seek(0)

        return send_file(buffer, mimetype="image/png", as_attachment=True, download_name="stereogram.png")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
