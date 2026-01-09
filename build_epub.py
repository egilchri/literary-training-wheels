import os, sys, re
from ebooklib import epub
from bs4 import BeautifulSoup

def clean_text_block(html_content):
    """Removes '### SECTION' headers and long equals-sign strings."""
    # 1. Remove the '### SECTION X ORIGINAL' markers
    cleaned = re.sub(r'### SECTION \d+ ORIGINAL', '', html_content)
    
    # 2. Remove spurious equals-sign strings (6 or more signs)
    cleaned = re.sub(r'={6,}', '', cleaned)
    
    return cleaned.strip()

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    
    # 1. METADATA
    book.set_identifier('id_wings_dove_vol2_final_v5')
    book.set_title('The Wings of the Dove (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    style = '''
        body { font-family: "Georgia", serif; padding: 1.5em; line-height: 1.7; }
        p { text-align: justify !important; margin-bottom: 1.2em; text-indent: 1.5em; }
        h1 { text-align: center; margin-top: 2em; color: #005a9c; }
        .original-text { color: #000000; margin-bottom: 2em; }
        .translation-content { background-color: #f9f9f9; padding: 15px; border-left: 3px solid #005a9c; margin-bottom: 2em; }
        summary { font-weight: bold; cursor: pointer; padding: 10px; background: #f0f4f8; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # 2. READ SOURCE
    with open(txt_source, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # --- 3. THE CHAPTER SPLITTER ---
    # Detects Roman Numeral chapters inside <p> or <h2> tags
    chapter_chunks = re.split(r'(<(?:p|h2)>[IVXLCDM]+</(?:p|h2)>)', full_text)
    
    content_items = []
    toc_links = []
    
    # Process Front Matter (Title Page/Credits)
    if chapter_chunks:
        intro_raw = clean_text_block(chapter_chunks[0])
        intro_item = epub.EpubHtml(title='Title Page', file_name='front.xhtml', content=f"<html><body>{intro_raw}</body></html>")
        intro_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        book.add_item(intro_item)
        content_items.append(intro_item)

    # 4. UNIQUE CHAPTER GENERATION
    # Uses 'idx' to prevent duplicate filenames for repeating Roman numerals in Volume 2
    for idx, i in enumerate(range(1, len(chapter_chunks), 2)):
        numeral_text = BeautifulSoup(chapter_chunks[i], 'html.parser').get_text().strip()
        body_clean = clean_text_block(chapter_chunks[i+1])
        
        file_name = f'chap_{idx}_{numeral_text}.xhtml'
        html_body = f"<h1>Chapter {numeral_text}</h1>{body_clean}"
        
        c = epub.EpubHtml(title=f"Chapter {numeral_text}", file_name=file_name, content=f"<html><body>{html_body}</body></html>")
        c.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        book.add_item(c)
        toc_links.append(epub.Link(file_name, f"Chapter {numeral_text}", f"chap_{idx}"))
        content_items.append(c)

    # --- 5. NAVIGATION & SPINE CONFIGURATION ---
    # Register the links for the sidebar Table of Contents
    book.toc = tuple(toc_links)
    
    # Create the internal Navigation Document item
    nav_item = epub.EpubNav()
    book.add_item(nav_item)
    
    # THE FIX: Explicitly set 'nav' as the first item in the spine.
    # This forces the e-reader to show the TOC at the beginning of the book.
    book.spine = ['nav'] + content_items

    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] EPUB created with visible TOC at the start: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2])
        
