import pygame
import numpy as np
from PIL import Image
import random

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("3D Magic Eye Puzzle Game")
font = pygame.font.Font(None, 36)

def generate_stereogram(pattern_size=(50, 50), hidden_shape_size=(20, 20)):
    """
    Generate a stereogram image with a hidden random shape.
    """
    width, height = pattern_size[0] * 15, pattern_size[1] * 15
    depth_map = np.zeros((height, width), dtype=np.uint8)

    # Place a random shape into the depth map
    start_x = random.randint(0, width - hidden_shape_size[0])
    start_y = random.randint(0, height - hidden_shape_size[1])
    depth_map[start_y:start_y + hidden_shape_size[1], start_x:start_x + hidden_shape_size[0]] = 30  # Small depth values to prevent large shifts

    # Generate random pattern
    pattern = np.random.randint(0, 256, pattern_size, dtype=np.uint8)
    stereogram = np.tile(pattern, (height // pattern_size[1], width // pattern_size[0]))

    # Create the stereogram by shifting pixels based on the depth map
    for y in range(height):
        for x in range(width):
            shift = int(depth_map[y, x] // 10)  # Convert to int to avoid overflow
            target_x = x + shift
            if target_x < width:  # Ensure no out-of-bounds access
                stereogram[y, target_x] = stereogram[y, x]

    # Convert to RGB PIL image for pygame compatibility
    stereogram_image = Image.fromarray(stereogram.astype(np.uint8)).convert("RGB")
    return stereogram_image, (start_x, start_y, hidden_shape_size[0], hidden_shape_size[1])

def main():
    # Game variables
    running = True
    clock = pygame.time.Clock()

    # Generate a stereogram
    stereogram_image, hidden_object = generate_stereogram()
    stereogram_surface = pygame.image.fromstring(stereogram_image.tobytes(), stereogram_image.size, "RGB")

    # Game state
    message = "Find the hidden object in the stereogram!"
    game_over = False

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                x, y = pygame.mouse.get_pos()
                # Check if the click is inside the hidden object
                if hidden_object[0] <= x <= hidden_object[0] + hidden_object[2] and \
                   hidden_object[1] <= y <= hidden_object[1] + hidden_object[3]:
                    message = "Congratulations! You found it!"
                    game_over = True
                else:
                    message = "Try again!"

        # Display stereogram
        screen.blit(stereogram_surface, (0, 0))

        # Display message
        text_surface = font.render(message, True, BLACK)
        screen.blit(text_surface, (20, SCREEN_HEIGHT - 50))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
