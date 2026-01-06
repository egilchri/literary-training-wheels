import os, sys, re, ebooklib
from ebooklib import epub

def create_bilingual_epub(txt_source, output_epub, max_sections=None):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('The Wings of the Dove (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    style = '''
        body { font-family: "Georgia", serif; padding: 2em; line-height: 1.8; }
        .original-text { color: #1a1a1a; border-bottom: 1px solid #eeeeee; padding-bottom: 1em; margin-bottom: 2em; }
        .original-text p { text-align: justify; text-indent: 1.5em; margin-bottom: 0.8em; }
        summary { font-family: "Helvetica", sans-serif; font-size: 0.9em; color: #005a9c; cursor: pointer; padding: 8px; background: #f0f4f8; border-radius: 4px; outline: none; }
        .translation-content { background-color: #fdfdfd; padding: 20px; border-left: 4px solid #005a9c; margin-top: 10px; }
        .translation-content p { font-family: "Helvetica", sans-serif; font-style: italic; color: #444444; text-indent: 0; text-align: left; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    with open(txt_source, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Split by the separator used in translation_epub.py
    all_chunks = full_content.split('========================================')
    if max_sections:
        all_chunks = all_chunks[:max_sections]

    epub_chapters = []
    
    for idx, chunk in enumerate(all_chunks):
        if not chunk.strip():
            continue
        
        section_num = idx + 1
        anchor_id = f"trans_{section_num}"
        
        # 1. CLEAN ARTIFACTS
        # Strips out our technical notes like "### SECTION 1 ORIGINAL"
        clean_chunk = re.sub(r'### SECTION \d+ (ORIGINAL|METADATA)', '', chunk)
        
        # 2. TARGETED ANCHOR
        # Injects the anchor ID into the <details> tag for TOC jumping
        html_content = re.sub(r'<details', f'<details id="{anchor_id}"', clean_chunk, count=1)
        
        # 3. TOC LOGIC
        match = re.search(r'<p>([IVXLCDM\d]+)</p>', chunk)
        if match:
            display_title = f"Chapter {match.group(1)}"
            link_target = f"section_{section_num}.xhtml"
        elif "METADATA" in chunk:
            display_title = "Title & Introduction"
            link_target = f"section_{section_num}.xhtml"
        else:
            display_title = "Contemporary Checkpoint"
            link_target = f"section_{section_num}.xhtml#{anchor_id}"

        file_name = f'section_{section_num}.xhtml'
        chapter = epub.EpubHtml(title=display_title, file_name=file_name, lang='en')
        chapter.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        # FIX: Simply provide the html_content. ebooklib will wrap it correctly.
        chapter.content = html_content
        
        book.add_item(chapter)
        epub_chapters.append(epub.Link(link_target, display_title, f"link_{section_num}"))

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + [item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)

