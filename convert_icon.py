from PIL import Image

def convert_png_to_ico(png_path, ico_path):
    # Open the image
    img = Image.open(png_path)
    
    # Ensure image has an alpha channel
    img = img.convert("RGBA")
    
    # Define sizes starting from large down to small
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    # Save as .ico containing multiple sizes
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Successfully converted {png_path} to {ico_path}")

if __name__ == "__main__":
    convert_png_to_ico(
        r"C:\Users\ymn_k\.gemini\antigravity\brain\b0af1f38-dd9a-4736-a84b-e7bfca593637\app_icon_1772706429567.png",
        r"C:\Users\ymn_k\Desktop\Develop\GAMESTOPREMINDER\work\GAMESTOPREMINDER\resources\icons\app_icon.ico"
    )
