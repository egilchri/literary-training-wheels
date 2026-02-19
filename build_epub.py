import os
import re
import argparse
from ebooklib import epub

def is_strictly_roman(text):
    """Matches standalone Roman numerals like 'VII' or 'I'."""
    pattern = r"^\s*[ivxlcdm]+\s*$"
    return bool(re.match(pattern, text, re.IGNORECASE))

def extract_metadata(summary_path):
    """Extracts SUMMARY and ANALYSIS from the summary file."""
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
            # Clean technical artifacts and SECTION markers
            text = re.sub(r'^\s*[#=]{3,}\s*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', text, flags=re.IGNORECASE)
            
            # Handle bullet points
            text = re.sub(r'^\s*[\*\-]\s*(.*)', r'<li>\1</li>', text, flags=re.MULTILINE)
            if '<li>' in text:
                text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
            
            paragraphs = text.split('\n\n')
            return "".join([f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()])

        metadata_list.append({
            'summary': format_to_html(summary_match.group(1)) if summary_match else "<p>No summary available.</p>",
            'analysis': format_to_html(analysis_match.group(1)) if analysis_match else None
        })
        
    return metadata_list

def create_epub(bilingual_txt, summary_txt, output_epub):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('The Wings of the Dove - Bilingual Edition')
    book.set_language('en')
    book.add_author('Henry James')

    chapter_metadata = extract_metadata(summary_txt)
    
    with open(bilingual_txt, 'r', encoding='utf-8') as f:
        full_content = f.read()

    sections = re.split(r'={40,}', full_content)
    chapters = []
    current_chapter_html = ""
    chapter_count = 0
    ROMAN_H2_PATTERN = r"<h2[^>]*?>\s*([ivxlcdm]+)\s*</h2>"

    print(f"[*] Building EPUB with Audio Controls...")

    for section in sections:
        if not section.strip():
            continue

        # Strip Technical markers
        clean_section = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', section, flags=re.IGNORECASE)
        clean_section = re.sub(r'^\s*[#=]{3,}\s*$', '', clean_section, flags=re.MULTILINE)

        header_match = re.search(ROMAN_H2_PATTERN, clean_section, re.IGNORECASE)
        
        if header_match:
            if chapter_count > 0 and current_chapter_html:
                save_chapter(book, chapters, chapter_count, current_chapter_html, chapter_metadata)
            
            chapter_count += 1
            roman_val = header_match.group(1).upper()
            current_chapter_html = f'<h1 class="chapter-title">Chapter {roman_val}</h1>'
            continue

        if chapter_count > 0:
            current_chapter_html += f'<div class="section-block">{clean_section}</div>'

    if chapter_count > 0 and current_chapter_html:
        save_chapter(book, chapters, chapter_count, current_chapter_html, chapter_metadata)

    style = '''
        body { font-family: "Times New Roman", serif; line-height: 1.6; padding: 1em; }
        h1.chapter-title { text-align: center; text-transform: uppercase; margin-top: 2em; margin-bottom: 0.5em; }
        
        .chapter-audio { text-align: center; margin-bottom: 2em; }
        audio { width: 100%; max-width: 400px; }

        details { margin-bottom: 1.5em; border: 1px solid #ddd; border-radius: 4px; }
        details summary { cursor: pointer; padding: 10px; font-weight: bold; background-color: #f0f0f0; }
        
        .summary-box { padding: 15px; font-style: italic; background-color: #f9f9f9; }
        .analysis-box { padding: 15px; background-color: #eef2f7; }
        .box-label { font-weight: bold; text-transform: uppercase; display: block; margin-bottom: 5px; font-size: 0.8em; color: #555; }
        
        .original-text { color: #000; margin-bottom: 0.5em; display: block; }
        .translation-content { color: #666; font-style: italic; margin-bottom: 1.5em; display: block; border-bottom: 1px solid #eee; padding-bottom: 1em; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters

    epub.write_epub(output_epub, book)
    print(f"[*] EPUB created successfully: {output_epub}")

def save_chapter(book, chapters_list, count, html_content, metadata_list):
    """Inserts Audio Player and Collapsible Metadata under the Chapter Title."""
    idx = count - 1
    meta = metadata_list[idx] if 0 <= idx < len(metadata_list) else {'summary': '', 'analysis': None}
    
    # Generate Audio Control HTML
    audio_url = f"https://media.githubusercontent.com/media/egilchri/wings_one/main/Chapter_{count}.mp3"
    audio_html = f'''
    <div class="chapter-audio">
        <audio controls preload="metadata">
            <source src="{audio_url}" type="audio/mpeg">
        </audio>
    </div>
    '''

    # Build Collapsible Metadata
    meta_html = f'''
    <details>
        <summary>Chapter Summary & Character Study</summary>
        <div class="summary-box">
            <span class="box-label">Summary</span>
            {meta["summary"]}
        </div>
        '''
    if meta['analysis']:
        meta_html += f'''
        <div class="analysis-box">
            <span class="box-label">Character Study</span>
            {meta["analysis"]}
        </div>
        '''
    meta_html += '</details>'
    
    # Inject both under the <h1> title
    title_end_tag = "</h1>"
    parts = html_content.split(title_end_tag, 1)
    
    if len(parts) == 2:
        # Order: Title -> Audio -> Collapsible Metadata -> Prose
        final_html = f"<html><body>{parts[0]}{title_end_tag}{audio_html}{meta_html}{parts[1]}</body></html>"
    else:
        final_html = f"<html><body>{audio_html}{meta_html}{html_content}</body></html>"
    
    chapter_item = epub.EpubHtml(title=f'Chapter {count}', file_name=f'chap_{count:02d}.xhtml', lang='en')
    chapter_item.content = final_html
    chapter_item.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
    book.add_item(chapter_item)
    chapters_list.append(chapter_item)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-s", "--summary", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    create_epub(args.input, args.summary, args.output)

