import os, sys, re
from ebooklib import epub

def create_bilingual_epub(txt_source, output_epub, max_sections=None):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('The Turn of the Screw (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    style = '''
        body { 
            font-family: "Georgia", serif; 
            padding: 2em; 
            line-height: 1.8; 
            background-color: #ffffff;
        }
        /* Style for Henry James's Original Text */
        .original-text { 
            color: #1a1a1a; 
            border-bottom: 1px solid #eeeeee;
            padding-bottom: 1em;
            margin-bottom: 2em;
        }
        .original-text p { 
            text-align: justify; 
            text-indent: 1.5em; 
            margin-bottom: 0.8em;
        }
        /* Style for the Modern Translation Dropdown */
        summary { 
            font-family: "Helvetica", sans-serif;
            font-size: 0.9em;
            color: #005a9c; 
            cursor: pointer; 
            padding: 8px; 
            background: #f0f4f8;
            border-radius: 4px;
        }
        .translation-content { 
            background-color: #fdfdfd; 
            padding: 20px; 
            border-left: 4px solid #005a9c; 
            margin-top: 10px;
        }
        .translation-content p { 
            font-family: "Helvetica", sans-serif; 
            font-style: italic; 
            color: #444444;
            text-indent: 0; 
            text-align: left;
            margin-bottom: 1em;
        }
    '''

    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Read the text source
    with open(txt_source, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Split by the separator used in translation_epub.py
    all_chunks = full_content.split('========================================')
    
    # Respect the section limit if provided
    if max_sections:
        all_chunks = all_chunks[:max_sections]
        print(f"[*] Building EPUB with first {max_sections} sections only.")

    epub_chapters = []
    
    # Loop through each chunk to create individual XHTML files for the TOC
    for idx, chunk in enumerate(all_chunks):
        if not chunk.strip():
            continue
        
        section_num = idx + 1
        
        # --- TOC LOGIC: SEARCH FOR CHAPTER HEADINGS ---
        # James often uses <p>I</p>, <p>II</p>, or <p><strong>Title</strong></p>
        # This regex looks for Roman Numerals or plain digits wrapped in <p> tags
        match = re.search(r'<p>([IVXLCDM\d]+)</p>', chunk)
        
        if match:
            display_title = f"Chapter {match.group(1)}"
        elif "### SECTION 1 ORIGINAL" in chunk:
            display_title = "Title & Metadata"
        else:
            display_title = "Contemporary Checkpoint"

        # Create the HTML item for this section
        file_name = f'section_{section_num}.xhtml'
        chapter = epub.EpubHtml(title=display_title, file_name=file_name, lang='en')
        chapter.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        chapter.content = f"<html><head></head><body>{chunk}</body></html>"
        
        book.add_item(chapter)
        epub_chapters.append(chapter)

    # Define Navigation and Table of Contents
    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # The spine defines the reading order
    book.spine = ['nav'] + epub_chapters
    
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        SOURCE = sys.argv[1]
        TARGET = sys.argv[2]
        LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
        create_bilingual_epub(SOURCE, TARGET, LIMIT)
    else:
        print("[!] Usage: python3 build_epub.py [SOURCE_TXT] [TARGET_EPUB] [OPTIONAL_LIMIT]")

