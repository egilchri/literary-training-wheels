import os, sys, re, asyncio, argparse
from bs4 import BeautifulSoup
import edge_tts

async def synthesize_chapter(text, output_path, voice="en-GB-SoniaNeural"):
    """
    Asynchronously generates an MP3. 
    Final cleanup ensures NO technical markers reach the AI voice.
    """
    # 1. REMOVE TECHNICAL MARKERS: Specifically target the SECTION tags
    tts_clean = re.sub(r'### SECTION \d+ (ORIGINAL|TRANSLATED)', '', text)
    
    # 2. COLLAPSE ALL WHITESPACE: Ensures smooth, non-choppy audio
    tts_text = " ".join(tts_clean.split())
    
    if not tts_text:
        return

    communicate = edge_tts.Communicate(tts_text, voice)
    try:
        await communicate.save(output_path)
        print(f"[*] Audio saved: {output_path}")
    except Exception as e:
        print(f"[!] Error synthesizing {output_path}: {e}")

async def build_audio_task(input_txt, output_dir, dry_run=False, limit=None):
    if not dry_run and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_chapters = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    
    processed_count = 0
    current_ch_num = 1
    audio_tasks = []

    for ch_text in raw_chapters:
        if limit and processed_count >= limit:
            break

        if not ch_text.strip() or "TITLE:" in ch_text[:100]:
            continue
            
        title_match = re.search(r"## ORIGINAL CHAPTER:\s*(.*)\n", ch_text)
        raw_ch_title = title_match.group(1).strip() if title_match else f"Chapter_{current_ch_num}"
        safe_title = "Introduction" if raw_ch_title.upper() == "CONTENTS" else re.sub(r'\W+', '_', raw_ch_title)
        output_file = os.path.join(output_dir, f"{current_ch_num:02d}_{safe_title}.mp3")

        soup = BeautifulSoup(ch_text, 'html.parser')
        original_blocks = soup.find_all('div', class_='original-text')
        
        filled_paragraphs = []
        for block in original_blocks:
            # Extract text and immediately strip any hidden markers
            raw_text = block.get_text()
            # Remove the SECTION markers from the text content
            clean_p = re.sub(r'### SECTION \d+ (ORIGINAL|TRANSLATED)', '', raw_text)
            
            # FILL: Turn the choppy paragraph into a single continuous line
            filled_p = " ".join(clean_p.split()).strip()
            if filled_p:
                filled_paragraphs.append(filled_p)

        full_chapter_text = "\n\n".join(filled_paragraphs)

        if full_chapter_text.strip():
            if dry_run:
                # The "START DUMP" markers are ONLY in the print statement, 
                # they are never passed to the audio function.
                print(f"\n{'='*25} START DUMP: {safe_title} {'='*25}")
                print(full_chapter_text)
                print(f"{'='*25} END DUMP: {safe_title} {'='*25}\n")
            else:
                audio_tasks.append(synthesize_chapter(full_chapter_text, output_file))
            
            processed_count += 1
        current_ch_num += 1
    
    if audio_tasks:
        print(f"[*] Synthesizing {len(audio_tasks)} chapters...")
        await asyncio.gather(*audio_tasks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output_dir", required=True)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("-n", "--num_chapters", type=int, default=None)
    args = parser.parse_args()
    
    asyncio.run(build_audio_task(args.input, args.output_dir, args.dry_run, args.num_chapters))

