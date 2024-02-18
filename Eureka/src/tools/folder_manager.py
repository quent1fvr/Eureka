import json
import os
dict_of_folders_path = os.getenv("DICT_OF_FOLDER_PATH")

class FolderManager:
    @staticmethod
    def load_folders(Dict_of_folders):
        """Load folders from a JSON file."""
        with open(Dict_of_folders, 'r') as file:
            return json.load(file)

    @staticmethod
    def save_folders(folders):
        """Save folders to a JSON file."""
        with open(dict_of_folders_path, 'w') as file:
            json.dump(folders, file)

    @staticmethod
    def get_folder_names(Dict_of_folders):
        """Get names of all folders."""
        return [folder["name"] for folder in Dict_of_folders["entries"]]

    @staticmethod
    def find_folder(Dict_of_folders, folder_name):
        """Find a folder by its name."""
        for folder in Dict_of_folders["entries"]:
            if folder["name"] == folder_name:
                return folder
        return None

    @staticmethod
    def create_folder(folder_name, documents, Dict_of_folders):
        """Create a new folder or update an existing one."""
        folder = FolderManager.find_folder(Dict_of_folders, folder_name)
        if not folder:
            Dict_of_folders["entries"].append({"name": folder_name, "files": documents})
        else:
            folder["files"] = documents
        FolderManager.save_folders(Dict_of_folders)

    @staticmethod
    def update_folder(folder_name, new_documents, Dict_of_folders):
        """Update an existing folder."""
        folder = FolderManager.find_folder(Dict_of_folders, folder_name)
        if folder:
            folder["files"].extend(new_documents)
            folder["files"] = list(set(folder["files"]))  # Remove duplicates
            FolderManager.save_folders(Dict_of_folders)

    @staticmethod
    def remove_folder(folder_name, Dict_of_folders):
        """Remove a folder."""
        Dict_of_folders["entries"] = [folder for folder in Dict_of_folders["entries"] if folder["name"] != folder_name]
        FolderManager.save_folders(Dict_of_folders)