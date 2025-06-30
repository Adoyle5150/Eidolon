import os

def get_unique_filename(base_path):
    if not os.path.exists(base_path):
        return base_path
    
    name, ext = os.path.splitext(base_path)
    counter = 1
    
    while True:
        new_path = f"{name}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1
