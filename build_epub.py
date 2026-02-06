import os, re, argparse
from ebooklib import epub

def parse_summaries(summary_file):
    summaries = {}
    if not summary_file or not os.path.exists(summary_file):
        return summaries

    current_title = None
    current_content = []

    with open(summary_file, 'r', encoding='utf-8') as f:
        for line in f:
            title_match = re.match(r"^TITLE:\s*(.*)", line)
            if title_match:
                if current_title:
                    summaries[current_title] = " ".join(current_content).strip()
                current_title = re.sub(r'^chapter\s+', '', title_match.group(1).strip().lower())
                current_content = []
            elif line.startswith("SUMMARY:"):
                content = line.replace("SUMMARY:", "").strip()
                if content: current_content.append(content)
            elif line.strip() in ["-" * 20, "=" * 40]:
                continue
            elif current_title and line.strip():
                current_content.append(line.strip())

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
            
        # Extract title (e.g., "I")
        title_match = re.search(r"## ORIGINAL CHAPTER:\s*(.*)\n", ch_text)
        raw_ch_title = title_match.group(1).strip() if title_match else f"{current_ch_num}"
        
        # CLEANUP: Remove technical markers and excessive whitespace
        clean_body = re.sub(r"## ORIGINAL CHAPTER:.*\n", "", ch_text)
        clean_body = re.sub(r"## TRANSLATED CHAPTER:.*\n", "", clean_body)
        clean_body = re.sub(r"#{10,}", "", clean_body)
        clean_body = re.sub(r"={10,}", "", clean_body)
        
        # Replace section markers with a simple bold label and NO extra breaks
        clean_body = re.sub(r'### SECTION \d+ ORIGINAL', '<p><b>[Original]</b></p>', clean_body)
        clean_body = re.sub(r'### SECTION \d+ TRANSLATED', '<p><b>[Translation]</b></p>', clean_body)

        norm_title = re.sub(r'^chapter\s+', '', raw_ch_title.lower())
        
        summary_html = ""
        if norm_title in chapter_summaries:
            # Removed the <hr/> and slashed margins to kill the whitespace
            summary_html = f"""
            <details style="background-color: #f4f4f4; padding: 10px; border: 1px solid #ccc; border-radius: 4px; margin: 10px 0;">
                <summary style="font-weight: bold; cursor: pointer;">Show Chapter Summary</summary>
                <div style="margin-top: 8px; font-style: italic;">{chapter_summaries[norm_title]}</div>
            </details>
            """

        # Convert remaining newlines to paragraphs for better spacing control
        paragraphs = clean_body.strip().split('\n')
        html_body = "".join([f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()])

        c = epub.EpubHtml(title=f"Chapter {raw_ch_title}", file_name=f'chap_{current_ch_num}.xhtml', lang='en')
        # Combined title and body with tight CSS
        c.content = f"""
            <h1 style="margin-bottom: 5px;">Chapter {raw_ch_title}</h1>
            {summary_html}
            <div class="chapter-content">{html_body}</div>
        """
        
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

