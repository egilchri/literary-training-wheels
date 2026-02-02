import os, re
from bs4 import BeautifulSoup

def refine_canto_presentation(directory="."):
    for filename in os.listdir(directory):
        if filename.endswith(".html") and "Canto" in filename:
            with open(filename, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            # 1. Force H1 titles to Black and Center
            h1 = soup.find('h1')
            if h1:
                # We reset the style attribute entirely to ensure 'color: black' takes priority
                h1['style'] = "text-align: center; color: black !important; border-bottom: 2px solid #333; padding-bottom: 10px;"

            # 2. Adjust Spacing Between Triplets
            # We target the .segment class to remove the gray border and adjust margins
            style_tag = soup.find('style')
            if style_tag:
                css_content = style_tag.string
                # Remove the gray vertical line
                css_content = css_content.replace("border-left: 4px solid #ccc;", "border-left: none;")
                # Set a consistent margin to create exactly 2 vertical spaces (approx 2em)
                if ".segment {" in css_content:
                    css_content = re.sub(r"\.segment\s*\{[^}]*\}", 
                                       ".segment { margin-bottom: 2em; padding: 0; border-left: none; }", 
                                       css_content)
                style_tag.string = css_content

            # 3. Clean up inner source-text breaks
            # This ensures we don't have stray <br/> tags adding extra padding
            for source_div in soup.find_all(class_="source-text"):
                # Remove leading/trailing <br/> inside the source-text to keep spacing tight
                content_inner = "".join([str(c) for c in source_div.contents])
                content_inner = re.sub(r"^(<br/>\s*)+|(<br/>\s*)+$", "", content_inner)
                source_div.clear()
                source_div.append(BeautifulSoup(content_inner, 'html.parser'))

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"[*] Refined presentation for: {filename}")

if __name__ == "__main__":
    refine_canto_presentation()
    
