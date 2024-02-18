import streamlit as st
import os
import logging
import json
from chromadb.utils import embedding_functions  # Replace with your actual module name
from config import dict_of_folder_path


def initialize_session_state():
    """Initialize session state variables for chat management."""
    if 'clear_chat_flag' not in st.session_state:
        st.session_state['clear_chat_flag'] = False
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'sources_info' not in st.session_state:
        st.session_state['sources_info'] = []


def load_folders():
    with open(dict_of_folder_path, 'r') as file:
        return json.load(file)
    
def initialize_chatbot_embedding():
    """Initialize embedding function for the chatbot."""
    # return embedding_functions.OpenAIEmbeddingFunction(
    #     api_key=os.environ['OPENAI_API_KEY'],
    #     model_name="text-embedding-ada-002"
    
def save_folders(folders):
    with open(dict_of_folder_path, 'w') as file:
        json.dump(folders, file)

def get_folder_names(Dict_of_folders):
    return [folder["name"] for folder in Dict_of_folders["entries"]]

def find_folder(Dict_of_folders, folder_name):
    for folder in Dict_of_folders["entries"]:
        if folder["name"] == folder_name:
            return folder
    return None
def setup_retriever(ctrl, embedding_function):
    """Set up the collection for the retriever in the chatbot."""
    ctrl.retriever.collection = ctrl.client_db.get_collection("Mistral_Collection")
def create_folder(folder_name, documents, Dict_of_folders):
    folder = find_folder(Dict_of_folders, folder_name)
    if not folder:
        Dict_of_folders["entries"].append({"name": folder_name, "files": documents})
    else:
        folder["files"] = documents
    save_folders(Dict_of_folders)

def update_folder(folder_name, new_documents, Dict_of_folders):
    folder = find_folder(Dict_of_folders, folder_name)
    if folder:
        folder["files"].extend(new_documents)
        folder["files"] = list(set(folder["files"]))  # Remove duplicates
        save_folders(Dict_of_folders)

def remove_folder(folder_name, Dict_of_folders):
    Dict_of_folders["entries"] = [folder for folder in Dict_of_folders["entries"] if folder["name"] != folder_name]
    save_folders(Dict_of_folders)
