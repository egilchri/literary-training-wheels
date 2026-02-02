import os
from bs4 import BeautifulSoup

def reformat_html_files(directory="."):
    for filename in os.listdir(directory):
        # Target only your Canto HTML files
        if filename.endswith(".html") and "Canto" in filename:
            with open(filename, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            # 1. Remove the vertical gray lines
            # This is controlled by the .segment border-left in the <style> block
            style_tag = soup.find('style')
            if style_tag:
                new_style = style_tag.string.replace(
                    "border-left: 4px solid #ccc;", 
                    "border-left: none;"
                )
                style_tag.string.replace_with(new_style)

            # 2. Color titles black and center them
            # We look for the h1 tag
            h1 = soup.find('h1')
            if h1:
                # Update the style attribute: center text and set color to black
                h1['style'] = "text-align: center; color: black; border-bottom: 2px solid #333; padding-bottom: 10px;"

            # 3. Save the modified file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"[*] Successfully reformatted: {filename}")

if __name__ == "__main__":
    reformat_html_files()

