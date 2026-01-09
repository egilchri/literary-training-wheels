import os, sys, re
from ebooklib import epub
from bs4 import BeautifulSoup

def clean_text_block(html_content):
    """Removes technical markers, redundant separators, and AI artifacts."""
    # 1. Remove the '### SECTION X ORIGINAL' markers
    cleaned = re.sub(r'### SECTION \d+ ORIGINAL', '', html_content)
    
    # 2. Remove the 'Enough thinking' artifact
    cleaned = cleaned.replace("Enough thinking", "")
    
    # 3. Remove long equals-sign strings
    cleaned = re.sub(r'={6,}', '', cleaned)
    
    return cleaned.strip()

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    book.set_identifier('id_wings_dove_vol2_final_restored')
    book.set_title('The Wings of the Dove - Bilingual Edition')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    # CSS - Forcing Italics via CSS for maximum reliability
    style = '''
        body { font-family: "Georgia", serif; padding: 1.5em; line-height: 1.7; }
        p { text-align: justify !important; margin-bottom: 1.2em; text-indent: 1.5em; }
        h1, h2 { text-align: center; margin-top: 2em; color: #005a9c; }
        .original-text { color: #000000; margin-bottom: 2em; }
        .translation-content { 
            background-color: #f9f9f9; padding: 15px; border-left: 3.5px solid #005a9c; 
            margin-bottom: 2em; font-style: italic !important; 
        }
        summary { font-weight: bold; cursor: pointer; padding: 10px; background: #f0f4f8; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    with open(txt_source, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # --- THE IMPROVED CHAPTER SPLITTER ---
    # Regex updated to handle tags WITH attributes (id, class, style)
    # It looks for <p>, <h1>, <h2>, or <h3> that contains only a Roman Numeral.
    chapter_regex = r'(<(?:p|h1|h2|h3)[^>]*>\s*[IVXLCDM]+\s*</(?:p|h1|h2|h3)>)'
    chapter_chunks = re.split(chapter_regex, full_text)
    
    content_items = []
    toc_links = []
    
    if chapter_chunks:
        intro_raw = clean_text_block(chapter_chunks[0])
        intro_item = epub.EpubHtml(title='Front Matter', file_name='front.xhtml', content=f"<html><body>{intro_raw}</body></html>")
        intro_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        book.add_item(intro_item)
        content_items.append(intro_item)

    # UNIQUE CHAPTER GENERATION
    for idx, i in enumerate(range(1, len(chapter_chunks), 2)):
        # Extract the Roman numeral (e.g., 'I') from the tag
        numeral = BeautifulSoup(chapter_chunks[i], 'html.parser').get_text().strip()
        body_clean = clean_text_block(chapter_chunks[i+1])
        
        file_name = f'chap_{idx}_{numeral}.xhtml'
        chap_uid = f'uid_{idx}' # Unique ID for the TOC link
        
        # We use idx in the filename to handle Volume 2's repeating chapters (Book 6, 7...)
        c = epub.EpubHtml(title=f"Chapter {numeral}", file_name=file_name, content=f"<html><body><h1>Chapter {numeral}</h1>{body_clean}</body></html>", uid=chap_uid)
        c.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        book.add_item(c)
        toc_links.append(epub.Link(file_name, f"Chapter {numeral}", chap_uid))
        content_items.append(c)

    # TOC HANDSHAKE
    book.toc = tuple(toc_links)
    book.add_item(epub.EpubNav())
    
    # Spine Priority: 'nav' must be first
    book.spine = ['nav'] + content_items

    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] EPUB built with {len(toc_links)} chapters in TOC.")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2])

