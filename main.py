# -*- coding: utf-8 -*-
import os
import shutil
import datetime
import json
import time

# === НАСТРОЙКИ ===
SOURCE_FOLDER = "Z:/shared/source"  # Путь к исходной папке (может быть сетевой)
DESTINATION_FOLDER = "Z:/shared/backups"  # Путь к папке для архивации (может быть сетевой)
STATE_FILE = os.path.join(DESTINATION_FOLDER, "backup_state.json")  # Файл состояния
MIN_FREE_SPACE_GB = 5  # Минимум свободного места на диске для создания бэкапа
CHECK_INTERVAL_SECONDS = 3600  # Периодичность проверки (раз в час)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def ensure_dirs():
    os.makedirs(DESTINATION_FOLDER, exist_ok=True)

def current_month_key():
    return datetime.datetime.now().strftime("%Y-%m")

def current_backup_folder():
    return f"backup_{datetime.datetime.now().strftime('%Y-%m-%d')}"

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
    folder_name = current_backup_folder()
    dest_path = os.path.join(DESTINATION_FOLDER, folder_name)
    if os.path.exists(dest_path):
        return  # Архив уже существует

    os.makedirs(dest_path, exist_ok=True)

    for dirpath, _, filenames in os.walk(SOURCE_FOLDER):
        for f in filenames:
            src = os.path.join(dirpath, f)
            rel_dir = os.path.relpath(dirpath, SOURCE_FOLDER)
            dst_dir = os.path.join(dest_path, rel_dir)
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src, os.path.join(dst_dir, f))

def main():
    ensure_dirs()
    while True:
        state = load_state()
        key = current_month_key()
        backup_name = current_backup_folder()
        dest_path = os.path.join(DESTINATION_FOLDER, backup_name)

        if state.get("last_backup") != key and not os.path.exists(dest_path):
            backup_size = get_folder_size_bytes(SOURCE_FOLDER)
            free_space = get_free_space_bytes(DESTINATION_FOLDER)

            if free_space < backup_size + MIN_FREE_SPACE_GB * 1024 ** 3:
                clean_old_backups(backup_size + MIN_FREE_SPACE_GB * 1024 ** 3)

            create_backup()
            state["last_backup"] = key
            save_state(state)

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