def display_chat():
    """Function to display chat messages."""
    for message in st.session_state['messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
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
        if existing_folder and not st.checkbox(f"A folder named '{new_folder_name}' already exists. Do you want to overwrite it?"):
            return

        create_folder(new_folder_name, selected_documents, Dict_of_folders)
        st.success(f"Folder '{new_folder_name}' created successfully.")
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

        def display_current_files(files):
            if files:
                file_list = '\n'.join(f"- {file}" for file in files)
                current_files_placeholder.markdown("### Current files in the folder:\n" + file_list)
            else:
                current_files_placeholder.write("No files in the folder.")

        display_current_files(selected_folder["files"])

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
            create_folder(selected_folder_name, updated_files, Dict_of_folders)
            st.success(f"Folder '{selected_folder_name}' updated.")
            st.experimental_rerun()

        if st.button("Remove Folder", key="remove_folder_button"):
            if st.checkbox(f"Are you sure you want to remove the folder '{selected_folder_name}'?"):
                remove_folder(selected_folder_name, Dict_of_folders)
                st.success(f"Folder '{selected_folder_name}' and its files removed.")
                st.experimental_rerun()

        display_current_files(selected_folder["files"])

def setup_sidebar(Dict_of_folders):
    """Function to set up the sidebar for document and chat control."""
    st.sidebar.title("Document Selection")
    query_type = st.sidebar.radio("Query Type", options=["Everything", "Folder", "Document(s)", "No Documents"])
    
    Folders_list = selected_documents = []
    if query_type == "Folder":
        Folders_list = st.sidebar.multiselect("Select Folder", options=get_folder_names(Dict_of_folders), key="Folders_list")
    elif query_type == "Document(s)":
        all_documents = set(doc for folder in Dict_of_folders["entries"] for doc in folder["files"])
        selected_documents = st.sidebar.multiselect("Select Document(s)", options=all_documents, key="Documents_in_folder")


    st.sidebar.title("Feedbacks")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if col1.button("👍 Positive"):
            handle_feedback("Positive")
    with col2:
        if col2.button("👎 Negative"):
            handle_feedback("Negative")
            


    st.sidebar.title("Manual Feedback")
    
    # Display the text input for feedback
    feedback_text = st.sidebar.text_input("Enter your feedback", key="manual_feedback")
    return query_type, Folders_list, selected_documents


def handle_feedback(feedback_type, feedback_content=""):
    """Function to handle feedback."""
    log_feedback(feedback_type, feedback_content)
    
def log_feedback(feedback_type, feedback_content):
    """Function to log feedback."""
    # Log different types of feedback
    if feedback_type == "Manual":
        logging.info(f"Feedback: {feedback_content} ", extra={'category': 'Manual Feedback', 'elapsed_time': 0})
    else:
        query, answer = "", ""
        sources_contents = [''] * 4
        if st.session_state['messages']:
            if len(st.session_state['messages']) > 1:
                query = st.session_state['messages'][-2]["content"]
                answer = st.session_state['messages'][-1]["content"]
                sources_contents = get_sources_contents() if 'sources_info' in st.session_state else sources_contents
        logging.info(f"Feedback: {feedback_type}, Collection: {"Eureka"}, Query: {query}, Answer: {answer}, Sources: {sources_contents}", extra={'category': 'Thumb Feedback', 'elapsed_time': 0})

def get_sources_contents():
    """Function to get contents of sources from session state."""
    return [source_content for _, _, _, source_content in st.session_state['sources_info']]
def submit_manual_feedback(feedback_text):
    """Function to submit manual feedback."""
    if feedback_text:
        handle_feedback("Manual", feedback_text)

def handle_user_query(ctrl, query_type, selected_documents, Folders_list):
    """Function to process and display user query and response."""
    user_query = st.chat_input("Ask your question here")
    if user_query:
        with st.spinner('Please wait...'):
            user_message = {"role": "user", "content": user_query}
            st.session_state['messages'].append(user_message)

            if query_type == "No Documents":
                response = ctrl.get_response(query=user_query, histo=st.session_state['messages'])
                st.session_state['sources_info'] = []
            else:
                documents = selected_documents if query_type in ["Folder", "Document(s)"] else []
                response, sources = ctrl.get_response(query=user_query, histo=st.session_state['messages'], folder=Folders_list, doc_or_folder=query_type, documents=documents)
                st.session_state['sources_info'] = [(source.index, source.title, source.distance_str, source.content) for source in sources[:3]]

            bot_message = {"role": "bot", "content": response}
            st.session_state['messages'].append(bot_message)
            display_chat()

def display_sources():
    """Function to display sources if available."""
    if st.session_state['sources_info']:
        with st.expander("View Sources"):
            for index, (source_index, title, score, content) in enumerate(st.session_state['sources_info']):
                st.markdown(f"**Source {source_index}: {title}** (score = {score})")
                st.text_area(f"source_content_{index}", value=content, height=100, disabled=True, key=f"source_content_{index}")



def streamlit_user(chat):   

    # Display the main title of the application
    st.markdown("""
    <h1 style='color: #009a44; text-align: center; font-size: 60px;'>
        Eureka
    </h1>""", unsafe_allow_html=True)


    # Initialization and setup
    initialize_session_state()
    Dict_of_folders = load_folders()
    print(Dict_of_folders)
    open_ai_embedding = initialize_chatbot_embedding()
    setup_retriever(chat, open_ai_embedding)

    # Set up sidebar for document selection, chat control, and manual feedback
    query_type, Folders_list, selected_documents = setup_sidebar(Dict_of_folders)

    # Display chat interface
    display_chat()

    # Handle user query and feedback
    handle_user_query(chat, query_type, selected_documents, Folders_list)

    # Display sources related to the query
    display_sources()