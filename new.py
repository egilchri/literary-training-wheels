import os, sys, re
from ebooklib import epub

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('The Turn of the Screw (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    # --- THE TYPOGRAPHY (CSS) ---
    style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        
        br {
            display: block;
            content: "";
            margin-top: 0.5em;
        }
        body { 
            font-family: "Georgia", serif; 
            padding: 1.5em; 
            line-height: 1.7; 
            background-color: #ffffff;
        }
        .justify-text { 
            text-align: justify !important; 
            text-justify: inter-word;
            hyphens: auto;
            display: block;
            margin-bottom: 2em;
            text-indent: 1.5em; 
        }
        .original-text { color: #000000; }
        .translation-content { 
            font-family: "Helvetica", sans-serif; 
            font-style: italic; 
            color: #444444; 
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 3px solid #005a9c;
            margin-bottom: 30px;
            text-align: left;
            text-indent: 0; 
        }
        summary { 
            color: #005a9c; 
            font-family: "Helvetica", sans-serif; 
            font-weight: bold; 
            cursor: pointer; 
            padding: 12px;
            background: #f0f4f8;
            border-radius: 8px;
            margin-top: 15px;
        }
    '''

    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # 1. READ THE FILE
    with open(txt_source, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- 2. THE SELECTIVE CLEANING FILTER (FIXED INDENTATION) ---
    # Step A: Hide the triple-stacks so they don't get destroyed
    content = content.replace('<br/><br/><br/>', '[[SCENE_BREAK]]')
    
    # Step B: Remove all single <br/> tags to allow for justification
    content = content.replace('<br/>', ' ')
    
    # Step C: Restore the triple-stacks with &nbsp; for the reader
    content = content.replace('[[SCENE_BREAK]]', '<br/>&nbsp;<br/>&nbsp;<br/>')

    # 3. CREATE THE CHAPTER
    c1 = epub.EpubHtml(title='Bilingual Text', file_name='chap_1.xhtml', lang='en')
    html_content = f"<html><head><style>{style}</style></head><body>{content}</body></html>"
    c1.content = html_content
    book.add_item(c1)

    book.spine = ['nav', c1]
    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] Smart-Cleaned EPUB created at: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        SOURCE, OUTPUT = sys.argv[1], sys.argv[2]
        if os.path.exists(SOURCE):
           create_bilingual_epub(SOURCE, OUTPUT)
    else:
        print("[!] Usage: python3 build_epub.py [SOURCE_TXT] [TARGET_EPUB]")
        
