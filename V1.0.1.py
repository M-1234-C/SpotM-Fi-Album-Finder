import os
import re
import time
import requests

# Translation dictionary with half the languages (English and Polish), matching beta 3.py structure
LOCALIZATION = {
    "en": {
        "title": "🎵 Album Cover Downloader 🎵",
        "exit_msg": "Goodbye! 👋",
        "song_prompt": "Enter the song name (or type 'exit' to quit, 'folder' for directory mode): ",
        "artist_prompt": "Enter the artist name (optional): ",
        "searching": "Searching for album cover for: '{}'...",
        "found_header": "\n--- Match Found! ---\n",
        "save_prompt": "Do you want to save this album cover? (y/n): ",
        "saved_success": "✅ Album cover successfully saved to {}",
        "not_found": "\n❌ Sorry, no matches found for that track.",
        "error_msg": "\nAn error occurred: {}",
        "loop_restart": "\n--- Restarting Search ---",
        "already_downloaded": "⏩ Album cover already downloaded.",
        "nav_header": "Current Directory",
        "nav_up": "[..] (Go up one directory)",
        "nav_instructions": "Enter number to navigate, 'S' to select this folder, 'C' to cancel: ",
        "nav_perm_error": "❌ Permission denied. Going back...",
        "nav_invalid": "❌ Invalid selection.",
        "no_music_found": "❌ No music files found in this directory.",
        "rate_limit_msg": "⚠️ Too many requests. Pausing for 8 seconds to recover...",
        # Compact Folder Mode Strings
        "scan_complete": "✨ SCAN COMPLETE SUMMARY ✨",
        "summary_saved": "📥 New covers saved:   {}",
        "summary_skipped": "⏩ Already on disk:    {}",
        "summary_not_found": "❌ Tracks not found:   {}",
        "compact_saved": "✅ Saved cover:    {} -> {} - {}",
        "compact_skipped": "⏩ Skipped (exists): {}",
        "compact_not_found": "❌ Not found:        {}"
    },
    "pl": {
        "title": "🎵 Wyszukiwarka Okładek Albumów 🎵",
        "exit_msg": "Do widzenia! 👋",
        "song_prompt": "Wpisz tytuł piosenki (lub wpisz 'exit' aby wyjść, 'folder' dla trybu katalogu): ",
        "artist_prompt": "Wpisz wykonawcę (opcjonalnie): ",
        "searching": "Szukanie okładki albumu dla: '{}'...",
        "found_header": "\n--- Znaleziono dopasowanie! ---\n",
        "save_prompt": "Czy chcesz zapisać tę okładkę albumu? (t/n): ",
        "saved_success": "✅ Okładka albumu została pomyślnie zapisana w {}",
        "not_found": "\n❌ Niestety, nie znaleziono dopasowania dla tego utworu.",
        "error_msg": "\nWystąpił błąd: {}",
        "loop_restart": "\n--- Restartowanie Wyszukiwania ---",
        "already_downloaded": "⏩ Okładka albumu została już pobrana.",
        "nav_header": "Obecny Katalog",
        "nav_up": "[..] (Przejdź w górę o jeden katalog)",
        "nav_instructions": "Wpisz numer by nawigować, 'S' by wybrać ten folder, 'C' by anulować: ",
        "nav_perm_error": "❌ Odmowa dostępu. Powrót...",
        "nav_invalid": "❌ Nieprawidłowy wybór.",
        "no_music_found": "❌ Nie znaleziono plików muzycznych w tym katalogu.",
        "rate_limit_msg": "⚠️ Za dużo zapytań. Pauza na 8 sekund, aby spróbować ponownie...",
        # Compact Folder Mode Strings
        "scan_complete": "✨ PODSUMOWANIE SKANOWANIA ✨",
        "summary_saved": "📥 Nowe okładki:       {}",
        "summary_skipped": "⏩ Już na dysku:       {}",
        "summary_not_found": "❌ Nie znaleziono:     {}",
        "compact_saved": "✅ Zapisano okładkę:  {} -> {} - {}",
        "compact_skipped": "⏩ Pominięto (pliki): {}",
        "compact_not_found": "❌ Brak okładki dla:  {}"
    }
}

valid_affirmations = ['y', 'yes', 't', 'tak']
valid_audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg', '.aac', '.mp4'}

