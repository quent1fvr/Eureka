import streamlit as st
import os
import time
import logging
import json
from chromadb.utils import embedding_functions
import tempfile
import streamlit as st
import json
import time
import logging
from chromadb.utils import embedding_functions  # Replace with your actual module name
from config import dict_of_folder_path



st.set_page_config(
    page_title="BNP Paribas Themed App",
    layout="wide",
    initial_sidebar_state="expanded"
)
def get_folder_names(Dict_of_folders):
    return [folder["name"] for folder in Dict_of_folders["entries"]]

def find_folder(Dict_of_folders, folder_name):
    for folder in Dict_of_folders["entries"]:
        if folder["name"] == folder_name:
            return folder
    return None
def remove_folder(folder_name, Dict_of_folders):
    Dict_of_folders["entries"] = [folder for folder in Dict_of_folders["entries"] if folder["name"] != folder_name]
    save_folders(Dict_of_folders)

def load_folders():
    with open(dict_of_folder_path, 'r') as file:
        return json.load(file)

def save_folders(Dict_of_folders):
    with open(dict_of_folder_path, 'w') as file:
        json.dump(Dict_of_folders, file)

def folder_creation_ui(Dict_of_folders, ctrl):
    st.subheader("Create New Folder")
    new_folder_name = st.text_input("Folder Name", key="new_folder_name")

    try:
        all_documents = [item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]
    except Exception as e:
        st.error("Failed to retrieve documents: " + str(e))
        return

    selected_documents = st.multiselect("Select documents to add", set(all_documents), key="selected_documents_for_new_folder")

    if st.button("Create Folder", key="create_folder_button"):
        if not new_folder_name:
            st.warning("Please enter a name for the folder.")
            return

        existing_folder = find_folder(Dict_of_folders, new_folder_name)
        if existing_folder:
            if not st.checkbox(f"A folder named '{new_folder_name}' already exists. Do you want to overwrite it?"):
                return

        create_folder(new_folder_name, selected_documents, Dict_of_folders)
        st.success(f"Folder '{new_folder_name}' created successfully.")

def create_folder(folder_name, documents, Dict_of_folders):
    folder = find_folder(Dict_of_folders, folder_name)
    if not folder:
        Dict_of_folders["entries"].append({"name": folder_name, "files": documents})
    else:
        folder["files"] = documents
    save_folders(Dict_of_folders)




def folder_management_ui(Dict_of_folders, ctrl):
    st.subheader("Manage Existing Folders")
    folder_names = get_folder_names(Dict_of_folders)
    
    if not folder_names:
        st.write("No folders to display.")
        return

    selected_folder_name = st.selectbox("Select a folder to manage", folder_names, key="selected_folder_to_manage")
    selected_folder = find_folder(Dict_of_folders, selected_folder_name)

    if selected_folder:
        current_files_placeholder = st.empty()
        display_current_files(current_files_placeholder, selected_folder["files"])

        try:
            all_documents = [item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]
        except Exception as e:
            st.error("Failed to retrieve documents: " + str(e))
            return

        additional_documents = st.multiselect("Add more documents to the folder", set([doc for doc in all_documents if doc not in selected_folder["files"]]), key="additional_documents")
        files_to_remove = st.multiselect("Select files to remove from the folder", selected_folder["files"], key="files_to_remove")

        if st.button("Update Folder", key="update_folder_button"):
            update_folder(selected_folder_name, additional_documents, files_to_remove, Dict_of_folders)
            st.success(f"Folder '{selected_folder_name}' updated.")
            st.experimental_rerun()

        if st.button("Remove Folder", key="remove_folder_button"):
            remove_folder(selected_folder_name, Dict_of_folders)
            st.success(f"Folder '{selected_folder_name}' and its files removed.")
            st.experimental_rerun()

def display_current_files(placeholder, files):
    if files:
        file_list = '\n'.join(f"- {file}" for file in files)
        placeholder.markdown("### Current files in the folder:\n" + file_list)
    else:
        placeholder.write("No files in the folder.")

def update_folder(folder_name, additional_documents, files_to_remove, Dict_of_folders):
    folder = find_folder(Dict_of_folders, folder_name)
    if folder:
        folder["files"] = [doc for doc in folder["files"] if doc not in files_to_remove]
        folder["files"].extend(additional_documents)
        save_folders(Dict_of_folders)




