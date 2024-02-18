import os
import logging.config
from src.control.control import Chatbot
from src.tools.retriever import Retriever
from src.Llm.llm import LlmAgent
import chromadb
from src.view.main import StreamlitApp 
from dotenv import load_dotenv
import os
from mistralai.client import MistralClient

def initialize_logging(logging_config_file_path):
    logging.config.fileConfig(logging_config_file_path)

def initialize_database():
    if not os.path.exists("database_demo2/"): 
        os.makedirs("database_demo2/")
    client_db = chromadb.PersistentClient("database_demo2/")
    client_db.get_or_create_collection("Mistral_Collection")
    return client_db

def initialize_chatbot(client_db, llm_agent):
    return Chatbot(client_db=client_db, llm_agent=llm_agent, retriever=Retriever(llmagent=llm_agent))

def main():
    load_dotenv()
    llm_model = os.getenv("LLM_MODEL")    
    logging_config_file_path = os.getenv("LOGGING_CONFIG_FILE_PATH")
    logfile_path = os.getenv("LOGFILE_PATH")
    dict_of_folders = os.getenv("DICT_OF_FOLDER_PATH")
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    mistral_client = MistralClient(mistral_api_key)
    initialize_logging(logging_config_file_path)
    llm_agent = LlmAgent(llm_model,mistral_client)
    client_db = initialize_database()
    chat = initialize_chatbot(client_db, llm_agent)
    app = StreamlitApp(chat,dict_of_folders)
    app.run()

if __name__ == "__main__":
    main()

