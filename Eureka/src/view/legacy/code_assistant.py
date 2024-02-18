import streamlit as st
from src.control.control import Chatbot
import json
from chromadb.utils import embedding_functions
import os
from config import dict_of_folder_path

def streamlit_user(ctrl: Chatbot):
    with open(dict_of_folder_path, 'r') as file:
        Dict_of_folders = json.load(file)

    # open_ai_embedding = embedding_functions.OpenAIEmbeddingFunction(
    #     api_key=os.environ['OPENAI_API_KEY'],
    #     model_name="text-embedding-ada-002"
    # )
    # ctrl.retriever.collection = ctrl.client_db.get_collection("Mistral_Collection", embedding_function=open_ai_embedding)


    # Collection and Query Type Selection
    collections = [a.name for a in ctrl.client_db.list_collections()]
    default_collection = collections[0] if collections else None
    collection_choice = st.sidebar.selectbox("Choose a Collection", options=collections, index=0 if default_collection else None)



    Folders_list = None
    selected_documents = []

    query_type = st.sidebar.radio("Query Type", options=["Everything", "Folder", "Document(s)"])

    if query_type == "Folder":
        Folders_list = st.sidebar.multiselect("Select Folder", options=Dict_of_folders["Name"], key="Folders_list")
        if Folders_list:
            folder_indices = [Dict_of_folders["Name"].index(folder) for folder in Folders_list]
            for idx, folder in zip(folder_indices, Folders_list):
                folder_docs = st.sidebar.multiselect(f"Select Document(s) in '{folder}'", options=Dict_of_folders["Files"][idx], key=f"docs_{folder}")
                selected_documents.extend(folder_docs)

    elif query_type == "Document(s)":
        all_documents = set(doc for doc_list in Dict_of_folders["Files"] for doc in doc_list)
        selected_documents = st.sidebar.multiselect("Select Document(s)", options=all_documents, key="Documents_in_folder")


    st.title("Eureka")

    # Initialize chat history and sources
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'sources_info' not in st.session_state:
        st.session_state['sources_info'] = []

    # Function to display chat messages
    def display_chat():
        for message in st.session_state['messages']:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    display_chat()

    # Accept user input
    user_query = st.chat_input("Posez votre question ici")
    if user_query:
        st.session_state['messages'].append({"role": "user", "content": user_query})

        documents = selected_documents if query_type in ["Folder", "Document(s)"] else []

        response, sources = ctrl.get_response(query=user_query, histo=st.session_state['messages'], folder=Folders_list, doc_or_folder=query_type, documents=documents)

        st.session_state['messages'].append({"role": "bot", "content": response})
        st.session_state['sources_info'] = [(source.index, source.title, source.distance_str, source.content) for source in sources[:3]]

        display_chat()  # Update the display with the new messages



if __name__ == "__main__":
    chatbot_control = Chatbot()  # Instantiate Chatbot
    streamlit_user(chatbot_control)
