import streamlit as st
import json
import os
import logging
from src.control.control import Chatbot
from chromadb.utils import embedding_functions
from config import dict_of_folder_path

# Function definitions
def initialize_session_state():
    """Initialize session state variables for chat management."""
    if 'clear_chat_flag' not in st.session_state:
        st.session_state['clear_chat_flag'] = False
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'sources_info' not in st.session_state:
        st.session_state['sources_info'] = []

def load_folder_paths():
    """Load folder paths from a configuration file."""
    with open(dict_of_folder_path, 'r') as file:
        return json.load(file)

def initialize_chatbot_embedding():
    """Initialize embedding function for the chatbot."""
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ['OPENAI_API_KEY'],
        model_name="text-embedding-ada-002"
    )

def setup_retriever(ctrl, embedding_function):
    """Set up the collection for the retriever in the chatbot."""
    ctrl.retriever.collection = ctrl.client_db.get_collection("Mistral_Collection")

def display_chat():
    """Function to display chat messages."""
    for message in st.session_state['messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def reset_conversation():
    """Function to reset the conversation."""
    st.session_state['messages'] = []
    st.session_state['sources_info'] = []

def handle_feedback(feedback_type, feedback_content=""):
    """Function to handle feedback."""
    log_feedback(feedback_type, feedback_content)

def get_sources_contents():
    """Function to get contents of sources from session state."""
    return [source_content for _, _, _, source_content in st.session_state['sources_info']]

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

def setup_sidebar(Dict_of_folders):
    """Function to set up the sidebar for document and chat control."""
    st.sidebar.title("Document Selection")
    query_type = st.sidebar.radio("Query Type", options=["Everything", "Folder", "Document(s)", "No Documents"])
    Folders_list = selected_documents = []
    if query_type == "Folder":
        Folders_list = st.sidebar.multiselect("Select Folder", options=Dict_of_folders["Name"], key="Folders_list")
        if Folders_list:
            folder_indices = [Dict_of_folders["Name"].index(folder) for folder in Folders_list]
            for idx, folder in zip(folder_indices, Folders_list):
                st.sidebar.selectbox(f"Documents in {folder} folder", options=Dict_of_folders["Files"][idx], key=f"docs_{folder}")
    elif query_type == "Document(s)":
        all_documents = set(doc for doc_list in Dict_of_folders["Files"] for doc in doc_list)
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

    def on_feedback_submit():
        """Handle feedback submission and clearing."""
        if feedback_text:
            submit_manual_feedback(feedback_text)
            # Clear the text input after submission
            st.session_state['manual_feedback'] = ''

    if st.sidebar.button("Submit Manual Feedback", on_click=on_feedback_submit):
        # Button click is handled by the on_feedback_submit callback
        pass

    return query_type, Folders_list, selected_documents    


def submit_manual_feedback(feedback_text):
    """Function to submit manual feedback."""
    if feedback_text:
        handle_feedback("Manual", feedback_text)

def handle_user_query(ctrl, query_type, selected_documents, Folders_list):
    """Function to process and display user query and response."""
    user_query = st.chat_input("Posez votre question ici")
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
    Dict_of_folders = load_folder_paths()
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