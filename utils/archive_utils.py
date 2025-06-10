# utils/archive_utils.py
import os
import zipfile
import tempfile
import shutil

_temp_dirs_to_clean = set()

def extract_file_to_temp(zip_archive_path: str, file_inside_zip: str) -> tuple[str | None, str | None]:
    if not os.path.exists(zip_archive_path):
        return None, None

    try:
        temp_dir = tempfile.mkdtemp(prefix="rb_archive_")
        _temp_dirs_to_clean.add(temp_dir)

        with zipfile.ZipFile(zip_archive_path, 'r') as zipf:
            extracted_path = zipf.extract(file_inside_zip, path=temp_dir)
            return extracted_path, temp_dir
    except (KeyError, FileNotFoundError, zipfile.BadZipFile) as e:
        print(f"Erreur extraction de '{file_inside_zip}' depuis '{zip_archive_path}': {e}")
        return None, None
    except Exception as e:
        print(f"Erreur inattendue lors de l'extraction de l'archive : {e}")
        return None, None

def cleanup_temp_dir(temp_dir_path: str | None):
    if temp_dir_path and temp_dir_path in _temp_dirs_to_clean:
        try:
            shutil.rmtree(temp_dir_path)
            _temp_dirs_to_clean.remove(temp_dir_path)
        except OSError as e:
            print(f"Erreur lors de la suppression du dossier temporaire {temp_dir_path}: {e}")

def cleanup_all_temp_dirs():
    for temp_dir in list(_temp_dirs_to_clean):
        cleanup_temp_dir(temp_dir)