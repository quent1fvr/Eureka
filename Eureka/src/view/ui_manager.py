import streamlit as st
from src.tools.folder_manager import FolderManager
from src.view.feedback_handler import FeedbackHandler
import logging
import time, tempfile
class UIManager:
    @staticmethod
    def folder_creation_ui(Dict_of_folders, ctrl):
        
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
                        folder_names = FolderManager.get_folder_names(Dict_of_folders)
                        if 'Default' in folder_names:
                            default_folder_index = folder_names.index('Default')
                            Dict_of_folders["entries"][default_folder_index]["files"].append(original_file_name)
                            FolderManager.save_folders(Dict_of_folders)
                        else:
                            st.error("Default folder not found.")

                        logging.info(f"Execution time for upload_doc: {end_time - start_time} seconds")
                    else:
                        st.error("File extension not supported. Only .docx, .pdf, and .html are supported.")

            if st.button("Clear File", key="clear_file_button"):
                st.session_state['input_doc_comp'] = None
        with st.expander("Folder creation", expanded=False):

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
                existing_folder = FolderManager.find_folder(Dict_of_folders, new_folder_name)
                if existing_folder and not st.checkbox(f"A folder named '{new_folder_name}' already exists. Do you want to overwrite it?"):
                    return
                FolderManager.create_folder(new_folder_name, selected_documents, Dict_of_folders)
                st.success(f"Folder '{new_folder_name}' created successfully.")
            
    @staticmethod
    def folder_management_ui(Dict_of_folders, ctrl):
        with st.expander("Folder managment", expanded=False):
            st.subheader("Manage Existing Folders")
            folder_names = FolderManager.get_folder_names(Dict_of_folders)
            if not folder_names:
                st.write("No folders to display.")
                return
            selected_folder_name = st.selectbox("Select a folder to manage", folder_names, key="selected_folder_to_manage")
            selected_folder = FolderManager.find_folder(Dict_of_folders, selected_folder_name)
            if selected_folder:
                current_files_placeholder = st.empty()
                UIManager.display_current_files(selected_folder["files"])
                try:
                    all_documents = [item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]
                except Exception as e:
                    st.error("Failed to retrieve documents: " + str(e))
                    return
                additional_documents = st.multiselect("Add more documents to the folder", 
                                                    set([doc for doc in all_documents if doc not in selected_folder["files"]]), 
                                                    key="additional_documents")
                files_to_remove = st.multiselect("Select files to remove from the folder", 
                                                selected_folder["files"], 
                                                key="files_to_remove")
                if st.button("Update Folder", key="update_folder_button"):
                    updated_files = [doc for doc in selected_folder["files"] if doc not in files_to_remove] + additional_documents
                    FolderManager.create_folder(selected_folder_name, updated_files, Dict_of_folders)
                    st.success(f"Folder '{selected_folder_name}' updated.")
                    st.experimental_rerun()
                if st.button("Remove Folder", key="remove_folder_button"):
                    if st.checkbox(f"Are you sure you want to remove the folder '{selected_folder_name}'?"):
                        FolderManager.remove_folder(selected_folder_name, Dict_of_folders)
                        st.success(f"Folder '{selected_folder_name}' and its files removed.")
                        st.experimental_rerun()
                UIManager.display_current_files(selected_folder["files"])


    @staticmethod
    def display_current_files(files):
        if files:
            file_list = '\n'.join(f"- {file}" for file in files)
            st.markdown("### Current files in the folder:\n" + file_list)
        else:
            st.write("No files in the folder.")

    @staticmethod
    def setup_sidebar(Dict_of_folders):
        st.sidebar.title("Document Selection")
        query_type = st.sidebar.radio("Query Type", options=["Everything", "Folder", "Document(s)", "No Documents"])
        Folders_list = selected_documents = []
        if query_type == "Folder":
            Folders_list = st.sidebar.multiselect("Select Folder", options=FolderManager.get_folder_names(Dict_of_folders), key="Folders_list")
        elif query_type == "Document(s)":
            all_documents = set(doc for folder in Dict_of_folders["entries"] for doc in folder["files"])
            selected_documents = st.sidebar.multiselect("Select Document(s)", options=all_documents, key="Documents_in_folder")
        st.sidebar.title("Feedbacks")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if col1.button("👍 Positive"):
                FeedbackHandler.handle_feedback("Positive")
        with col2:
            if col2.button("👎 Negative"):
                FeedbackHandler.handle_feedback("Negative")
        st.sidebar.title("Manual Feedback")
        feedback_text = st.sidebar.text_input("Enter your feedback", key="manual_feedback")
        
        def on_feedback_submit():
            """Handle feedback submission and clearing."""
            if feedback_text:
                FeedbackHandler.submit_manual_feedback(feedback_text)
                st.session_state['manual_feedback'] = ''
        if st.sidebar.button("Submit Manual Feedback", on_click=on_feedback_submit):
            pass
        
        return query_type, Folders_list, selected_documents



    @staticmethod
    def document_deletion_ui(ctrl, Dict_of_folders):
        with st.expander("Document Deletion", expanded=False):
            all_documents = UIManager.get_all_documents(ctrl)
            selected_file_to_delete = st.selectbox("Select a file to delete", options=set(all_documents), key="select_file_to_delete")

            if st.button("Delete File", key="delete_file_button"):
                if selected_file_to_delete:
                    UIManager.delete_file(selected_file_to_delete, ctrl, Dict_of_folders)

    @staticmethod
    def get_all_documents(ctrl):
        try:
            all_documents = ctrl.retriever.collection.get()['metadatas']
            return [doc['doc'] for doc in all_documents]
        except Exception as e:
            logging.error("Failed to retrieve document IDs: " + str(e))
            return []

    @staticmethod
    def delete_file(file_name, ctrl, Dict_of_folders):
        try:
            ctrl.retriever.collection.delete(where={"doc": file_name})
            for folder in Dict_of_folders["entries"]:
                if file_name in folder["files"]:
                    folder["files"].remove(file_name)
            FolderManager.save_folders(Dict_of_folders)
            st.success(f"File '{file_name}' deleted successfully.")
        except Exception as e:
            st.error(f"Error in deleting file '{file_name}': {e}")