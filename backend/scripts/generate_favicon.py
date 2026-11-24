import base64
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw

def generate_favicons():
    src_path = Path(r"C:/Users/jayad/.gemini/antigravity/brain/ea6f84cf-8a0c-48d4-8d5c-048876ccc8ed/.user_uploaded/media_1794939120272_182226d4.png")
    if not src_path.exists():
        print(f"Error: Source image not found at {src_path}")
        return

    im = Image.open(src_path).convert("RGBA")

    # Canvas 256x256
    size = 256
    bg_color = (36, 41, 47, 255)

    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    # Rounded corners with radius 48
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=48, fill=bg_color)

    # Scale image to fit inside comfortably
    scale = 204.0 / im.width
    target_w = int(im.width * scale)
    target_h = int(im.height * scale)
    im_resized = im.resize((target_w, target_h), Image.Resampling.LANCZOS)

    x = (size - target_w) // 2
    y = (size - target_h) // 2
    badge.paste(im_resized, (x, y), im_resized)

    # Save PNGs
    badge.save("frontend/public/images/favicon.png", "PNG")
    badge.save("frontend/public/images/favicon_light.png", "PNG")
    badge.save("frontend/public/favicon.png", "PNG")

    # Save ICO (multi-res: 16x16, 32x32, 48x48, 64x64)
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    badge.save("frontend/public/favicon.ico", format="ICO", sizes=ico_sizes)

    # Generate SVGs
    buffered = BytesIO()
    badge.save(buffered, format="PNG")
    b64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <image width="256" height="256" href="data:image/png;base64,{b64_data}"/>
</svg>
"""
    with open("frontend/public/images/favicon.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    with open("frontend/public/images/favicon_light.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("Favicon generation successful!")

if __name__ == "__main__":
    generate_favicons()
