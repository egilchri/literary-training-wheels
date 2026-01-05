import os, sys, re
from ebooklib import epub

def create_bilingual_epub(txt_source, output_epub):
    book = epub.EpubBook()
    book.set_identifier('id123456')
    book.set_title('The Turn of the Screw (Bilingual Edition)')
    book.set_language('en')
    book.add_author('Henry James / Gemini AI')

    # --- TYPOGRAPHY (CSS) ---
    style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        body { font-family: "Georgia", serif; padding: 1.5em; line-height: 1.7; background-color: #ffffff; }
        
        /* The Native Paragraph Rule for Spacing & Justification */
        p {
            text-align: justify !important;
            text-justify: inter-word;
            margin-bottom: 1.2em;
            text-indent: 1.5em;
            display: block;
        }

        .original-text { color: #000000; margin-bottom: 2em; }
        .translation-content { 
            font-family: "Helvetica", sans-serif; font-style: italic; color: #444444; 
            background-color: #f9f9f9; padding: 15px; border-left: 3px solid #005a9c; margin-bottom: 2em;
        }
        .translation-content p { text-indent: 0 !important; text-align: left !important; }
        summary { color: #005a9c; font-family: "Helvetica", sans-serif; font-weight: bold; cursor: pointer; padding: 10px; background: #f0f4f8; border-radius: 5px; }
        .scene-break { display: block; height: 3em; text-align: center; }
    '''

    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    with open(txt_source, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step A: Handle Scene Breaks
    content = re.sub(r'\n{3,}', '<div class="scene-break">&nbsp;</div>', content)

    # Step B: Inject <p> tags into Translation blocks
    def fix_trans(m):
        inner = m.group(1).strip()
        paras = inner.split('\n\n')
        wrapped = "".join([f"<p>{p.strip()}</p>" for p in paras if p.strip()])
        return f'<div class="translation-content">{wrapped}</div>'
    content = re.sub(r'<div class="translation-content">(.*?)</div>', fix_trans, content, flags=re.DOTALL)

    # Step C: Inject <p> tags into Original blocks
    def fix_orig(m):
        inner = m.group(1).strip()
        lines = inner.split('\n')
        # Preserve the Section Header and wrap the rest in <p>
        header = f"<strong>{lines[0]}</strong>" if lines[0].startswith('###') else ""
        body = "\n".join(lines[1:]) if header else inner
        paras = body.split('\n\n')
        wrapped_body = "".join([f"<p>{p.strip()}</p>" for p in paras if p.strip()])
        return f'<div class="original-text justify-text">{header}{wrapped_body}</div>'
    content = re.sub(r'<div class="original-text justify-text">(.*?)</div>', fix_orig, content, flags=re.DOTALL)

    # Final Binding
    c1 = epub.EpubHtml(title='Bilingual Text', file_name='chap_1.xhtml', lang='en')
    c1.add_link(href='style/nav.css', rel='stylesheet', type='text/css')
    c1.content = f"<html><head></head><body>{content}</body></html>"
    book.add_item(c1)
    book.spine = ['nav', c1]
    epub.write_epub(output_epub, book, {})
    print(f"\n[SUCCESS] Structured EPUB created at: {output_epub}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        create_bilingual_epub(sys.argv[1], sys.argv[2])

