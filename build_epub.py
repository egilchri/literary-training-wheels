import os, sys, re
from ebooklib import epub
from bs4 import BeautifulSoup

def clean_text_block(html_content):
    """Removes technical section markers and long equals-sign strings."""
    # 1. Remove '### SECTION X ORIGINAL' markers
    cleaned = re.sub(r'### SECTION \d+ ORIGINAL', '', html_content)
    
    # 2. Remove spurious equals-sign strings (6 or more signs)
    cleaned = re.sub(r'={6,}', '', cleaned)
    
    return cleaned.strip()

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    
    # METADATA
    book.set_identifier('id_wings_dove_final_v4')
    book.set_title('The Wings of the Dove (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    style = '''
        body { font-family: "Georgia", serif; padding: 1.5em; line-height: 1.7; }
        p { text-align: justify !important; margin-bottom: 1.2em; text-indent: 1.5em; }
        h1 { text-align: center; margin-top: 2em; color: #005a9c; font-size: 1.8em; }
        .original-text { color: #000000; margin-bottom: 2em; }
        .translation-content { background-color: #f9f9f9; padding: 15px; border-left: 3px solid #005a9c; margin-bottom: 2em; }
        summary { font-weight: bold; cursor: pointer; padding: 10px; background: #f0f4f8; }
        /* Style for the visible TOC page */
        nav#toc ol { list-style-type: none; padding-left: 0; }
        nav#toc li { margin-bottom: 0.5em; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # READ SOURCE
    with open(txt_source, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # --- THE CHAPTER SPLITTER ---
    # Detects Roman Numeral chapters inside <p> or <h2> tags
    chapter_chunks = re.split(r'(<(?:p|h2)>[IVXLCDM]+</(?:p|h2)>)', full_text)
    
    # 'nav' MUST be the first item in the spine to appear at the beginning
    spine = ['nav']
    toc_links = []
    
    # Process Front Matter (Title Page/Credits)
    if chapter_chunks:
        intro_raw = clean_text_block(chapter_chunks[0])
        intro_item = epub.EpubHtml(title='Title Page', file_name='front.xhtml', content=f"<html><body>{intro_raw}</body></html>")
        intro_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        book.add_item(intro_item)
        spine.append(intro_item)

    # UNIQUE CHAPTER GENERATION
    for idx, i in enumerate(range(1, len(chapter_chunks), 2)):
        numeral_text = BeautifulSoup(chapter_chunks[i], 'html.parser').get_text().strip()
        body_clean = clean_text_block(chapter_chunks[i+1])
        
        file_name = f'chap_{idx}_{numeral_text}.xhtml'
        html_body = f"<h1>Chapter {numeral_text}</h1>{body_clean}"
        
        c = epub.EpubHtml(title=f"Chapter {numeral_text}", file_name=file_name, content=f"<html><body>{html_body}</body></html>")
        c.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        book.add_item(c)
        toc_links.append(epub.Link(file_name, f"Chapter {numeral_text}", f"chap_{idx}"))
        spine.append(c)

    # --- NAVIGATION MANIFEST ---
    book.toc = tuple(toc_links)
    
    # Create the navigation item and ensure it's registered
    nav_item = epub.EpubNav()
    book.add_item(nav_item)
    book.spine = spine

    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] EPUB created with TOC at the beginning: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2])

