# utils/data_manager.py
import json
import os
import shutil
import tempfile
from typing import Callable, Any
from .file_lock import FileLock
from .ui_messages import show_recovery_success, show_recovery_error


def _get_lock_path(file_path: str) -> str:
    return f"{file_path}.lock"


def _save_json_atomically(file_path: str, data: dict | list):
    dir_name = os.path.dirname(file_path)
    if not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name, exist_ok=True)
        except OSError as e:
            print(f"Erreur critique lors de la création du dossier pour la sauvegarde '{dir_name}': {e}")
            raise

    temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=os.path.basename(file_path) + '~', suffix='.tmp')

    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as tf:
            json.dump(data, tf, indent=4, ensure_ascii=False)

        backup_path = file_path + ".bak"
        if os.path.exists(file_path):
            try:
                os.replace(file_path, backup_path)
            except OSError as e:
                print(f"AVERTISSEMENT: Impossible de créer le backup pour {file_path}: {e}")

        os.replace(temp_path, file_path)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde atomique de {file_path}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def read_modify_write_json(file_path: str, modification_func: Callable[[Any], Any]) -> Any:
    lock_path = _get_lock_path(file_path)

    with FileLock(lock_path):
        data = load_json_data(file_path)
        result = modification_func(data)
        _save_json_atomically(file_path, data)
        return result


def load_json_data(file_path: str) -> Any:
    is_list_type = 'remboursements_index' in os.path.basename(file_path)
    default_value = [] if is_list_type else {}

    if not os.path.exists(file_path):
        return default_value

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return default_value
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"ALERTE: Fichier JSON corrompu détecté : {file_path}")
        backup_path = file_path + ".bak"
        backup_exists = os.path.exists(backup_path)

        if backup_exists:
            try:
                print(f"Tentative de restauration depuis {backup_path}...")
                shutil.copy2(backup_path, file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    restored_data = json.load(f)
                print("Restauration réussie.")
                show_recovery_success(file_path)
                return restored_data
            except (IOError, json.JSONDecodeError):
                print(f"ERREUR: Le fichier de backup {backup_path} est aussi corrompu.")
                show_recovery_error(file_path, backup_exists=True)
                return default_value
        else:
            print("ERREUR: Aucun fichier de backup trouvé.")
            show_recovery_error(file_path, backup_exists=False)
            return default_value
    except (IOError, FileNotFoundError):
        return default_value