import webbrowser
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter import simpledialog

import ffmpy
import requests
from bs4 import BeautifulSoup
from pytube import YouTube
import os

special_marks = [".", "!", ",", "?", ";"]


# Step 1: Use the song search term to find the song on YouTube
def find_song_link(search_term):
    youtube_base_url = "https://www.youtube.com/results?search_query= {}"
    search_url = youtube_base_url.format(str(search_term))
    r = requests.get(search_url)
    # webbrowser.open(search_url)
    soup = BeautifulSoup(r.text, "html.parser")
    unique_search_href = ""
    for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}, limit=1):
        unique_search_href = vid["href"]
    song_url = f"https://www.youtube.com{unique_search_href}"
    webbrowser.open(song_url)
    return song_url


# Step 2: Download the song audio only to the given directory path
def download_song_audio(song_url, directory_path):
    yt_video = YouTube(song_url)
    mp4_filename = yt_video.title
    # Removes any special punctuation from the file name
    for punctuation in special_marks:
        mp4_filename = mp4_filename.replace(punctuation, "")
    audio_streams = yt_video.streams.get_audio_only()
    complete_mp4_path = audio_streams.download(output_path=directory_path, filename=mp4_filename)
    return complete_mp4_path


# Step 3: Convert the mp4 file to an mp3 file and removes the mp4_file
def convert_song(complete_mp4_path):
    complete_mp3_path = str(complete_mp4_path).replace(".mp4", ".mp3")
    ff = ffmpy.FFmpeg(inputs={complete_mp4_path: None}, outputs={complete_mp3_path: None})
    ff.run()
    os.remove(complete_mp4_path)
    return complete_mp3_path


# Step 4: Put it all together
def run_program():
    again = True
    correct_song = False

    # Create tkinter window
    window = Tk()
    window.eval("tk::PlaceWindow %s center" % window.winfo_toplevel())
    window.wm_attributes("-topmost", 1)
    window.withdraw()

    # Prompts the user for the folder that they want the mp3 downloaded to
    directory_path = filedialog.askdirectory(
        title="Choose the directory/folder where you want the songs to download to.")

    # If the directory path is empty, end the program
    if not directory_path:
        sys.exit(0)

    # Run until the correct song is chosen and again is False
    while not correct_song and again:
        song = simpledialog.askstring("Song Name", "What is the name of the song you would like to convert (include "
                                                   "artist)?")

        # If the song is None, meaning the user hit the X button, exit the program
        if song is None:
            sys.exit(0)

        if song:
            song_link = find_song_link(song)
            correct_song = messagebox.askyesno("Correct Song", "Was the correct song pulled up in your browser?")
            if correct_song:
                complete_mp4_path = download_song_audio(song_link, directory_path)
                complete_mp3_path = convert_song(complete_mp4_path)
                messagebox.showinfo("File Name", f"Song directory path is: {complete_mp3_path}")
                again = messagebox.askyesno("Convert Again?", "Would you like to convert another song?")
                correct_song = False

    window.deiconify()
    window.destroy()
    window.quit()
    sys.exit()


run_program()
