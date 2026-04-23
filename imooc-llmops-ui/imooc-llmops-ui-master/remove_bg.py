import os
from PIL import Image

def remove_white_bg_soft(img_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # Use distance to pure white to determine alpha
            # Pure white: 255, 255, 255
            dist = max(r, g, b)
            
            if r > 200 and g > 200 and b > 200:
                # High brightness: calculate how close to pure white it is
                brightness = min(255, (r + g + b) // 3)
                if brightness > 240:
                    alpha = 0
                else:
                    # Smoothly fade out edges
                    alpha = int(255 * (240 - brightness) / 40.0)
                
                # To prevent whitish glow, we can assume the intended color was darker
                # But it's safer to just set alpha and keep original color, or make it slightly darker
                pixels[x, y] = (r, g, b, alpha)

    img.save(out_path, "PNG")
    print(f"Saved {out_path}")

input_img = r"d:\perfect-project\LLMops\imooc-llmops-ui\imooc-llmops-ui-master\src\assets\images\logo2.png"
output_img = r"d:\perfect-project\LLMops\imooc-llmops-ui\imooc-llmops-ui-master\src\assets\images\logo2_transparent.png"
remove_white_bg_soft(input_img, output_img)
