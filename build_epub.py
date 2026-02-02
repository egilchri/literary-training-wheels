import os, sys, re, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def interrogate_source(epub_path):
    """Pulls original Title/Author to automate the build."""
    source = epub.read_epub(epub_path)
    return {
        'id': source.get_metadata('DC', 'identifier')[0][0] if source.get_metadata('DC', 'identifier') else 'id_123',
        'title': source.get_metadata('DC', 'title')[0][0] if source.get_metadata('DC', 'title') else 'Unknown',
        'author': source.get_metadata('DC', 'creator')[0][0] if source.get_metadata('DC', 'creator') else 'Unknown',
        'lang': source.get_metadata('DC', 'language')[0][0] if source.get_metadata('DC', 'language') else 'en'
    }

def create_bilingual_epub(txt_source, original_epub):
    meta = interrogate_source(original_epub)
    output_epub = os.path.splitext(txt_source)[0] + ".epub"
    book = epub.EpubBook()
    book.set_identifier(meta['id'])
    book.set_title(f"{meta['title']} (Bilingual)")
    book.set_language(meta['lang'])
    book.add_author(f"{meta['author']} / Gemini AI")

    # CSS for high-quality typography
    style = 'body { font-family: "Georgia", serif; padding: 2em; line-height: 1.8; } .original-text { margin-bottom: 1.5em; text-align: justify; } .translation-content i { color: #333; line-height: 1.6; } h1, h2, h3 { text-align: center; color: #005a9c; margin-top: 1.5em; }'
    book.add_item(epub.EpubItem(uid="style", file_name="style/nav.css", media_type="text/css", content=style))

    with open(txt_source, 'r', encoding='utf-8') as f:
        chunks = f.read().split('========================================')

    toc_links = []
    for idx, chunk in enumerate(chunks):
        if not chunk.strip() or "TITLE:" in chunk: continue
        file_name = f'section_{idx}.xhtml'
        clean = re.sub(r'### SECTION \d+ ORIGINAL', '', chunk).strip()
        
        # TOC LOGIC: Captures hierarchical headers like Combray and I
        soup = BeautifulSoup(chunk, 'html.parser')
        for h in soup.find_all(['h1', 'h2', 'h3']):
            txt = h.get_text().strip()
            if len(txt) < 60 and (re.match(r'^[IVXLCDM\d\.\s]+$', txt) or re.search(r'PART|BOOK|CHAPTER|COMBRAY', txt, re.IGNORECASE)):
                toc_links.append(epub.Link(file_name, txt, f"toc_{idx}_{h.name}"))

        item = epub.EpubHtml(title="Section", file_name=file_name)
        item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        item.content = f'<html><body>{clean}</body></html>'
        book.add_item(item)

    book.toc = tuple(toc_links)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + [item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] Built: {output_epub}")

if __name__ == "__main__":
    create_bilingual_epub(sys.argv[1], sys.argv[2])

