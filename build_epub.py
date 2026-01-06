import os, sys, re
from ebooklib import epub


def create_bilingual_epub(txt_source, output_epub, max_sections=None):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('The Turn of the Screw (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    style = '''
        body { font-family: "Georgia", serif; padding: 1.5em; line-height: 1.7; }
        p { text-align: justify !important; margin-bottom: 1.2em; text-indent: 1.5em; }
        .translation-content p { font-family: "Helvetica", sans-serif; font-style: italic; text-indent: 0; text-align: left; }
        .original-text { color: #000000; }
        .translation-content { background-color: #f9f9f9; padding: 15px; border-left: 3px solid #005a9c; }
        summary { font-weight: bold; cursor: pointer; padding: 10px; background: #f0f4f8; }
    '''

    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Read and CHOP the file based on the limit
    with open(txt_source, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Split by the separator we use in the translation script
    all_chunks = full_content.split('========================================')
    
    # Respect the section limit
    if max_sections:
        content = '========================================'.join(all_chunks[:max_sections])
        print(f"[*] Building EPUB with first {max_sections} sections only.")
    else:
        content = full_content

    c1 = epub.EpubHtml(title='Bilingual Text', file_name='chap_1.xhtml', lang='en')
    c1.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
    c1.content = f"<html><head></head><body>{content}</body></html>"
    book.add_item(c1)
    
    book.spine = ['nav', c1]
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        SOURCE = sys.argv[1]
        TARGET = sys.argv[2]
        # Optional 3rd argument for section limit
        LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
        create_bilingual_epub(SOURCE, TARGET, LIMIT)
    else:
        print("[!] Usage: python3 build_epub.py [SOURCE_TXT] [TARGET_EPUB] [OPTIONAL_LIMIT]")
        
