import os, sys, re
from ebooklib import epub
from bs4 import BeautifulSoup

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    
    # 1. METADATA
    book.set_identifier('id_wings_dove_v2_final')
    book.set_title('The Wings of the Dove - Volume 2 (Bilingual)')
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
    # Split specifically on Roman Numerals inside <p> tags
    chapter_chunks = re.split(r'(<p>[IVXLCDM]+</p>)', full_text)
    
    spine = ['nav']
    toc_links = []
    
    # Process Front Matter (Credits/Intro)
    if chapter_chunks:
        intro_content = chapter_chunks[0]
        intro_item = epub.EpubHtml(title='Front Matter', file_name='front.xhtml', content=f"<html><body>{intro_content}</body></html>")
        intro_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        book.add_item(intro_item)
        spine.append(intro_item)

    # 4. UNIQUE CHAPTER GENERATION
    # Use 'enumerate' to get a unique index (idx) for every chapter
    for idx, i in enumerate(range(1, len(chapter_chunks), 2)):
        numeral = BeautifulSoup(chapter_chunks[i], 'html.parser').get_text().strip()
        body = chapter_chunks[i+1]
        
        # FIX: Include idx in the filename to prevent "Duplicate name" errors
        # if Henry James has multiple "Chapter I" entries across different Books.
        file_name = f'chap_{idx}_{numeral}.xhtml'
        html_body = f"<h1>Chapter {numeral}</h1>{body}"
        
        c = epub.EpubHtml(title=f"Chapter {numeral}", file_name=file_name, content=f"<html><body>{html_body}</body></html>")
        c.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        book.add_item(c)
        toc_links.append(epub.Link(file_name, f"Chapter {numeral}", f"chap_{idx}"))
        spine.append(c)

    # --- 5. CLEAN NAVIGATION ---
    book.toc = tuple(toc_links)
    
    # Only add the Nav item ONCE to avoid Duplicate nav.xhtml warning
    book.add_item(epub.EpubNav())
    book.spine = spine

    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] Clean EPUB created without duplicates: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python3 build_epub.py <input.txt> <output.epub>")

