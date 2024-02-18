import os
from src.tools.retriever import Retriever
from src.Llm.llm import LlmAgent
from src.model.block import Block
from src.model.doc import Doc
import logging 
import time
import streamlit as st
import yake

class Chatbot:

    def __init__(self, retriever: Retriever = None, client_db=None, llm_agent : LlmAgent = None):
        self.llm = llm_agent
        self.retriever = retriever
        self.client_db = client_db

    def get_response(self, query, histo, folder, doc_or_folder , documents):
        timestart = time.time()
        histo_conversation, histo_queries = self._get_histo(histo)
        # language_of_query = self.llm.detect_language_v2(query).lower()
        #queries = self.llm.translate_v2(histo_queries)
        # if "en" in language_of_query:
        #     language_of_query = "en"
        # else:
        #     language_of_query = "fr"
        
        # block_sources = self.retriever.similarity_search(queries=queries)
        language_of_query = "en"
        timestart = time.time()
        histo_conversation, histo_queries = self._get_histo(histo)
        
        block_sources_similarity = self.retriever.similarity_search(queries=query, folder=folder, document_or_folder=doc_or_folder, documents=documents)

        ###### TEST Keyword Extraction ######=

        # text = query
        # max_ngram_size = 1
        # deduplication_threshold = 0.9
        # numOfKeywords = 2
        # custom_kw_extractor = yake.KeywordExtractor( n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
        # keywords = custom_kw_extractor.extract_keywords(text)
        # print("@@@@@@@@@@@@@@@@@@")
        # print(keywords)
        # print("@@@@@@@@@@@@@@@@@@")

        # keywords = [k[0] for k in keywords]
        # block_sources_keywords =  self.retriever.keyword(queries=query, keywords =keywords , folder=folder, document_or_folder=doc_or_folder, documents=documents) 
              
        # combined_sources = list(set(block_sources_similarity + block_sources_keywords))        
                      
        block_sources = self._select_best_sources(block_sources_similarity)
        
        sources_contents = [f"Paragraph title : {s.title}\n-----\n{s.content}" if s.title else f"Paragraph {s.index}\n-----\n{s.content}" for s in block_sources]
        context = '\n'.join(sources_contents)
        i = 1
        while (len(context) + len(histo_conversation) > 15000) and i < len(sources_contents):
            context = "\n".join(sources_contents[:-i])
            i += 1
        print("Query: ", query, ", Type: ", type(query))
        if isinstance(query, (list, dict)):
            print("Length of Query: ", len(query))

        print("Histo: ", histo_conversation, ", Type: ", type(histo_conversation))
        if isinstance(histo_conversation, (list, dict)):
            print("Length of Histo: ", len(histo_conversation))

        print("Context: ", context, ", Type: ", type(context))
        if isinstance(context, (list, dict)):
            print("Length of Context: ", len(context))

        print("Language: ", language_of_query, ", Type: ", type(language_of_query))
        if isinstance(language_of_query, (list, dict)):
            print("Length of Language: ", len(language_of_query)) 
        
        answer = self.llm.generate_paragraph_v2(query=query, histo=histo_conversation, context=context, language=language_of_query)   
        answer = self._clean_chatgpt_answer(answer)
        timeend  = time.time()
        exec_time = timeend - timestart
        collection = self.retriever.collection
        logging.info(f"Collection: {collection.name}   , Query: {query} , Answer: {answer},  Sources: {sources_contents}", extra={'category': 'Query', 'elapsed_time':exec_time})

        return answer, block_sources

    

    @staticmethod
    def  _select_best_sources(sources: [Block], delta_1_2=0.15, delta_1_n=0.3, absolute=1.2, alpha=0.9) -> [Block]:
        """
        Select the best sources: not far from the very best, not far from the last selected, and not too bad per se
        """
        best_sources = []
        for idx, s in enumerate(sources):
            if idx == 0 \
                    or (s.distance - sources[idx - 1].distance < delta_1_2
                        and s.distance - sources[0].distance < delta_1_n) \
                    or s.distance < absolute:
                best_sources.append(s)
                delta_1_2 *= alpha
                delta_1_n *= alpha
                absolute *= alpha
            else:
                break
        return best_sources
    

    @staticmethod
    def _get_histo(histo: [(str, str)]) -> (str, str):
        histo_conversation = ""
        histo_queries = ""

        for (query, answer) in histo[-5:]:
            histo_conversation += f'user: {query} \n bot: {answer}\n'
            histo_queries += query + '\n'
        return histo_conversation[:-1], histo_queries
    

    @staticmethod
    def _clean_answer(answer: str) -> str:
        print(answer)
        answer = answer.strip('bot:')
        while answer and answer[-1] in {"'", '"', " ", "`"}:
            answer = answer[:-1]
        while answer and answer[0] in {"'", '"', " ", "`"}:
            answer = answer[1:]
        answer = answer.strip('bot:')
        if answer:
            if answer[-1] != ".":
                answer += "."
        return answer
    
    def _clean_chatgpt_answer(self,answer: str) -> str:
        answer = answer.strip('bot:')
        answer = answer.strip('Answer:')
        answer = answer.strip('Réponse:')
        while answer and answer[-1] in {"'", '"', " ", "`"}:
            answer = answer[:-1]
        return answer
    
    def upload_doc(self, input_doc_path, include_images_, actual_page_start, original_file_name):
        title = original_file_name  # The original file name, including extension
        print(title)
        extension = title.split('.')[-1]
        print(extension)
        if extension and extension in ['docx', 'pdf', 'html', 'xlsx']:

            # Use the collection from the retriever
            try: 
                collection = self.client_db.get_collection(name=self.retriever.collection.name)
            except:
                st.warning("Please select a collection to ingest your document")
                return False

            if collection.count() >= 0:
                st.info("Please wait while your document is being analysed")
                print("Database is empty")
                # Use input_doc_path here
                doc = Doc(path=input_doc_path, original_file_name=original_file_name, include_images=include_images_, actual_first_page=actual_page_start)

                retriever = Retriever(doc.container, collection=collection, llmagent=self.llm)
            else:
                print("Database is not empty")
                retriever = Retriever(collection=collection, llmagent=self.llm)

            self.retriever = retriever
            return True
        else:
            st.error("File extension not supported. Only .docx, .pdf, .html, and .xlsx are supported.")
            return False
    

    def list_models(self,model_dir):
        """
        List all files in the given directory.

        Args:
        model_dir (str): Directory containing model files.

        Returns:
        list: A list of filenames in the specified directory.
        """
        
        return [f for f in os.listdir(model_dir) if os.path.isfile(os.path.join(model_dir, f))]
    
    

