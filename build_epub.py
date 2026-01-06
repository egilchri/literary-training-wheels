import os, sys, re
import ebooklib
from ebooklib import epub

def create_bilingual_epub(txt_source, output_epub, max_sections=None):
    book = epub.EpubBook()
    # ... [Standard metadata setup remains the same] ...
    book.set_identifier('id123456')
    book.set_title('The Turn of the Screw (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    # [CSS remains the same as before]
    style = '''
        body { font-family: "Georgia", serif; padding: 2em; line-height: 1.8; }
        .original-text { color: #1a1a1a; border-bottom: 1px solid #eeeeee; padding-bottom: 1em; margin-bottom: 2em; }
        .original-text p { text-align: justify; text-indent: 1.5em; margin-bottom: 0.8em; }
        summary { font-family: "Helvetica", sans-serif; font-size: 0.9em; color: #005a9c; cursor: pointer; padding: 8px; background: #f0f4f8; border-radius: 4px; }
        .translation-content { background-color: #fdfdfd; padding: 20px; border-left: 4px solid #005a9c; margin-top: 10px; }
        .translation-content p { font-family: "Helvetica", sans-serif; font-style: italic; color: #444444; text-indent: 0; text-align: left; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    with open(txt_source, 'r', encoding='utf-8') as f:
        full_content = f.read()

    all_chunks = full_content.split('========================================')
    if max_sections:
        all_chunks = all_chunks[:max_sections]

    epub_chapters = []
    
    for idx, chunk in enumerate(all_chunks):
        if not chunk.strip():
            continue
        
        section_num = idx + 1
        
        # 1. REMOVE ARTIFACTS: Strip the "### SECTION X ORIGINAL" labels
        clean_chunk = re.sub(r'### SECTION \d+ (ORIGINAL|METADATA)', '', chunk)
        
        # 2. ADD ANCHOR: Wrap the chunk in a div with a unique ID for the TOC
        anchor_id = f"checkpoint_{section_num}"
        html_with_anchor = f"<div id='{anchor_id}'>{clean_chunk}</div>"
        
        # 3. TOC LOGIC
        match = re.search(r'<p>([IVXLCDM\d]+)</p>', chunk)
        if match:
            display_title = f"Chapter {match.group(1)}"
        elif "METADATA" in chunk:
            display_title = "Title & Introduction"
        else:
            display_title = "Contemporary Checkpoint"

        file_name = f'section_{section_num}.xhtml'
        chapter = epub.EpubHtml(title=display_title, file_name=file_name, lang='en')
        chapter.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        # Add the jump-to anchor inside the HTML content
        chapter.content = f"<html><head></head><body>{html_with_anchor}</body></html>"
        
        book.add_item(chapter)
        
        # Point the TOC link to the specific file AND the anchor ID
        epub_chapters.append(epub.Link(f"{file_name}#{anchor_id}", display_title, f"link_{section_num}"))

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + [item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] Cleaned EPUB created with functional TOC anchors.")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)

