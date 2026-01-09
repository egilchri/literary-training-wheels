import os, sys, re, ebooklib
from ebooklib import epub

def create_bilingual_epub(txt_source, output_epub=None):
    # Default output name if none provided
    if not output_epub:
        output_epub = os.path.splitext(txt_source)[0].replace("_Bilingual", "") + "_Final.epub"

    with open(txt_source, 'r', encoding='utf-8') as f:
        full_content = f.read()

    all_chunks = full_content.split('========================================')
    
    # --- NEW: INTERROGATE METADATA FROM TEXT FILE ---
    meta_chunk = all_chunks[0]
    meta_data = {}
    for line in meta_chunk.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            meta_data[key.strip()] = val.strip()

    book = epub.EpubBook()
    book.set_identifier(meta_data.get('IDENTIFIER', 'id123'))
    book.set_title(f"{meta_data.get('TITLE', 'Unknown')} (Bilingual Edition)")
    book.set_language(meta_data.get('LANGUAGE', 'en'))
    book.add_author(f"{meta_data.get('AUTHOR', 'Unknown')} / Gemini AI")

    # [Rest of your hierarchical TOC and CSS logic follows...]
    
    # Add NCX and NAV for epubcheck compliance
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    book.spine = ['nav'] + [item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] Generalised EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

