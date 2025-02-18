import os
import json
import yt_dlp
import tkinter as tk
import re
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from threading import Thread

def save_config(destination_folder):
    with open('config.json', 'w') as config_file:
        json.dump({'destination_folder': destination_folder}, config_file)


def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            return config.get('destination_folder', '')
    return ''


def update_progress(percent, progress_var, progress_bar):
    progress_var.set(percent)
    progress_bar.update()


def download_audio(url, destination_folder, progress_var, progress_bar, status_label, download_results):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(destination_folder, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [lambda d: progress_hook(d, progress_var, progress_bar, status_label)],
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Unknown Title')
        download_results.append(f"{url.rsplit('=', 1)[1]}|{video_title[:35]:35}: Sucesso!")
    except Exception as e:
        download_results.append(f"{url.rsplit('=', 1)[1]}: Falhou! ({str(e)[:33]})")


def progress_hook(d, progress_var, progress_bar, status_label):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded_bytes = d.get('downloaded_bytes', 0)
        percent = int(downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
        speed = d.get('speed', 0) or 0
        size_in_mib = total_bytes / 1024 / 1024 if total_bytes > 0 else 0
        speed_in_kib = speed / 1024 if speed > 0 else 0
        update_progress(percent, progress_var, progress_bar)
        status_label.config(text=f"Baixando: {percent}% - Velocidade: {speed_in_kib:.2f} KiB/s - Tamanho: {size_in_mib:.2f} MiB")
    elif d['status'] == 'finished':
        update_progress(100, progress_var, progress_bar)
        status_label.config(text="Conversão para MP3 concluída")


def start_download():
    url_input = url_entry.get("1.0", tk.END).strip()
    if not url_input:
        messagebox.showwarning("Aviso", "Por favor, insira o link do vídeo ou o código.")
        return

    destination_folder = destination_folder_var.get()
    if not destination_folder:
        messagebox.showwarning("Aviso", "Por favor, escolha a pasta de destino.")
        return

    save_config(destination_folder)

    
    if list_var.get():
        urls = url_input.splitlines()
    else:
        urls = [url_input]

    download_results = []
    threads = []

    for url in urls:
        if not re.match(r'^https?://', url):
            url = f'https://www.youtube.com/watch?v={url}'
        
        download_thread = Thread(target=download_audio, args=(url, destination_folder, progress_var, progress_bar, status_label, download_results))
        download_thread.start()
        threads.append(download_thread)

    monitor_thread = Thread(target=monitor_downloads, args=(threads, download_results))
    monitor_thread.start()


def monitor_downloads(threads, download_results):
    for thread in threads:
        thread.join()
    
    results_text.config(state=tk.NORMAL)
    results_text.delete("1.0", tk.END)
    for result in download_results:
        results_text.insert(tk.END, result + '\n')
    results_text.config(state=tk.DISABLED)
    messagebox.showinfo("Download Completo", "Todos os downloads foram concluídos.")


def select_destination_folder():
    folder = filedialog.askdirectory()
    if folder:
        destination_folder_var.set(folder)


def toggle_list_mode():
    if list_var.get():
        url_entry.config(height=10)
    else:
        url_entry.config(height=1)


root = tk.Tk()
root.title("YouTube Audio Downloader")
root.geometry("680x600")

frame = tk.Frame(root)
frame.pack(expand=True)

tk.Label(frame, text="Link do Vídeo ou Código:").pack(pady=5)
url_entry = tk.Text(frame, width=80, height=1)
url_entry.pack(pady=5)

list_var = tk.BooleanVar()
list_checkbox = tk.Checkbutton(frame, text="Lista", variable=list_var, command=toggle_list_mode)
list_checkbox.pack(pady=5)

tk.Label(frame, text="Pasta de Destino:").pack(pady=5)
destination_folder_var = tk.StringVar()
destination_folder_var.set(load_config())

destination_frame = tk.Frame(frame)
destination_frame.pack(pady=5)
tk.Entry(destination_frame, textvariable=destination_folder_var, width=70).pack(side=tk.LEFT, padx=5)
tk.Button(destination_frame, text="Selecionar", command=select_destination_folder).pack(side=tk.LEFT, padx=5)

tk.Label(frame, text="Progresso:").pack(pady=5)
progress_var = tk.IntVar()
progress_bar = Progressbar(frame, orient=tk.HORIZONTAL, length=400, mode='determinate', maximum=100, variable=progress_var)
progress_bar.pack(pady=5)

status_label = tk.Label(frame, text="Aguardando...")
status_label.pack(pady=5)

tk.Button(frame, text="Baixar Áudio", command=start_download).pack(pady=20)

tk.Label(frame, text="Resultados do Download:").pack(pady=5)
results_text = tk.Text(frame, width=80, height=10, state=tk.DISABLED)
results_text.pack(pady=5)

root.mainloop()
