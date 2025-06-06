import json
import os
import tempfile
from typing import Callable, Any
from .file_lock import FileLock


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

        os.replace(temp_path, file_path)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde atomique de {file_path}: {e}")
        os.remove(temp_path)
        raise


def read_modify_write_json(file_path: str, modification_func: Callable[[Any], Any]) -> Any:
    lock_path = _get_lock_path(file_path)

    with FileLock(lock_path):
        data = {}
        file_basename = os.path.basename(file_path)

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content)
                    else:
                        data = [] if 'remboursements' in file_basename else {}
            except (json.JSONDecodeError, FileNotFoundError):
                data = [] if 'remboursements' in file_basename else {}
        else:
            data = [] if 'remboursements' in file_basename else {}

        result = modification_func(data)

        _save_json_atomically(file_path, data)

        return result


def load_json_data(file_path: str) -> Any:
    lock_path = _get_lock_path(file_path)

    with FileLock(lock_path):
        file_basename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            return [] if 'remboursements' in file_basename else {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return [] if 'remboursements' in file_basename else {}
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return [] if 'remboursements' in file_basename else {}