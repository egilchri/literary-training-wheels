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
        .original-text { color: #1a1a1a; margin-bottom: 2em; }
        .original-text p { text-align: justify; text-indent: 1.5em; margin-bottom: 0.8em; }
        .translation-block { 
            background-color: #f9f9f9; border-left: 5px solid #005a9c; 
            margin: 1.5em 0; padding: 1em 1.5em; font-family: "Helvetica", sans-serif;
            display: block;
        }
        .translation-label { font-weight: bold; color: #005a9c; font-size: 0.8em; text-transform: uppercase; margin-bottom: 0.5em; display: block; }
        .translation-content p { font-style: italic; color: #444444; margin-bottom: 0.8em; text-indent: 0; display: block; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    with open(txt_source, 'r', encoding='utf-8') as f:
        full_content = f.read()

    all_chunks = full_content.split('========================================')
    if max_sections:
        all_chunks = all_chunks[:max_sections]

    # --- TOC NESTING LOGIC ---
    nested_toc = []
    current_parent = None
    sub_items = []

    for idx, chunk in enumerate(all_chunks):
        if not chunk.strip():
            continue
        
        section_num = idx + 1
        anchor_id = f"trans_{section_num}"
        file_name = f'section_{section_num}.xhtml'
        
        # 1. CLEANUP
        clean_chunk = re.sub(r'### SECTION \d+ (ORIGINAL|METADATA)', '', chunk)
        
        # 2. IDENTIFY HEADINGS
        chapter_match = re.search(r'<(?:p|h\d)[^>]*>([IVXLCDM\d]+)</(?:p|h\d)>', chunk)
        volume_match = re.search(r'VOLUME\s+[IVXLCDM\d]+', chunk, re.IGNORECASE)
        
        # 3. BUILD HIERARCHY
        if chapter_match or volume_match:
            # If we had sub-items for a previous chapter, finalize that parent
            if current_parent:
                nested_toc.append((current_parent, tuple(sub_items)))
                sub_items = []
            
            title = f"Chapter {chapter_match.group(1)}" if chapter_match else volume_match.group(0).title()
            current_parent = epub.Link(file_name, title, f"parent_{section_num}")
        else:
            # If no parent has been established yet (e.g. at the very start), create a default Title/Intro parent
            if not current_parent:
                current_parent = epub.Link(file_name, "Introduction", "parent_intro")
            
            checkpoint_title = f"Contemporary Checkpoint {section_num}"
            sub_items.append(epub.Link(f"{file_name}#{anchor_id}", checkpoint_title, f"sub_{section_num}"))

        # Create the HTML item
        chapter_item = epub.EpubHtml(title="Section", file_name=file_name, lang='en')
        chapter_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        chapter_item.content = f'<html><head></head><body>{clean_chunk}</body></html>'
        book.add_item(chapter_item)

    # Add the final group to the TOC
    if current_parent:
        nested_toc.append((current_parent, tuple(sub_items)))

    book.toc = tuple(nested_toc)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + [item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] Hierarchical EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)

