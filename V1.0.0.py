import os
import re
import requests

# Translation dictionary with half the languages (English and Polish), matching beta 3.py structure
LOCALIZATION = {
    "en": {
        "title": "🎵 Album Cover Downloader 🎵",
        "exit_msg": "Goodbye! 👋",
        "song_prompt": "Enter the song name (or type 'exit' to quit): ",
        "artist_prompt": "Enter the artist name (optional): ",
        "searching": "Searching for album cover for: '{}'...",
        "found_header": "\n--- Match Found! ---\n",
        "save_prompt": "Do you want to save this album cover? (y/n): ",
        "saved_success": "✅ Album cover successfully saved to {}",
        "not_found": "\n❌ Sorry, no matches found for that track.",
        "error_msg": "\nAn error occurred: {}",
        "loop_restart": "\n--- Restarting Search ---"
    },
    "pl": {
        "title": "🎵 Wyszukiwarka Okładek Albumów 🎵",
        "exit_msg": "Do widzenia! 👋",
        "song_prompt": "Wpisz tytuł piosenki (lub wpisz 'exit', aby wyjść): ",
        "artist_prompt": "Wpisz wykonawcę (opcjonalnie): ",
        "searching": "Szukanie okładki albumu dla: '{}'...",
        "found_header": "\n--- Znaleziono dopasowanie! ---\n",
        "save_prompt": "Czy chcesz zapisać tę okładkę albumu? (t/n): ",
        "saved_success": "✅ Okładka albumu została pomyślnie zapisana w {}",
        "not_found": "\n❌ Niestety, nie znaleziono dopasowania dla tego utworu.",
        "error_msg": "\nWystąpił błąd: {}",
        "loop_restart": "\n--- Restartowanie Wyszukiwania ---"
    }
}

valid_affirmations = ['y', 'yes', 't', 'tak']

def sanitize_filename(name):
    """Removes invalid characters to make a safe filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def choose_language():
    while True:
        # UI prompt structured exactly like the upload screenshot
        print("Select your language / Wybierz język:")
        print("1. English (en)")
        print("2. Polish (pl)")
        
        choice = input("Enter number or language code (default 'en'): ").strip().lower()
        if not choice:
            return "en"
            
        if choice == "1" or choice == "en":
            return "en"
        elif choice == "2" or choice == "pl":
            return "pl"
        
        print("Invalid choice, defaulting to English.")
        return "en"

def main():
    # Language selection runs only once at start
    lang_code = choose_language()
    txt = LOCALIZATION[lang_code]
    
    print("\n" + "="*40)
    print(txt['title'])
    print("="*40)
    
    while True:
        song_name = input("\n" + txt['song_prompt']).strip()
        if song_name.lower() == 'exit':
            print(txt['exit_msg'])
            break
            
        if not song_name:
            continue
            
        artist_name = input(txt['artist_prompt']).strip()
        
        if artist_name:
            search_query = f"{song_name} {artist_name}"
        else:
            search_query = song_name
            
        print(txt['searching'].format(search_query))
        
        url = "https://itunes.apple.com/search"
        params = {
            "term": search_query,
            "media": "music",
            "entity": "song",
            "limit": 1
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["resultCount"] > 0:
                track = data["results"][0]
                found_track = track.get("trackName", "Unknown Song")
                found_artist = track.get("artistName", "Unknown Artist")
                found_album = track.get("collectionName", "Unknown Album")
                
                artwork_url = track.get("artworkUrl100")
                if artwork_url:
                    artwork_url = artwork_url.replace("100x100bb", "1000x1000bb")
                else:
                    print(txt['not_found'])
                    print(txt['loop_restart'])
                    continue
                
                print(txt['found_header'])
                print(f"🎵 Song: {found_track}")
                print(f"👤 Artist: {found_artist}")
                print(f"💿 Album: {found_album}")
                print("\n----------------------------\n")
                
                save = input(txt['save_prompt']).lower().strip()
                if save in valid_affirmations:
                    filename = sanitize_filename(f"{found_artist} - {found_album}.jpg")
                    
                    img_data = requests.get(artwork_url).content
                    with open(filename, "wb") as handler:
                        handler.write(img_data)
                    print(txt['saved_success'].format(os.path.abspath(filename)))
            else:
                print(txt['not_found'])
                
        except Exception as e:
            print(txt['error_msg'].format(e))
            
        print(txt['loop_restart'])

if __name__ == "__main__":
    main()
