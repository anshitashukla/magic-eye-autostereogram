import cv2
import numpy as np
import os

# Function to create a tiled repeating pattern with scale factor
def create_tiled_pattern(pattern, output_height, output_width, tile_scale=10):
    """
    Create a tiled version of the input pattern.
    - pattern: Input pattern image
    - output_height: Height of the output frame
    - output_width: Width of the output frame
    - tile_scale: Scale factor to increase number of tiles both vertically and horizontally
    """
    pattern_height, pattern_width = pattern.shape[:2]

    # Resize pattern to increase tiling density
    scaled_pattern_height = max(1, pattern_height // tile_scale)
    scaled_pattern_width = max(1, pattern_width // tile_scale)
    scaled_pattern = cv2.resize(pattern, (scaled_pattern_width, scaled_pattern_height))

    # Calculate number of tiles needed
    tiles_y = (output_height // scaled_pattern_height) + 1
    tiles_x = (output_width // scaled_pattern_width) + 1

    # Tile the pattern and crop to match the output size
    tiled_pattern = np.tile(scaled_pattern, (tiles_y, tiles_x, 1))
    tiled_pattern = tiled_pattern[:output_height, :output_width]

    return tiled_pattern

# Function to create a single autostereogram frame
def generate_autostereogram(depth_map, pattern, shift=100, tile_scale=500):
    """
    Generate an autostereogram frame from a depth map and repeating pattern.
    - depth_map: Grayscale depth map
    - pattern: Repeating pattern image
    - shift: Amount of pixel shift for the depth effect
    - tile_scale: Scale factor to control tiling density
    """
    height, width = depth_map.shape[:2]
    output = np.zeros((height, width, 3), dtype=np.uint8)

    # Tile the pattern to match the frame size with specified scale
    tiled_pattern = create_tiled_pattern(pattern, height, width, tile_scale)
    output[:, :] = tiled_pattern[:, :]

    # Apply depth shift to create stereogram effect
    for y in range(height):
        for x in range(width - shift):
            pixel_value = float(depth_map[y, x])  # Ensure it's a scalar value
            displacement = shift * (1 - pixel_value / 255.0)
            if x + int(displacement) < width:
                output[y, x] = output[y, x + int(displacement)]

    return output

# Function to process video into autostereogram
def process_video(input_video, pattern_image, output_video, depth_map_output_dir, depth_map_video, tile_scale=10):
    """Convert a video into an autostereogram video and save the colorful depth map video."""
    # Load the pattern image
    pattern = cv2.imread(pattern_image)
    if pattern is None:
        raise FileNotFoundError(f"Pattern image not found at {pattern_image}. Check the file path!")

    # Open input video
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise FileNotFoundError(f"Input video not found at {input_video}. Check the file path!")

    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # VideoWriter for outputs
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))
    depth_out = cv2.VideoWriter(depth_map_video, fourcc, fps, (frame_width, frame_height))

    # Create output directory for depth maps
    os.makedirs(depth_map_output_dir, exist_ok=True)

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale depth map
        depth_map = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Save colorful depth map
        colorful_depth_map = cv2.applyColorMap(depth_map, cv2.COLORMAP_JET)
        depth_map_path = os.path.join(depth_map_output_dir, f"depth_map_{frame_count:04d}.png")
        cv2.imwrite(depth_map_path, colorful_depth_map)

        # Write colorful depth map to video
        depth_out.write(colorful_depth_map)

        # Generate autostereogram with increased tiling
        stereogram = generate_autostereogram(depth_map, pattern, tile_scale=tile_scale)

        # Write to output video
        out.write(stereogram)
        frame_count += 1
        print(f"Processed frame {frame_count}")

    # Release resources
    cap.release()
    out.release()
    depth_out.release()
    print("Processing complete. Output saved to:", output_video)
    print("Colorful depth map video saved to:", depth_map_video)

if __name__ == "__main__":
    # Paths to input and output
    input_video = "ip.mp4"  # Replace with input video path
    pattern_image = "pattern.png"  # Path to pattern image
    output_video = "autostereogram_output.mp4"  # Output stereogram video
    depth_map_video = "depth_map_output.mp4"  # Output colorful depth map video
    depth_map_output_dir = "depth_maps"  # Directory for colorful depth maps

    # Tiling scale factor (higher values increase the number of tiles)
    tile_scale = 10  # Adjust this value to control the number of tiles

    # Run the processing
    process_video(input_video, pattern_image, output_video, depth_map_output_dir, depth_map_video, tile_scale)
