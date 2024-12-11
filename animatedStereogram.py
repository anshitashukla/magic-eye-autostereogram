from flask import Flask, render_template, request, send_file
import numpy as np
from PIL import Image, ImageSequence
import io

app = Flask(__name__)

def resize_to_minimum_size(image, min_size=(1080, 1080)):
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

def extract_texture_from_uploaded_pattern(texture_image, patch_size=(100, 100)):
    resized_texture_image = texture_image.resize(patch_size, Image.Resampling.LANCZOS)
    tiled_texture = np.array(resized_texture_image)
    return tiled_texture

def generate_3d_stereogram(depth_map, texture, pattern_size=(50, 50)):
    height, width = depth_map.shape
    tiled_texture = np.tile(texture, (height // pattern_size[1] + 1, width // pattern_size[0] + 1, 1))
    tiled_texture = tiled_texture[:height, :width, :]
    stereogram = np.zeros_like(tiled_texture, dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            shift = int(depth_map[y, x]) // 5
            if x + shift < width:
                stereogram[y, x] = tiled_texture[y, x + shift]
            else:
                stereogram[y, x] = tiled_texture[y, x]

    stereogram_image = Image.fromarray(stereogram.astype(np.uint8), mode="RGB")
    return stereogram_image

def generate_animated_stereogram(depth_map, textures, pattern_size=(50, 50)):
    frames = []
    for i, texture in enumerate(textures):
        frame = generate_3d_stereogram(depth_map, texture, pattern_size)
        print(f"Frame {i+1} generated.")
        frames.append(frame)

    if len(frames) < 2:
        raise ValueError("Not enough frames to create an animation.")

    buffer = io.BytesIO()
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=500,
        loop=0
    )
    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_depth_map = request.files.get("depth_map")
        uploaded_texture = request.files.get("texture")

        if not uploaded_depth_map:
            return "Error: Please upload a depth map."

        depth_map_image = Image.open(uploaded_depth_map).convert("L")
        depth_map_image = resize_to_minimum_size(depth_map_image)
        depth_map = np.array(depth_map_image)

        textures = []
        if uploaded_texture:
            texture_image = Image.open(uploaded_texture).convert("RGB")
            texture_image = resize_to_minimum_size(texture_image, (100, 100))
            texture = extract_texture_from_uploaded_pattern(texture_image)
            for i in range(5):
                varied_texture = texture.astype(np.int32)  # Convert to int32
                varied_texture[:, :, 0] = (varied_texture[:, :, 0] + i * 20) % 256  # Perform calculation
                textures.append(varied_texture.astype(np.uint8))  # Convert back to uint8
        else:
            for _ in range(5):
                random_texture = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
                textures.append(random_texture)

        animated_gif = generate_animated_stereogram(depth_map, textures)
        return send_file(animated_gif, mimetype="image/gif", as_attachment=True, download_name="animated_stereogram.gif")

    return render_template("index1.html")

if __name__ == "__main__":
    app.run(debug=True)
