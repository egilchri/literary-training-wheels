import os, sys, re, asyncio, argparse
from bs4 import BeautifulSoup
from pydub import AudioSegment
import edge_tts

# --- CONFIGURATION ---
VOICE_MAP = {
    "french": "fr-FR-HenriNeural",
    "italian": "it-IT-DiegoNeural",
    "spanish": "es-ES-AlvaroNeural",
    "danish": "da-DK-JeppeNeural",
    "swedish": "sv-SE-MattiasNeural",
    "portuguese": "pt-PT-DuarteNeural",
    "norwegian": "nb-NO-FinnNeural",
    "british": "en-GB-RyanNeural"
}
VOICE_EN = "en-US-GuyNeural"
SILENCE_GAP = 1500 
RETRIES = 3         

def speed_to_tts_rate(speed_decimal):
    return f"{(speed_decimal - 1) * 100:+.0f}%"

async def generate_speech(text, voice, output_path, *, speed=1.0):
    clean_text = text.replace("Enough thinking", "").strip()
    if not clean_text or len(clean_text) < 2: return False
    rate_str = speed_to_tts_rate(speed)
    for attempt in range(RETRIES):
        try:
            communicate = edge_tts.Communicate(clean_text, voice, rate=rate_str)
            await communicate.save(output_path)
            return True
        except Exception:
            if attempt < RETRIES - 1: await asyncio.sleep(2)
            else: return False

def parse_summaries(summary_file):
    """Maps section numbers to Canto names and summaries[cite: 529]."""
    canto_map = {}
    if not summary_file or not os.path.exists(summary_file): return canto_map
    with open(summary_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # pattern = re.compile(r"NARRATIVE SUMMARY:\s*(.*?)\s*\(SECTIONS\s*(\d+)-\d+\)\n-+\n(.*?)(?=\n-|\Z)", re.DOTALL)
    # \h* matches horizontal whitespace (spaces/tabs) without crossing into a new line
    pattern = re.compile(r"NARRATIVE SUMMARY:\s*(.*?)\s*\(SECTIONS\s*(\d+)-\d+\)[ \t]*\n-+\n(.*?)(?=\n-|\Z)", re.DOTALL)
    for match in pattern.finditer(content):
        canto_map[int(match.group(2))] = {"name": match.group(1).strip(), "summary": match.group(3).strip()}
    return canto_map

def generate_html_player(title, summary, segments, mp3_filename):
    """Creates a new HTML file for a Canto with a summary div."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: 'Georgia', serif; line-height: 1.6; padding: 50px; background: #f4f4f9; color: #333; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #2c3e50; }}
            .summary-box {{ background: #f0f4f8; border-left: 5px solid #2c3e50; padding: 15px; margin-bottom: 25px; font-style: italic; }}
            .player-sticky {{ position: sticky; top: 0; background: white; padding: 20px 0; border-bottom: 2px solid #eee; z-index: 100; }}
            audio {{ width: 100%; }}
            .segment {{ margin-bottom: 30px; padding: 15px; border-left: 4px solid #ccc; }}
            .source-text {{ font-size: 1.2em; color: #2980b9; font-weight: bold; }}
            .translation {{ font-style: italic; color: #7f8c8d; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <div class="summary-box">{summary}</div>
            <div class="player-sticky"><audio controls src="{mp3_filename}"></audio></div>
            <div id="content">
    """
    for src, en in segments:
        html_content += f'<div class="segment"><div class="source-text">{src}</div><div class="translation">{en}</div></div>'
    html_content += "</div></div></body></html>"
    
    html_filename = mp3_filename.replace(".mp3", ".html")
    with open(html_filename, "w", encoding="utf-8") as f: f.write(html_content)

def parse_bilingual_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    title = re.search(r"TITLE: (.*)", content).group(1).strip() if "TITLE:" in content else "Unknown"
    author = re.search(r"AUTHOR: (.*)", content).group(1).strip() if "AUTHOR:" in content else "Unknown"
    segments = []
    for chunk in content.split('========================================'):
        if "ORIGINAL" not in chunk: continue
        soup = BeautifulSoup(chunk, 'html.parser')
        orig = soup.find('div', class_='original-text')
        tran = soup.find('div', class_='translation-content')
        if orig:
            s = re.sub(r'### SECTION \d+ ORIGINAL', '', orig.get_text()).strip()
            e = re.sub(r'<[^>]+>', '', tran.get_text()).strip() if tran else ""
            segments.append((s, e))
    return title, author, segments

async def main(file_path, start_from=1, speed=1.0, lang="french", summary_file=None, num_cantos=0):
    title, author, segments = parse_bilingual_text(file_path)
    canto_map = parse_summaries(summary_file)
    voice_code = VOICE_MAP.get(lang.lower(), "fr-FR-HenriNeural")
    
    combined_audio = AudioSegment.empty()
    current_canto_segments = []
    current_canto_info = {"name": f"{title}_Start", "summary": "Introductory sections."}
    silence = AudioSegment.silent(duration=SILENCE_GAP)

    # Initialize this before the loop
    cantos_processed = 0

    for i, (src, en) in enumerate(segments, start=1):
        if i < start_from: continue
        
        # Trigger split if this section starts a new Canto [cite: 558, 565]
        if i in canto_map:
            if current_canto_segments:
                fname = f"{current_canto_info['name'].replace(' ', '_')}_speed_{speed}.mp3"
                combined_audio.export(fname, format="mp3")
                generate_html_player(current_canto_info['name'], current_canto_info['summary'], current_canto_segments, fname)
                combined_audio = AudioSegment.empty()
                current_canto_segments = []
                cantos_processed += 1
                if num_cantos > 0 and cantos_processed >= num_cantos:
                    print(f"[*] Reached limit of {num_cantos} cantos. Exiting.")
                    return
            current_canto_info = canto_map[i]
            print(f"[*] Starting {current_canto_info['name']}")

        src_tmp, en_tmp = f"tmp_s_{i}.mp3", f"tmp_e_{i}.mp3"
        if await generate_speech(src, voice_code, src_tmp, speed=speed):
            combined_audio += AudioSegment.from_mp3(src_tmp) + silence
            if en and await generate_speech(en, VOICE_EN, en_tmp):
                combined_audio += AudioSegment.from_mp3(en_tmp) + (silence * 2)
                os.remove(en_tmp)
            os.remove(src_tmp)
            current_canto_segments.append((src, en))
            print(f"Processed Segment {i}")

    if current_canto_segments:
        fname = f"{current_canto_info['name'].replace(' ', '_')}_speed_{speed}.mp3"
        combined_audio.export(fname, format="mp3")
        generate_html_player(current_canto_info['name'], current_canto_info['summary'], current_canto_segments, fname)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("-summary_file", "--summary_file", help="Path to summaries file")
    parser.add_argument("-start", type=int, default=1)
    parser.add_argument("-speed", type=float, default=1.0)
    parser.add_argument("-lang", type=str, default="french")
    parser.add_argument("-num_cantos", type=int, default=0, help="Number of Cantos to process before exiting")
    args = parser.parse_args()
    asyncio.run(main(args.input_file, args.start, args.speed, args.lang, args.summary_file, args. num_cantos))



