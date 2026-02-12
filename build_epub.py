import os
import re
import argparse
from ebooklib import epub

def extract_summaries(summary_path):
    """Extracts text between 'SUMMARY:' and 'CONTENT:' from the summary file."""
    if not os.path.exists(summary_path):
        return []
    with open(summary_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    # Split by the dashed lines used in the summary output file
    blocks = re.split(r'={40,}', full_text)
    summaries = []
    for block in blocks:
        if not block.strip(): 
            continue
        match = re.search(r'SUMMARY:(.*?)(?=CONTENT:)', block, re.DOTALL | re.IGNORECASE)
        if match:
            summaries.append(match.group(1).strip())
    return summaries

def clean_chapter_title(ch_text, global_count):
    """Identifies real chapters and returns a sequential Arabic title."""
    header_section = ch_text[:500]

    # SKIP Table of Contents and Book dividers to prevent sequence resets
    if header_section.count("Chapter") > 3:
        return None
    if re.search(r'BOOK\s+(FIRST|SECOND|THIRD|FOURTH|FIFTH)', header_section, re.IGNORECASE):
        return None

    # ONLY match "Chapter [Roman Numeral]" for narrative chapters
    roman_match = re.search(r'Chapter\s+([IVXLCDM]+)', header_section, re.IGNORECASE)
    if roman_match:
        return f"Chapter {global_count}"
        
    return None

def clean_chapter_content(ch_text):
    """
    Strips out technical metadata, section headers, and boundary lines
    to provide a clean reading experience.
    """
    # 1. Remove '### SECTION X ORIGINAL/TRANSLATED' headers
    cleaned = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', ch_text)
    
    # 2. Remove '## ORIGINAL CHAPTER' and '## TRANSLATED CHAPTER' metadata
    cleaned = re.sub(r'##\s+ORIGINAL\s+CHAPTER:.*?\n', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'##\s+TRANSLATED\s+CHAPTER:.*?\n', '', cleaned, flags=re.IGNORECASE)
    
    # 3. Remove long boundary lines (#### and ====)
    cleaned = re.sub(r'#{10,}', '', cleaned)
    cleaned = re.sub(r'={10,}', '', cleaned)
    
    # 4. Remove '>>> CHAPTER BOUNDARY <<<' markers
    cleaned = cleaned.replace('>>> CHAPTER BOUNDARY <<<', '')
    
    return cleaned.strip()

def build_epub(input_txt, summary_txt, output_epub):
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by the physical boundary markers
    raw_chapters = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    summaries = extract_summaries(summary_txt)

    book = epub.EpubBook()
    book.set_identifier('id_final_sequential_v1')
    book.set_title('The Wings of the Dove - Sequential Arabic Edition')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    epub_chapters = []
    summary_index = 0
    global_chapter_count = 1 

    for ch_text in raw_chapters:
        if not ch_text.strip():
            continue

        new_title = clean_chapter_title(ch_text, global_chapter_count)
        
        if new_title:
            file_name = f'chap_{global_chapter_count}.xhtml'
            chapter = epub.EpubHtml(title=new_title, file_name=file_name, lang='en')
            
            # Fetch summary and clean narrative text
            current_summary = summaries[summary_index] if summary_index < len(summaries) else "No summary available."
            cleaned_text = clean_chapter_content(ch_text)
            
            # Structure HTML with visible <h1> and a gray-box italicized summary
            chapter_content = f'''
                <h1 class="chapter-title">{new_title}</h1>
                <details class="summary-box">
                    <summary>Chapter Summary (Click to expand)</summary>
                    <div class="summary-content">
                        {current_summary}
                    </div>
                </details>
                <div class="main-body">
                    {cleaned_text}
                </div>
            '''
            chapter.content = chapter_content
            book.add_item(chapter)
            epub_chapters.append(chapter)
            
            summary_index += 1
            global_chapter_count += 1

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # CSS for the Gray Box, Italics, and Clean Text
    style = '''
        h1.chapter-title { text-align: center; color: #333; margin-bottom: 1.2em; }
        
        /* The Gray Box summary styling */
        .summary-box { 
            margin-bottom: 25px; 
            background-color: #f6f6f6; /* Gray background for the box */
            border: 1px solid #ddd; 
            border-radius: 4px;
        }
        
        summary { 
            padding: 12px; 
            background-color: #f0f0f0; 
            cursor: pointer; 
            font-weight: bold; 
            list-style: none;
            border-bottom: 1px solid #ddd;
        }
        
        .summary-content { 
            padding: 15px; 
            font-style: italic; /* Italics for the summary content */
            color: #444;
        }

        .original-text { color: #000; margin-top: 1.5em; display: block; }
        .translation-content { color: #666; font-style: italic; margin-bottom: 1.5em; display: block; }
    '''
    
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    book.spine = ['nav'] + epub_chapters
    
    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] Created clean EPUB with {global_chapter_count - 1} chapters.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary_file", required=True) # Used exactly as per your command
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    build_epub(args.input, args.summary_file, args.output)

