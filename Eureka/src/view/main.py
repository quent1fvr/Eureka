import streamlit as st
import os
import logging
import json
from src.view.usage_guide import streamlit_usage_guide
from src.view.log_view import StreamlitInterfaceLOG
from src.tools.folder_manager import FolderManager
dict_of_folders_path = os.getenv("DICT_OF_FOLDER_PATH")
from src.view.ui_manager import UIManager
from src.view.query_handler import UserQueryHandler,SourceDisplay, SessionState, ChatDisplay


class ChatbotEmbedding:
    def __init__(self):
        self.embedding_function = None

    def initialize(self):
        """Initialize the embedding function for the chatbot."""
        self.embedding_function = None


# Retrieval setup for the chatbot
class RetrieverSetup:
    @staticmethod
    def setup(ctrl, embedding_function):
        """Set up the collection for the retriever in the chatbot."""
        ctrl.retriever.collection = ctrl.client_db.get_collection("Mistral_Collection")

              
class StreamlitApp:
    def __init__(self, chat,Dict_of_folders):
        self.chat = chat
        self.Dict_of_folders = Dict_of_folders
        self.embedding = None
        self.interface_log = StreamlitInterfaceLOG(chat)  # Initialize Log Interface

    def run(self):
        SessionState.initialize()
        self.Dict_of_folders = FolderManager.load_folders(self.Dict_of_folders)
        self.embedding = ChatbotEmbedding()
        self.embedding.initialize()
        RetrieverSetup.setup(self.chat, self.embedding.embedding_function)

        view_type = self.setup_view_choice()

        if view_type == "User View":
            self.run_user_view()
        elif view_type == "Admin View":
            self.run_admin_view()
        elif view_type == "Log View":
            self.interface_log.log_view()
        elif view_type == "Usage Guide":
            streamlit_usage_guide()

    def setup_view_choice(self):
        st.sidebar.title("Navigation")
        return st.sidebar.radio("Choose a View", ["User View", "Admin View", "Log View", "Usage Guide"])

    def run_user_view(self):
        query_type, Folders_list, selected_documents = UIManager.setup_sidebar(self.Dict_of_folders)
        ChatDisplay.display_chat()
        UserQueryHandler.handle_user_query(self.chat, query_type, selected_documents, Folders_list)
        SourceDisplay.display_sources()

    def run_admin_view(self):
        st.markdown("<h1 style='color: #009a44; text-align: center; font-size: 60px;'>AskTheDocs - Admin View</h1>", unsafe_allow_html=True)
        UIManager.folder_creation_ui(self.Dict_of_folders, self.chat)
        UIManager.folder_management_ui(self.Dict_of_folders, self.chat)
        UIManager.document_deletion_ui(self.chat, self.Dict_of_folders)


# Main execution
if __name__ == "__main__":
    chat = None  # Initialize your Chatbot control here
    app = StreamlitApp(chat)
    app.run()
