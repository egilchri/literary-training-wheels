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
            background-color: #f9f9f9; 
            border-left: 5px solid #005a9c; 
            margin: 1.5em 0; 
            padding: 1em 1.5em;
            font-family: "Helvetica", sans-serif;
            display: block;
        }
        .translation-label {
            font-weight: bold;
            color: #005a9c;
            font-size: 0.8em;
            text-transform: uppercase;
            margin-bottom: 0.5em;
            display: block;
        }
        .translation-content p { 
            font-style: italic; 
            color: #444444; 
            margin-bottom: 0.8em;
            text-indent: 0;
            display: block;
        }
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
        
        # 1. CLEANUP TECHNICAL LABELS
        clean_chunk = re.sub(r'### SECTION \d+ (ORIGINAL|METADATA)', '', chunk)
        
        # 2. ADVANCED CHAPTER DETECTION
        # Find all Roman numerals inside <p> or <h> tags in this chunk
        found_chapters = re.findall(r'<(?:p|h\d)>([IVXLCDM\d]+)</(?:p|h\d)>', chunk)
        
        if found_chapters:
            if len(found_chapters) > 1:
                display_title = f"Chapters {', '.join(found_chapters)}"
            else:
                display_title = f"Chapter {found_chapters[0]}"
        elif "METADATA" in chunk:
            display_title = "Title & Introduction"
        else:
            display_title = "Contemporary Checkpoint"

        file_name = f'section_{section_num}.xhtml'
        chapter = epub.EpubHtml(title=display_title, file_name=file_name, lang='en')
        chapter.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
        
        # Wrapping in basic HTML structure for stability
        chapter.content = f'<html><head></head><body>{clean_chunk}</body></html>'
        
        book.add_item(chapter)
        epub_chapters.append(chapter)

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + epub_chapters
    
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] Multi-chapter aware EPUB created: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)

