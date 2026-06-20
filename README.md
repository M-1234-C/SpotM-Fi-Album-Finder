# SpotM-Fi-Album-Finder
A external app for SpotM-Fi that lets you find the album cover for the song you want and download it

# But what actually is it ?

A lightweight, localized Python command-line interface that lets you quickly search for and download high-resolution ($1000 \times 1000\text{ px}$) album artwork using the iTunes Search API.

## Features

* **High-Res Artworks:** Automatically fetches the highest available resolution ($1000 \times 1000\text{ px}$) instead of standard thumbnails.
* **Multi-language Support:** Fully localized in multiple languages (More will be added later)
* **Smart Filename Sanitization:** Automatically strips out invalid OS characters (`\ / * ? : " < > |`) to ensure clean saving.
* **Flexible Search:** Search by song title alone, or add the artist's name for more accurate matching.

## Prerequisites

Before running the script make sure you have Python 3.6+ and the `requests` library (for handling API queriries)
