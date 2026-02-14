import os
import re
import argparse
from ebooklib import epub

def extract_metadata(summary_path):
    """
    Extracts both SUMMARY and ANALYSIS from the summary file.
    Returns a list of dictionaries: [{'summary': '...', 'analysis': '...'}, ...]
    """
    if not os.path.exists(summary_path):
        return []
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    blocks = re.split(r'={40,}', full_text)
    metadata_list = []
    
    for block in blocks:
        if not block.strip(): 
            continue
            
        summary_match = re.search(r'SUMMARY:(.*?)(?=ANALYSIS:|CONTENT:|$)', block, re.DOTALL | re.IGNORECASE)
        analysis_match = re.search(r'ANALYSIS:(.*?)(?=CONTENT:|$)', block, re.DOTALL | re.IGNORECASE)
        
        def format_to_html(text):
            if not text: return ""
            text = text.strip()
            paragraphs = text.split('\n\n')
            return "".join([f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()])

        metadata_list.append({
            'summary': format_to_html(summary_match.group(1)) if summary_match else "<p>No summary available.</p>",
            'analysis': format_to_html(analysis_match.group(1)) if analysis_match else None
        })
        
    return metadata_list

def clean_chapter_title(ch_text, global_count):
    """Identifies real chapters and returns a sequential Arabic title."""
    match = re.search(r'##\s+ORIGINAL\s+CHAPTER:\s+Chapter\s+([IVXLCDM]+)', ch_text, re.IGNORECASE)
    if match:
        return f"Chapter {global_count}"
    return None

def clean_chapter_content(ch_text):
    """Strips out technical metadata and boundary lines."""
    cleaned = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', ch_text)
    cleaned = re.sub(r'##\s+ORIGINAL\s+CHAPTER:.*?\n', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'##\s+TRANSLATED\s+CHAPTER:.*?\n', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'#{10,}', '', cleaned)
    cleaned = re.sub(r'={10,}', '', cleaned)
    return cleaned.strip()

def build_epub(input_txt, summary_txt, output_epub):
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_chapters = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    chapter_metadata = extract_metadata(summary_txt)

    book = epub.EpubBook()
    book.set_identifier('id_wings_vol2_responsive_v1')
    book.set_title('The Wings of the Dove - Responsive Edition')
    book.set_language('en')
    book.add_author('Henry James')

    epub_chapters = []
    meta_index = 0
    global_chapter_count = 1 

    for ch_text in raw_chapters:
        if not ch_text.strip(): continue
        new_title = clean_chapter_title(ch_text, global_chapter_count)
        
        if new_title:
            file_name = f'chap_{global_chapter_count}.xhtml'
            chapter = epub.EpubHtml(title=new_title, file_name=file_name, lang='en')
            
            meta = chapter_metadata[meta_index] if meta_index < len(chapter_metadata) else {'summary': "<p>N/A</p>", 'analysis': None}
            cleaned_text = clean_chapter_content(ch_text)
            
            analysis_html = ""
            if meta['analysis']:
                analysis_html = f'''
                <details class="summary-box">
                    <summary>Literary Analysis (Click to expand)</summary>
                    <div class="summary-content">
                        {meta['analysis']}
                    </div>
                </details>
                '''
            
            chapter.content = f'''
                <h1 class="chapter-title">{new_title}</h1>
                
                <details class="summary-box">
                    <summary>Chapter Summary (Click to expand)</summary>
                    <div class="summary-content">
                        {meta['summary']}
                    </div>
                </details>

                {analysis_html}

                <div class="main-body">
                    {cleaned_text}
                </div>
            '''
            chapter.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
            
            book.add_item(chapter)
            epub_chapters.append(chapter)
            meta_index += 1
            global_chapter_count += 1

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # RESPONSIVE CSS
    style = '''
        /* Global settings */
        body { font-family: serif; line-height: 1.5; margin: 0; padding: 1em; }
        h1.chapter-title { text-align: center; color: #333; margin-bottom: 1.2em; font-size: 1.8em; }

        /* Summary and Analysis Boxes */
        .summary-box { margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
        summary { padding: 10px; background-color: #eeeeee; cursor: pointer; font-weight: bold; list-style: none; }
        .summary-content { 
            padding: 15px; 
            background-color: #f6f6f6; 
            border-top: 1px solid #ddd;
            font-style: italic; 
            color: #444;
            font-size: 1em;
        }
        .summary-content p { margin-bottom: 1em; }

        /* Main Body Bilingual Layout */
        .original-text { color: #000; margin-top: 1.5em; display: block; font-size: 1.1em; }
        .translation-content { color: #666; font-style: italic; margin-bottom: 1.5em; display: block; font-size: 1em; }

        /* --- RESPONSIVE MEDIA QUERIES --- */
        
        /* For Small Phones (Width < 480px) */
        @media only screen and (max-width: 480px) {
            body { padding: 0.5em; }
            h1.chapter-title { font-size: 1.4em; }
            .summary-content { font-size: 0.9em; padding: 10px; }
            .original-text { font-size: 1em; }
            .translation-content { font-size: 0.9em; }
        }

        /* For Tablets (Width between 481px and 768px) */
        @media only screen and (min-width: 481px) and (max-width: 768px) {
            body { padding: 1.5em; }
            h1.chapter-title { font-size: 1.6em; }
            .summary-content { font-size: 0.95em; }
        }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + epub_chapters
    epub.write_epub(output_epub, book, {})
    print(f"[SUCCESS] Responsive EPUB created with optimized phone/tablet views.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary_file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build_epub(args.input, args.summary_file, args.output)

