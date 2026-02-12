import os, sys, re, asyncio, argparse
from bs4 import BeautifulSoup
from pydub import AudioSegment
import edge_tts

# Configuration for the narrator
VOICE = "en-GB-SoniaNeural"

async def synthesize_to_segment(text, voice=VOICE):
    """Synthesizes text to an AudioSegment."""
    temp_file = f"temp_{asyncio.current_task().get_name()}.mp3"
    communicate = edge_tts.Communicate(" ".join(text.split()), voice)
    await communicate.save(temp_file)
    segment = AudioSegment.from_mp3(temp_file)
    os.remove(temp_file)
    return segment

async def build_audiobook(input_txt, output_mp3, num_chapters=None, dry_run=False):
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by the physical boundary markers
    raw_blocks = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    
    full_audiobook = AudioSegment.empty()
    silence_gap = AudioSegment.silent(duration=2000) 
    
    individual_dir = "individual_chapters"
    if not dry_run:
        os.makedirs(individual_dir, exist_ok=True)

    processed_count = 0
    cumulative_seconds = 0
    js_map = {}

    for block in raw_blocks:
        if num_chapters and processed_count >= num_chapters:
            break
        
        # VALIDATE REAL CHAPTER: Look for "## ORIGINAL CHAPTER: Chapter [Roman Numeral]"
        match = re.search(r'## ORIGINAL CHAPTER: (Chapter [IVXLCDM]+)', block)
        if not match:
            continue

        chapter_name = match.group(1) 

        # ACCUMULATE ALL SECTIONS within this chapter boundary
        soup = BeautifulSoup(block, 'html.parser')
        original_blocks = soup.find_all('div', class_='original-text')
        
        paragraphs = []
        for section in original_blocks:
            # Remove internal section markers
            clean_text = re.sub(r'### SECTION \d+ ORIGINAL', '', section.get_text())
            
            # Split by double newlines to find individual paragraphs within the section
            sub_paras = clean_text.split('\n\n')
            for p in sub_paras:
                normalized = " ".join(p.split()).strip()
                if normalized:
                    paragraphs.append(normalized)
        
        if paragraphs:
            if dry_run:
                print(f"\n{'='*60}")
                print(f" DRY RUN: {chapter_name}")
                print(f"{'='*60}")
                for i, para in enumerate(paragraphs, 1):
                    print(f"[{i}] {para}\n")
                processed_count += 1
                continue

            # Processing for Audio
            print(f"[*] Processing {chapter_name} ({len(paragraphs)} paragraphs accumulated)...")
            chapter_body = "\n\n".join(paragraphs)
            
            js_map[chapter_name.lower()] = int(cumulative_seconds)

            announcement_text = f"{chapter_name}."
            announcement_audio = await synthesize_to_segment(announcement_text)
            content_audio = await synthesize_to_segment(chapter_body)
            
            current_chapter_audio = announcement_audio + AudioSegment.silent(duration=1000) + content_audio
            
            individual_filename = os.path.join(individual_dir, f"{chapter_name.replace(' ', '_')}.mp3")
            current_chapter_audio.export(individual_filename, format="mp3")

            full_audiobook += current_chapter_audio + silence_gap
            cumulative_seconds += (len(current_chapter_audio) + 2000) / 1000.0
            processed_count += 1

    if dry_run:
        print(f"\n[DRY RUN COMPLETE] Total chapters found: {processed_count}")
        return

    # Final Master Export
    full_audiobook.export(output_mp3, format="mp3")
    
    # Print the Map for index.html
    print("\n" + "="*30)
    print("COPY THIS TO YOUR index.html SCRIPT:")
    print("="*30)
    print("const chapterMap = {")
    for name, sec in js_map.items():
        print(f'    "{name}": {sec},')
    print("};")
    print("="*30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-n", "--num_chapters", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Show full text dump by paragraph")
    args = parser.parse_args()

    asyncio.run(build_audiobook(args.input, args.output, args.num_chapters, args.dry_run))

