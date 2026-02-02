import os
from bs4 import BeautifulSoup

def append_br_to_lines(directory="."):
    for filename in os.listdir(directory):
        if filename.endswith(".html") and "Canto" in filename:
            with open(filename, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            # Cerca i div che contengono il testo originale
            # Usa 'source-text' o 'original' in base alla classe nel tuo HTML
            targets = soup.find_all(class_=['source-text', 'original'])

            for target in targets:
                # Recupera il testo preservando i ritorni a capo esistenti
                lines = target.get_text().splitlines()
                
                # Svuota il contenitore e ricostruiscilo con i <br/>
                target.clear()
                for i, line in enumerate(lines):
                    target.append(line.strip())
                    # Aggiunge <br/> alla fine di ogni riga, tranne l'ultima se preferisci
                    target.append(soup.new_tag("br"))
                    # Aggiunge un newline reale nel codice per leggibilità
                    target.append("\n")

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"[*] Elaborato: {filename}")

if __name__ == "__main__":
    append_br_to_lines()

