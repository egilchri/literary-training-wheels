import os, re, argparse
from ebooklib import epub

def parse_summaries(summary_file):
    summaries = {}
    if not summary_file or not os.path.exists(summary_file):
        return summaries

    current_title = None
    current_content = []
    is_capturing_summary = False

    with open(summary_file, 'r', encoding='utf-8') as f:
        for line in f:
            line_stripped = line.strip()
            
            # 1. Detect New Chapter Title
            title_match = re.match(r"^TITLE:\s*(.*)", line)
            if title_match:
                if current_title:
                    summaries[current_title] = " ".join(current_content).strip()
                current_title = re.sub(r'^chapter\s+', '', title_match.group(1).strip().lower())
                current_content = []
                is_capturing_summary = False
                continue

            # 2. Detect Summary Start
            if line.startswith("SUMMARY:"):
                is_capturing_summary = True
                content = line.replace("SUMMARY:", "").strip()
                if content:
                    current_content.append(content)
                continue

            # 3. Detect Content Start (STOP capturing summary here)
            if line.startswith("CONTENT:"):
                is_capturing_summary = False
                continue

            # 4. Collect lines only if we are in the summary block
            if is_capturing_summary and current_title and line_stripped:
                # Ignore the separator lines
                if line_stripped != "=" * 40:
                    current_content.append(line_stripped)

        # Catch the last one
        if current_title:
            summaries[current_title] = " ".join(current_content).strip()
            
    return summaries
    

def build_bilingual_epub(input_txt, output_epub, summary_file=None):
    book = epub.EpubBook()
    
    title, author = "Unknown Title", "Unknown Author"
    if os.path.exists(input_txt):
        with open(input_txt, 'r', encoding='utf-8') as f:
            for _ in range(15): 
                line = f.readline()
                if not line: break
                if line.startswith("TITLE:"): title = line.replace("TITLE:", "").strip()
                if line.startswith("AUTHOR:"): author = line.replace("AUTHOR:", "").strip()

    book.set_title(title)
    book.add_author(author)
    book.set_identifier("bilingual_edition_" + re.sub(r'\W+', '', title))

    chapter_summaries = parse_summaries(summary_file) if summary_file else {}
    chapters = []
    current_ch_num = 1
    
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()
    
    raw_chapters = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)

    for ch_text in raw_chapters:
        if not ch_text.strip() or "TITLE:" in ch_text[:100]:
            continue
            
        title_match = re.search(r"## ORIGINAL CHAPTER:\s*(.*)\n", ch_text)
        raw_ch_title = title_match.group(1).strip() if title_match else f"{current_ch_num}"
        
        # Normalize mapping for Introduction
        norm_title = "introduction" if raw_ch_title.upper() == "CONTENTS" else re.sub(r'^chapter\s+', '', raw_ch_title.lower())
        display_title = "Introduction" if norm_title == "introduction" else f"Chapter {raw_ch_title}"

        # 1. First, replace SECTION markers with unique placeholders so they don't get joined into paragraphs
        processed_body = re.sub(r'### SECTION \d+ ORIGINAL', '\n\n[[ORIGINAL_LABEL]]\n\n', ch_text)
        processed_body = re.sub(r'### SECTION \d+ TRANSLATED', '\n\n[[TRANSLATED_LABEL]]\n\n', processed_body)

        # 2. Remove technical headers
        processed_body = re.sub(r"## (ORIGINAL|TRANSLATED) CHAPTER:.*\n", "", processed_body)
        processed_body = re.sub(r"#{10,}|={10,}", "", processed_body)
        
        # 3. Process into paragraphs
        raw_blocks = processed_body.strip().split('\n\n')
        final_html_parts = []
        
        for block in raw_blocks:
            joined_text = block.replace('\n', ' ').strip()
            if not joined_text:
                continue
                
            if joined_text == "[[ORIGINAL_LABEL]]":
                final_html_parts.append('<p style="margin-top: 1.5em; font-weight: bold; color: #444;">[Original]</p>')
            elif joined_text == "[[TRANSLATED_LABEL]]":
                final_html_parts.append('<p style="margin-top: 1.5em; font-weight: bold; color: #444;">[Translation]</p>')
            else:
                # This is the actual story text
                final_html_parts.append(f'<p style="margin-bottom: 0.8em;">{joined_text}</p>')

        summary_html = ""
        if norm_title in chapter_summaries:
            summary_html = f"""
            <details style="background-color: #f4f4f4; padding: 10px; border: 1px solid #ccc; border-radius: 4px; margin: 10px 0;">
                <summary style="font-weight: bold; cursor: pointer;">Show Chapter Summary</summary>
                <div style="margin-top: 8px; font-style: italic; color: #555;">{chapter_summaries[norm_title]}</div>
            </details>
            """

        c = epub.EpubHtml(title=display_title, file_name=f'chap_{current_ch_num}.xhtml', lang='en')
        c.content = f'<h1 style="margin-bottom: 0.3em;">{display_title}</h1>{summary_html}<div>{"".join(final_html_parts)}</div>'
        
        book.add_item(c)
        chapters.append(c)
        current_ch_num += 1

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters

    epub.write_epub(output_epub, book)
    print(f"[*] Created EPUB: {output_epub}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-s", "--summary_file")
    args = parser.parse_args()
    build_bilingual_epub(args.input, args.output, args.summary_file)

