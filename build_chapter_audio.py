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
    communicate = edge_tts.Communicate(" ".join(text.split()), voice)
    await communicate.save(temp_file)
    segment = AudioSegment.from_mp3(temp_file)
    os.remove(temp_file)
    return segment

async def build_audiobook(input_txt, output_mp3, num_chapters=None, dry_run=False):
    if not os.path.exists(input_txt):
        print(f"[!] Input file not found: {input_txt}")
        return

    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split using the Chapter Boundary marker
    raw_blocks = re.split(r'#{40}\n>>> CHAPTER BOUNDARY <<<\n#{40}', content)
    
    full_audiobook = AudioSegment.empty()
    silence_gap = AudioSegment.silent(duration=2000) 
    
    individual_dir = "individual_chapters"
    if not dry_run:
        os.makedirs(individual_dir, exist_ok=True)

    processed_count = 0
    cumulative_seconds = 0
    js_map = {}
    
    # MATCHING LOGIC: Sequential Arabic numbering used in extract_chapters.py
    global_chapter_count = 1 

    print(f"[*] Analyzing {len(raw_blocks)} blocks for audio generation...")

    for block in raw_blocks:
        if num_chapters and processed_count >= num_chapters:
            break
        
        # PATTERN MATCH: Identify real narrative chapters
        match = re.search(r'##\s+ORIGINAL\s+CHAPTER:\s+Chapter\s+([IVXLCDM]+)', block, re.IGNORECASE)
        
        if match:
            chapter_label = f"Chapter {global_chapter_count}"

            # ACCUMULATE TEXT: Collect all narrative paragraphs within the block
            soup = BeautifulSoup(block, 'html.parser')
            original_blocks = soup.find_all('div', class_='original-text')
            
            paragraphs = []
            for section in original_blocks:
                # Clean technical markers to prevent the TTS from reading them
                clean_text = re.sub(r'###\s+SECTION\s+\d+\s+(ORIGINAL|TRANSLATED)', '', section.get_text())
                clean_text = re.sub(r"## (ORIGINAL|TRANSLATED) CHAPTER:.*\n", "", clean_text, flags=re.IGNORECASE)
                
                sub_paras = clean_text.split('\n\n')
                for p in sub_paras:
                    normalized = " ".join(p.split()).strip()
                    if normalized:
                        paragraphs.append(normalized)
            
            if paragraphs:
                if dry_run:
                    print(f"\n{'='*60}")
                    print(f" DRY RUN: {chapter_label}")
                    print(f"{'='*60}")
                    for para in paragraphs:
                        print(f"{para}\n")
                    processed_count += 1
                    global_chapter_count += 1
                    continue

                # Audio Synthesis
                print(f"[*] Processing {chapter_label} ({len(paragraphs)} paragraphs)...")
                chapter_body = "\n\n".join(paragraphs)
                
                # Store timing for the index.html map
                js_map[chapter_label.lower()] = int(cumulative_seconds)

                announcement_text = f"{chapter_label}."
                announcement_audio = await synthesize_to_segment(announcement_text)
                content_audio = await synthesize_to_segment(chapter_body)
                
                # Combine: Announcement -> 1s Pause -> Content
                current_chapter_audio = announcement_audio + AudioSegment.silent(duration=1000) + content_audio
                
                # Export individual chapter file
                individual_filename = os.path.join(individual_dir, f"{chapter_label.replace(' ', '_')}.mp3")
                current_chapter_audio.export(individual_filename, format="mp3")

                # Add to master audiobook with a 2s gap
                full_audiobook += current_chapter_audio + silence_gap
                cumulative_seconds += (len(current_chapter_audio) + 2000) / 1000.0
                
                processed_count += 1
                global_chapter_count += 1

    if dry_run:
        print(f"\n[DRY RUN COMPLETE] Total chapters identified: {processed_count}")
        return

    # Final Export
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
    parser.add_argument("--dry-run", action="store_true", help="Clean text dump of identified chapters")
    args = parser.parse_args()

    asyncio.run(build_audiobook(args.input, args.output, args.num_chapters, args.dry_run))
    