def sanitize_filename(name):
    """Removes invalid characters to make a safe filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def choose_language():
    while True:
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

def navigate_directories(txt):
    """Interactive directory navigator using numbers."""
    current_path = os.path.expanduser("~") 
    
    while True:
        print(f"\n--- {txt['nav_header']}: {current_path} ---")
        
        try:
            items = os.listdir(current_path)
            dirs = [d for d in items if os.path.isdir(os.path.join(current_path, d)) and not d.startswith('.')]
            dirs.sort()
        except PermissionError:
            print(txt['nav_perm_error'])
            current_path = os.path.dirname(current_path)
            continue

        print(f"0. {txt['nav_up']}")
        for i, d in enumerate(dirs, 1):
            print(f"{i}. {d}")
        
        print("\n----------------------------")
        choice = input(txt['nav_instructions']).strip().upper()
        
        if choice == 'C':
            return None
        elif choice == 'S':
            return current_path
        elif choice == '0':
            current_path = os.path.dirname(current_path)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(dirs):
                current_path = os.path.join(current_path, dirs[idx])
            else:
                print(txt['nav_invalid'])
        else:
            print(txt['nav_invalid'])

def process_folder(folder_path, txt):
    """Scans directory and all its subdirectories cleanly and prints a beautiful layout summary."""
    downloaded_albums = set()
    print(f"\n🚀 Scanning: {folder_path}...")
    
    music_files_found = False
    saved_count = 0
    skipped_count = 0
    not_found_count = 0

    try:
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in valid_audio_extensions:
                    music_files_found = True
                    search_query = os.path.splitext(filename)[0]
                    
                    url = "https://itunes.apple.com/search"
                    params = {
                        "term": search_query,
                        "media": "music",
                        "entity": "song",
                        "limit": 1
                    }
                    
                    try:
                        time.sleep(1) # Base 1-second request safety delay
                        response = requests.get(url, params=params)
                        
                        if response.status_code == 429:
                            print("\n" + txt['rate_limit_msg'])
                            time.sleep(8)
                            response = requests.get(url, params=params)
                            
                        response.raise_for_status()
                        data = response.json()
                        
                        if data["resultCount"] > 0:
                            track = data["results"][0]
                            found_artist = track.get("artistName", "Unknown Artist")
                            found_album = track.get("collectionName", "Unknown Album")
                            
                            album_identifier = f"{found_artist} - {found_album}"
                            img_filename = sanitize_filename(f"{album_identifier}.jpg")
                            out_path = os.path.join(root, img_filename)

                            if album_identifier in downloaded_albums or os.path.exists(out_path):
                                print(txt['compact_skipped'].format(filename))
                                downloaded_albums.add(album_identifier)
                                skipped_count += 1
                                continue
                            
                            artwork_url = track.get("artworkUrl100")
                            if artwork_url:
                                artwork_url = artwork_url.replace("100x100bb", "1000x1000bb")
                            else:
                                print(txt['compact_not_found'].format(filename))
                                not_found_count += 1
                                continue
                            
                            img_data = requests.get(artwork_url).content
                            with open(out_path, "wb") as handler:
                                handler.write(img_data)
                            
                            downloaded_albums.add(album_identifier)
                            # Now prints: song_filename -> Artist - Album
                            print(txt['compact_saved'].format(filename, found_artist, found_album))
                            saved_count += 1
                        else:
                            print(txt['compact_not_found'].format(filename))
                            not_found_count += 1
                            
                    except Exception as e:
                        print(f"❌ Error scanning '{filename}': {e}")
                        not_found_count += 1
    except Exception as e:
        print(txt['error_msg'].format(e))
        return
                
    if not music_files_found:
        print(txt['no_music_found'])
    else:
        # Visual structured metrics dashboard
        print("\n" + "="*40)
        print(f"       {txt['scan_complete']}")
        print("="*40)
        print(txt['summary_saved'].format(saved_count))
        print(txt['summary_skipped'].format(skipped_count))
        print(txt['summary_not_found'].format(not_found_count))
        print("="*40)

def main():
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
            
        if song_name.lower() == 'folder':
            folder_path = navigate_directories(txt)
            if folder_path:
                process_folder(folder_path, txt)
            print(txt['loop_restart'])
            continue

        # --- MANUAL SINGLE SONG SEARCH ---
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
