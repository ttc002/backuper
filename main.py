# -*- coding: utf-8 -*-
import os
import shutil
import datetime
import json
import zipfile
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import ctypes

# === НАСТРОЙКИ ===
SOURCE_FOLDER = "Z:/shared/source"  # Путь к исходной папке (может быть сетевой)
DESTINATION_FOLDER = "Z:/shared/backups"  # Путь к папке для архивации (может быть сетевой)
STATE_FILE = os.path.join(DESTINATION_FOLDER, "backup_state.json")  # Файл состояния
MIN_FREE_SPACE_GB = 5  # Минимум свободного места на диске для создания бэкапа

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def ensure_dirs():
    os.makedirs(DESTINATION_FOLDER, exist_ok=True)

def current_month_key():
    return datetime.datetime.now().strftime("%Y-%m")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f)

def get_folder_size_bytes(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_free_space_bytes(folder):
    total, used, free = shutil.disk_usage(folder)
    return free

def clean_old_backups(required_space):
    files = [os.path.join(DESTINATION_FOLDER, f) for f in os.listdir(DESTINATION_FOLDER)]
    files = sorted(files, key=os.path.getctime)
    while files and get_free_space_bytes(DESTINATION_FOLDER) < required_space:
        oldest = files.pop(0)
        size = get_folder_size_bytes(oldest)
        if os.path.isdir(oldest):
            shutil.rmtree(oldest)
        else:
            os.remove(oldest)

def create_backup():
    now = datetime.datetime.now()
    folder_name = f"backup_{now.strftime('%Y-%m-%d')}"
    dest_path = os.path.join(DESTINATION_FOLDER, folder_name)
    shutil.copytree(SOURCE_FOLDER, dest_path)

def main():
    ensure_dirs()
    state = load_state()
    key = current_month_key()

    if state.get("last_backup") != key:
        backup_size = get_folder_size_bytes(SOURCE_FOLDER)
        free_space = get_free_space_bytes(DESTINATION_FOLDER)

        if free_space < backup_size + MIN_FREE_SPACE_GB * 1024 ** 3:
            clean_old_backups(backup_size + MIN_FREE_SPACE_GB * 1024 ** 3)

        create_backup()
        state["last_backup"] = key
        save_state(state)

# === GUI ===
def gui():
    state = load_state()
    last_backup = state.get("last_backup", "Никогда")
    free_space_gb = get_free_space_bytes(DESTINATION_FOLDER) / (1024 ** 3)
    folder_size_gb = get_folder_size_bytes(SOURCE_FOLDER) / (1024 ** 3)

    root = tk.Tk()
    root.title("Архиватор Папок")
    root.geometry("400x250")

    ttk.Label(root, text=f"Папка источника:").pack(pady=5)
    ttk.Label(root, text=SOURCE_FOLDER).pack()

    ttk.Label(root, text=f"Папка назначения:").pack(pady=5)
    ttk.Label(root, text=DESTINATION_FOLDER).pack()

    ttk.Label(root, text=f"Последняя архивация: {last_backup}").pack(pady=10)
    ttk.Label(root, text=f"Свободно на диске: {free_space_gb:.2f} GB").pack()
    ttk.Label(root, text=f"Размер исходной папки: {folder_size_gb:.2f} GB").pack()

    def run_backup():
        main()
        messagebox.showinfo("Успех", "Резервное копирование завершено!")
        root.destroy()
        gui()

    ttk.Button(root, text="Создать архив сейчас", command=run_backup).pack(pady=20)
    root.mainloop()

if __name__ == "__main__":
    gui()
