import os, sys, re, asyncio
import edge_tts
from bs4 import BeautifulSoup
from pydub import AudioSegment

# --- CONFIGURATION ---
# Voices: Henri (FR) is literary and calm; Guy (EN) is a clear narrator.
VOICE_FR = "fr-FR-HenriNeural" 
VOICE_EN = "en-US-GuyNeural"
SILENCE_GAP = 1500 # Milliseconds between segments

async def generate_speech(text, voice, output_path):
    """Synthesizes a single text segment to MP3."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def parse_bilingual_text(file_path):
    """Extracts metadata and segments from the working text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Metadata Interrogation
    title_match = re.search(r"TITLE: (.*)", content)
    author_match = re.search(r"AUTHOR: (.*)", content)
    title = title_match.group(1).strip() if title_match else "Unknown Title"
    author = author_match.group(1).strip() if author_match else "Unknown Author"

    # Split by the section separator
    chunks = content.split('========================================')
    segments = []

    for chunk in chunks:
        if "ORIGINAL" not in chunk: continue
        soup = BeautifulSoup(chunk, 'html.parser')
        
        # Pull original French and contemporary English
        original_div = soup.find('div', class_='original-text')
        translation_div = soup.find('div', class_='translation-content')
        
        if original_div:
            # Clean text (removing section markers)
            fr_text = re.sub(r'### SECTION \d+ ORIGINAL', '', original_div.get_text()).strip()
            en_text = translation_div.get_text().strip() if translation_div else ""
            segments.append((fr_text, en_text))
            
    return title, author, segments

async def main(file_path, start_from=1):
    """Main loop with slicing logic to start at a specific segment."""
    title, author, segments = parse_bilingual_text(file_path)
    
    # Adjust for 0-based indexing
    start_idx = max(0, start_from - 1)
    active_segments = segments[start_idx:]
    
    print(f"[*] Generating Interleaved Audio for: {title} by {author}")
    print(f"[*] Starting from segment {start_from} of {len(segments)}")
    
    combined_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=SILENCE_GAP)

    # Iterate only through the requested segments
    for i, (fr, en) in enumerate(active_segments, start=start_idx):
        print(f"[*] Processing Segment {i+1}/{len(segments)}...", end=" ", flush=True)
        
        # Temp files for this segment
        fr_tmp, en_tmp = f"tmp_fr_{i}.mp3", f"tmp_en_{i}.mp3"
        
        # 1. Synthesize French
        await generate_speech(fr, VOICE_FR, fr_tmp)
        fr_audio = AudioSegment.from_mp3(fr_tmp)
        
        # 2. Synthesize English (if translation exists)
        seg_audio = fr_audio + silence
        if en:
            await generate_speech(en, VOICE_EN, en_tmp)
            en_audio = AudioSegment.from_mp3(en_tmp)
            seg_audio += en_audio + (silence * 2) # Extra gap after the pair
            os.remove(en_tmp)
        
        combined_audio += seg_audio
        os.remove(fr_tmp)
        print("Done.")

    # Create filename reflecting the starting point if not starting at 1
    suffix = f"_from_{start_from}" if start_from > 1 else ""
    output_filename = os.path.splitext(file_path)[0] + f"{suffix}.mp3"
    
    combined_audio.export(output_filename, format="mp3", tags={'title': title, 'artist': author})
    print(f"\n[SUCCESS] Audiobook created: {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 build_audio.py <bilingual_text_file.txt> [start_segment_number]")
    else:
        # Default to 1 if no second argument is provided
        start_seg = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        asyncio.run(main(sys.argv[1], start_seg))

