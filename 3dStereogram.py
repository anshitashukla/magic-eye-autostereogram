from flask import Flask, render_template, request, send_file
import numpy as np
from PIL import Image
import io

app = Flask(__name__)

def resize_to_minimum_size(image, min_size=(1080, 1080)):
    """
    Resize an image to at least the specified minimum size while maintaining aspect ratio.
    """
    width, height = image.size
    if width < min_size[0] or height < min_size[1]:
        scale_width = min_size[0] / width
        scale_height = min_size[1] / height
        scale = max(scale_width, scale_height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized_image
    return image

def extract_texture_from_uploaded_pattern(texture_image, patch_size=(50, 50)):
    """
    Resize the entire uploaded texture image to the required patch_size without cropping.
    """
    resized_texture_image = texture_image.resize(patch_size, Image.Resampling.LANCZOS)
    tiled_texture = np.array(resized_texture_image)
    return tiled_texture

def generate_3d_stereogram(depth_map, texture, pattern_size=(50, 50)):
    """
    Generate a 3D stereogram based on the provided depth map and the resized texture.
    """
    height, width = depth_map.shape

    # Tile the resized texture to match the depth map size
    tiled_texture = np.tile(texture, (height // pattern_size[1] + 1, width // pattern_size[0] + 1, 1))
    tiled_texture = tiled_texture[:height, :width, :]  # Crop to match depth map size

    # Create a stereogram with 3D effect
    stereogram = np.zeros_like(tiled_texture, dtype=np.uint8)

    # Populate the stereogram based on the depth map
    for y in range(height):
        for x in range(width):
            shift = int(depth_map[y, x]) // 5  # Scale the shift based on depth
            if x + shift < width:
                stereogram[y, x] = tiled_texture[y, x + shift]
            else:
                stereogram[y, x] = tiled_texture[y, x]  # Use original if out of bounds

    # Convert stereogram to RGB image
    stereogram_image = Image.fromarray(stereogram.astype(np.uint8), mode="RGB")
    return stereogram_image

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if files are provided
        uploaded_depth_map = request.files.get("depth_map")
        uploaded_texture = request.files.get("texture")

        if not uploaded_depth_map or not uploaded_texture:
            return "Error: Please upload both a depth map and a texture."

        # Convert depth map to NumPy array and resize if necessary
        depth_map_image = Image.open(uploaded_depth_map).convert("L")  # Grayscale depth map
        depth_map_image = resize_to_minimum_size(depth_map_image)
        depth_map = np.array(depth_map_image)

        # Convert uploaded texture, resize it, and extract pattern
        texture_image = Image.open(uploaded_texture).convert("RGB")  # Preserve colors
        texture_image = resize_to_minimum_size(texture_image, (50, 50))
        texture = extract_texture_from_uploaded_pattern(texture_image)

        # Generate the 3D stereogram
        stereogram = generate_3d_stereogram(depth_map, texture)

        # Save the result to a buffer
        buffer = io.BytesIO()
        stereogram.save(buffer, format="PNG")
        buffer.seek(0)

        return send_file(buffer, mimetype="image/png", as_attachment=True, download_name="3d_stereogram.png")

    return render_template("index1.html")

if __name__ == "__main__":
    app.run(debug=True)

