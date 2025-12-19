import os
import shutil

def clean_project_artifacts(root_dir=None):
    """
    Recursively deletes __pycache__ and .idea directories starting from root_dir.
    If root_dir is None, uses the project root relative to this file.
    """
    if root_dir is None:
        # Assuming struct: project/src/utils/cleanup.py
        # Go up two levels to get project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))

    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to prevent walking into removed dirs
        # Copy list to iterate safely while modifying
        for d in list(dirnames):
            if d == "__pycache__" or d == ".idea":
                full_path = os.path.join(dirpath, d)
                try:
                    shutil.rmtree(full_path)
                except Exception:
                    pass
                dirnames.remove(d)

