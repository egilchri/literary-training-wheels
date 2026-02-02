import os

def apply_css_fix(directory="."):
    # Target property to inject
    css_fix = "white-space: pre-wrap;"
    
    for filename in os.listdir(directory):
        if filename.endswith(".html") and "Canto" in filename:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # Locate the .original class in the style block and inject the fix
            # This looks for '.original {' and adds the property right after the brace
            if ".original {" in content and css_fix not in content:
                updated_content = content.replace(".original {", f".original {{ {css_fix}")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"[*] Updated: {filename}")
            else:
                print(f"[ ] Skipped (already fixed or not found): {filename}")

if __name__ == "__main__":
    apply_css_fix()
    
