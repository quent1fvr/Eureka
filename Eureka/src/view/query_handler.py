import streamlit as st

class UserQueryHandler:
    @staticmethod
    def handle_user_query(ctrl, query_type, selected_documents, Folders_list):
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
                ChatDisplay.display_chat()
                

class SourceDisplay:
    @staticmethod
    def display_sources():
        if st.session_state['sources_info']:
            with st.expander("View Sources"):
                for index, (source_index, title, score, content) in enumerate(st.session_state['sources_info']):
                    st.markdown(f"**Source {source_index}: {title}** (score = {score})")
                    st.text_area(f"source_content_{index}", value=content, height=100, disabled=True, key=f"source_content_{index}")
    @staticmethod
    def get_sources_contents():
        return [source_content for _, _, _, source_content in st.session_state['sources_info']]
    
    
# Chat display
class ChatDisplay:
    @staticmethod
    def display_chat():
        """Function to display chat messages."""
        for message in st.session_state['messages']:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

class SessionState:
    @staticmethod
    def initialize():
        """Initialize session state variables for chat management."""
        if 'clear_chat_flag' not in st.session_state:
            st.session_state['clear_chat_flag'] = False
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []
        if 'sources_info' not in st.session_state:
            st.session_state['sources_info'] = []