def admin_view(ctrl, Dict_of_folders):
    ctrl.retriever.collection = ctrl.client_db.get_collection("Mistral_Collection")

    st.markdown("""
        <h1 style='color: #009a44; text-align: center; font-size: 60px;'>
            Eureka - Admin View
        </h1>""", unsafe_allow_html=True)
    

    # Import other necessary libraries and modules

    # Enable logging for debugging
    logging.basicConfig(level=logging.DEBUG)

    def get_all_documents():
        try:
            # Retrieve all documents and their metadata
            all_documents = ctrl.retriever.collection.get()['metadatas']
            logging.debug(f"All documents retrieved: {all_documents}")
            # Return a list of document names
            return [doc['doc'] for doc in all_documents]
        except Exception as e:
            logging.error("Failed to retrieve document IDs: " + str(e))
            return []

    def get_document_ids_by_name(file_name, ctrl):
        try:
            # Retrieve all documents and their metadata
            all_documents = ctrl.retriever.collection.get()['metadatas']
            logging.debug(f"Documents for ID retrieval: {all_documents}")
            # Filter documents by the specified file name
            matching_ids = [doc['id'] for doc in all_documents if doc['doc'] == file_name]
            logging.debug(f"Matching IDs found for '{file_name}': {matching_ids}")
            return matching_ids
        except Exception as e:
            logging.error("Failed to retrieve document IDs: " + str(e))
            return []


    def delete_file(file_name, ctrl, Dict_of_folders):
        try:
            # Delete the document from the Chroma collection
            #doc_ids_to_delete = get_document_ids_by_name(file_name, ctrl)
            print(file_name)
            ctrl.retriever.collection.delete(where={"doc" :file_name})
            
            logging.info(f"Document '{file_name}' deleted from Chroma collection.")

            # Now, remove the document from each folder in Dict_of_folders
            for folder in Dict_of_folders["entries"]:
                if file_name in folder["files"]:
                    folder["files"].remove(file_name)
                    logging.info(f"Removed '{file_name}' from folder '{folder['name']}'.")

            # Save the updated folders structure
            save_folders(Dict_of_folders)

            st.success(f"File '{file_name}' deleted successfully.")

        except Exception as e:
            st.error(f"Error in deleting file '{file_name}': {e}")


    
    with st.expander("Document Management", expanded=True):
        actual_page_start = st.number_input("Start page (default = 1)", value=1, min_value=1, key="actual_page_start")
        include_images = st.checkbox("Analyze text from images (ONLY for .pdf)", value=False, key="include_images")
        uploaded_file = st.file_uploader("Upload a file", key="input_doc_comp")

        if st.button("Process File", key="process_file_button"):
            if uploaded_file is not None:
                original_file_name = uploaded_file.name
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                start_time = time.time()
                # Pass both the temporary file path and the original file name
                result = ctrl.upload_doc(tmp_file_path, include_images, actual_page_start, original_file_name)
                end_time = time.time()

                if result:
                    st.success('File processed successfully.')
                    folder_names = get_folder_names(Dict_of_folders)
                    if 'Default' in folder_names:
                        default_folder_index = folder_names.index('Default')
                        Dict_of_folders["entries"][default_folder_index]["files"].append(original_file_name)
                        save_folders(Dict_of_folders)
                    else:
                        st.error("Default folder not found.")

                    logging.info(f"Execution time for upload_doc: {end_time - start_time} seconds")
                else:
                    st.error("File extension not supported. Only .docx, .pdf, and .html are supported.")

        if st.button("Clear File", key="clear_file_button"):
            st.session_state['input_doc_comp'] = None


    with st.expander("Folder Management", expanded=True):
        folder_creation_ui(Dict_of_folders, ctrl)
        folder_management_ui(Dict_of_folders, ctrl)            

    with st.expander("Document Deletion", expanded=False):
        all_documents = get_all_documents()
        selected_file_to_delete = st.selectbox("Select a file to delete", options=all_documents, key="select_file_to_delete")

        if st.button("Delete File", key="delete_file_button"):
            if selected_file_to_delete:
                # Store the file name in session state to delete
                st.session_state['file_to_delete'] = selected_file_to_delete

        # Check if the deletion process has started and the file to delete is confirmed
        if 'file_to_delete' in st.session_state and st.session_state['file_to_delete']:
            # Show a confirmation button
            if st.button("Confirm Delete", key="confirm_delete_button"):
                delete_file(st.session_state['file_to_delete'], ctrl, Dict_of_folders)
                st.success(f"File '{st.session_state['file_to_delete']}' deleted successfully.")
                del st.session_state['file_to_delete']
                del st.session_state['select_file_to_delete']  # Clear the selection
                st.experimental_rerun()
                


def streamlit_admin(ctrl):
    Dict_of_folders = load_folders()
    admin_view(ctrl, Dict_of_folders)

# Main execution
if __name__ == "__main__":
    ctrl = None  # Initialize your Chatbot control here
    streamlit_admin(ctrl)
