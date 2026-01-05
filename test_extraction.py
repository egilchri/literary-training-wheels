import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

# Drag your book here again for the path
BOOK_PATH = "/Users/edgargilchrist/tools/BookTransltor/TurnOfTheScrew.epub"

def test_peek():
    print("--- PORTSMOUTH OFFLINE TEST ---")
    if not os.path.exists(BOOK_PATH):
        print(f"[!] Error: File not found at {BOOK_PATH}")
        return

    book = epub.read_epub(BOOK_PATH)
    print(f"[OK] Successfully opened: {os.path.basename(BOOK_PATH)}")
    
    # Just grab the very first section
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    if items:
        soup = BeautifulSoup(items[0].get_content(), 'html.parser')
        text = soup.get_text().strip()
        print(f"[OK] Extracted {len(text)} characters of original text.")
        print("-" * 30)
        print(f"PREVIEW OF BOOK START: {text[:200]}...")
        print("-" * 30)
        print("RESULT: Your Mac is ready. The API is the only thing holding us back.")

if __name__ == "__main__":
    test_peek()
