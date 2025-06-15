import os
import shutil


def delete_pycache(root_dir):
    """Remove all __pycache__ directories."""
    for dirpath, dirnames, _ in os.walk(root_dir):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"Deleted: {pycache_path}")
def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    delete_pycache(root_dir)
    print("All __pycache__ directories deleted successfully.")
if __name__ == "__main__":
    main()
