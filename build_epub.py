import os, sys, re
from ebooklib import epub
from bs4 import BeautifulSoup

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    
    # 1. METADATA - Explicitly setting these helps Amazon index the book
    book.set_identifier('id_wings_dove_v2')
    book.set_title('The Wings of the Dove (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    # CSS for styling
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

    # --- 3. THE TOC FIX: STRICT ROMAN NUMERAL DETECTION ---
    # We split ONLY on Roman Numerals (I, II, III...) that are on their own line.
    # This prevents '1909' or other numbers from being turned into chapters.
    chapter_chunks = re.split(r'(<p>[IVXLCDM]+</p>)', full_text)
    
    spine = ['nav']
    toc_links = []
    
    # Handle everything before Chapter I (Title pages, credits, etc.)
    intro_content = chapter_chunks[0]
    intro_item = epub.EpubHtml(title='Front Matter', file_name='front.xhtml', content=f"<html><body>{intro_content}</body></html>")
    intro_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
    book.add_item(intro_item)
    spine.append(intro_item)

    # Loop through Chapters
    for i in range(1, len(chapter_chunks), 2):
        # Extract the Roman Numeral (e.g., "II")
        numeral = BeautifulSoup(chapter_chunks[i], 'html.parser').get_text().strip()
        body = chapter_chunks[i+1]
        
        file_name = f'chap_{numeral}.xhtml'
        html_body = f"<h1>Chapter {numeral}</h1>{body}"
        
        c = epub.EpubHtml(title=f"Chapter {numeral}", file_name=file_name, content=f"<html><body>{html_body}</body></html>")
        c.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        book.add_item(c)
        toc_links.append(epub.Link(file_name, f"Chapter {numeral}", f"chap_{numeral}"))
        spine.append(c)

    # --- 4. AMAZON LANDMARKS ---
    # This tells Kindle exactly where to start and where the TOC is
    book.toc = tuple(toc_links)
    book.add_item(epub.EpubNav())
    
    # We explicitly add the 'landmarks' for Kindle 'Start' and 'TOC' buttons
    book.spine = spine
    
    # Define navigation document explicitly
    nav = epub.EpubNav()
    book.add_item(nav)

    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] Amazon-ready EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2])

