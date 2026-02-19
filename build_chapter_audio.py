import os, sys, re, asyncio, argparse
from bs4 import BeautifulSoup
from pydub import AudioSegment
import edge_tts

# Configuration for the narrator
VOICE = "en-GB-SoniaNeural"

async def synthesize_to_segment(text, voice=VOICE):
    """Synthesizes text to an AudioSegment."""
    temp_file = f"temp_{asyncio.current_task().get_name()}.mp3"
    # Clean text to ensure the TTS engine handles it smoothly
    clean_text = " ".join(text.split())
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(temp_file)
    segment = AudioSegment.from_mp3(temp_file)
    os.remove(temp_file)
    return segment

def is_strictly_roman(text):
    """Matches standalone Roman numerals like 'VII' or 'I'."""
    pattern = r"^\s*[ivxlcdm]+\s*$"
    return bool(re.match(pattern, text, re.IGNORECASE))

async def build_audiobook(input_txt, output_mp3, num_chapters=None, dry_run=False):
    if not os.path.exists(input_txt):
        print(f"[!] Input file not found: {input_txt}")
        return

    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split using the divider produced by translate_epub.py
    raw_sections = re.split(r'={40}', content)
    
    full_audiobook = AudioSegment.empty()
    silence_gap = AudioSegment.silent(duration=2000) 
    
    individual_dir = "individual_chapters"
    if not dry_run:
        os.makedirs(individual_dir, exist_ok=True)

    # Tracking variables
    current_chapter_title = None
    current_chapter_accumulator = []
    js_map = {}
    cumulative_seconds = 0.0
    processed_chapters = 0

    # Regex to find the <h2> tag with ONLY a Roman Numeral
    ROMAN_H2_RE = r"<h2[^>]*?>\s*([ivxlcdm]+)\s*</h2>"

    print(f"[*] Analyzing sections for narrative chapters...")

    for section in raw_sections:
        if not section.strip():
            continue

        # Detect Chapter Header
        header_match = re.search(ROMAN_H2_RE, section, re.IGNORECASE)
        
        if header_match:
            # Finalize previous chapter audio before starting the next
            if current_chapter_title and current_chapter_accumulator:
                result = await process_audio_chapter(
                    current_chapter_title, 
                    current_chapter_accumulator, 
                    individual_dir, 
                    js_map, 
                    cumulative_seconds, 
                    dry_run
                )
                
                if result:
                    chapter_audio, new_offset = result
                    if not dry_run:
                        full_audiobook += chapter_audio + silence_gap
                    cumulative_seconds = new_offset
                    processed_chapters += 1
                
                if num_chapters and processed_chapters >= num_chapters:
                    current_chapter_title = None # Stop accumulation
                    break

            current_chapter_title = header_match.group(1).upper().strip()
            current_chapter_accumulator = []
            print(f"[*] Found Chapter {current_chapter_title}...")
            continue

        # Accumulate prose while inside a chapter
        if current_chapter_title:
            original_match = re.search(r"### SECTION \d+ ORIGINAL\n(.*?)(?=\n<details>|### SECTION|$)", section, re.DOTALL)
            if original_match:
                clean_prose = re.sub(r'<[^>]+>', '', original_match.group(1)).strip()
                if clean_prose:
                    current_chapter_accumulator.append(clean_prose)

    # Process the final chapter
    if current_chapter_title and current_chapter_accumulator:
        if not num_chapters or processed_chapters < num_chapters:
            result = await process_audio_chapter(
                current_chapter_title, 
                current_chapter_accumulator, 
                individual_dir, 
                js_map, 
                cumulative_seconds, 
                dry_run
            )
            if result and not dry_run:
                chapter_audio, _ = result
                full_audiobook += chapter_audio + silence_gap

    if not dry_run:
        full_audiobook.export(output_mp3, format="mp3")
        print(f"\n[*] Audiobook saved to: {output_mp3}")
        
        # Print the Map for index.html
        print("\n" + "="*30)
        print("COPY THIS TO YOUR index.html SCRIPT:")
        print("="*30)
        print("const chapterMap = {")
        for name, sec in js_map.items():
            print(f'    "Chapter {name}": {sec},')
        print("};")
        print("="*30)

async def process_audio_chapter(title, text_list, out_dir, js_map, offset, dry_run):
    full_text = " ".join(text_list).strip()
    # Length filter to ignore structural fragments or empty chapters
    if not full_text or len(full_text) < 150:
        return None

    if dry_run:
        print(f"    [DRY RUN] Would synthesize Chapter {title} ({len(full_text)} chars)")
        # Estimated time for dry run (roughly 150 words per minute)
        est_seconds = (len(full_text) / 5) / 2.5 
        js_map[title] = round(offset, 2)
        return None, offset + est_seconds + 2.0

    print(f"    - Synthesizing Chapter {title}...")
    try:
        chapter_audio = await synthesize_to_segment(full_text)
        
        # Save individual file
        safe_name = f"Chapter_{title}.mp3"
        chapter_audio.export(os.path.join(out_dir, safe_name), format="mp3")
        
        # Update Map
        js_map[title] = round(offset, 2)
        
        # Calculate new offset (duration + 2s gap)
        new_offset = offset + (len(chapter_audio) / 1000.0) + 2.0
        return chapter_audio, new_offset
    except Exception as e:
        print(f"    [!] Error synthesizing Chapter {title}: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build audiobook from bilingual translation text.")
    parser.add_argument("-i", "--input", required=True, help="Input .txt file from translator")
    parser.add_argument("-o", "--output", required=True, help="Output master .mp3 file")
    parser.add_argument("-n", "--num_chapters", type=int, default=None, help="Limit number of chapters")
    parser.add_argument("--dry-run", action="store_true", help="Count chapters without synthesizing")
    
    args = parser.parse_args()
    
    asyncio.run(build_audiobook(args.input, args.output, args.num_chapters, args.dry_run))

    
