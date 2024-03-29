import os
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage


class LlmAgent:

    def __init__(self, llm_model: str,client):
        self.llm = llm_model
        self.client =client

    def send_request_to_mistral(self, messages):
        chat_response = self.client.chat(
            model=self.llm,
            messages=messages,
            temperature=0
        )
        return chat_response.choices[0].message.content

    def create_chat_message(self, role, content):
        return ChatMessage(role=role, content=content)

    def generate_paragraph(self, query: str, context: {}, histo: [(str, str)], language='fr') -> str:
        template = (f"You are a conversation bot designed to answer to the query from users."
                    f"Your answer is based on the context delimited by triple backticks :\n ``` {context} ```\n"
                    f"You are consistent and avoid redundancies with the rest of the initial conversation delimited by triple backticks :\n ``` {histo} ```\n"
                    f"Your response shall be in {language} and shall be concise."
                    f"You shall only provide the answer, nothing else before and after."
                    f"Here is the query you are given :\n"
                    f"``` {query} ```")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)

    def generate_paragraph_v2(self, query: str, context: {}, histo: [(str, str)], language='fr') -> str:
        """generates the  answer"""
        template = (f"You are a conversation bot designed to answer to the query from users."
                    f"Here is the query to answer : {query} in french"
                    f"Your answer is based on the context delimited by triple backticks :\n ``` {context} ```\n and your personal knowledge"
                    f"You are consistent and avoid redundancies with the rest of the initial conversation delimited by triple backticks :\n ``` {histo} ```\n"
                    f"Your response shall be in french and shall be concise.")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)

    def translate(self, text: str) -> str:
        """translates"""
        template = (f"Your task consists in translating in English the following text delimited by triple backticks: ``` {text} ```\n"
                    f"If the text is already in English, just return it !\n"
                    f"Your must not provide an answer to the text, just translate it.\n")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)
    
    
    def translate_v2(self, text: str) -> str:
        """translates"""
        template = "Translate in english the text. If it is already in english, just return the text."
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)

    def generate_answer(self, query: str, answer: str, histo: str, context: str,language : str) -> str:
        """provides the final answer in {language} based on the initial query and the answer in english"""
        template = (f"Your task consists in translating the answer in {language}, if its not already the case, to the query "
                    f"delimited by triple backticks: ```{query}``` \n"
                    f"You don't add new content to the answer but: "
                    f"1 You can use some vocabulary from the context delimited by triple backticks:\n"
                    f"```{context}```\n"
                    f"2 You are consistent and avoid redundancies with the rest of the initial"
                    f"conversation delimited by triple backticks: ```{histo}```\n"
                    f"Your response shall respect the following format:<response>\n"
                    f"Here is the answer you are given in {language}:"
                    f"{answer}")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)
    
    def summarize_paragraph(self, prompt : str, title_doc : str = '',title_para : str = ''):
        max_tokens = 700
        """summarizes the paragraph"""
        template = (f"Your task consists in summarizing the paragraph of the document untitled ```{title_doc}```."
                    f"The paragraph title is ```{title_para}```."
                    f"Your response shall be concise and shall respect the following format:"
                    f"<summary>"
                    f"If you see that the summary that you are creating will not respect ```{max_tokens}``` tokens, find a way to make it shorter."
                    f"The paragraph you need to summarize is the following :"
                    f"{prompt}")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)
    
    def summarize_paragraph_v2(self, prompt : str, title_doc : str = '', title_para : str = ''):
        max_tokens = 850
        location_of_the_paragraph = prompt.split(" :")[0]
        """summarizes the paragraph"""
        template = (f"Your task consists in summarizing in English the paragraph of the document untitled ```{title_doc}``` located in the ```{location_of_the_paragraph}``` section of the document."
                    f"The paragraph title is ```{title_para}```."
                    f"Your response shall be concise and shall respect the following format:"
                    f"<summary>"
                    f"If you see that the summary that you are creating will not respect ```{max_tokens}``` tokens, find a way to make it shorter.")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)
    
    def detect_language(self, text: str) -> str:
        """detects the language"""
        template = (f"Your task consists in detecting the language of the last question or sentence of the text."
                    f"You should only give the two letters code of the language detected, nothing else."
                    f"Here is the text you are given delimited by triple backticks : ```{text}```")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)
    
    def detect_language_v2(self, text: str) -> str:
        """detects the language"""
        template = (f"Your task consists in detecting the language of the last question or sentence of the text."
                f"You should only give the two letters code of the language detected, nothing else.")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)


    def detect_language_v2(self, text: str) -> str:
        """detects the language"""
        template = (f"Your task consists in detecting the language of the last question or sentence of the text."
                f"You should only give the two letters code of the language detected, nothing else.")
        messages = [self.create_chat_message("user", template)]
        response = self.send_request_to_mistral(messages)
        print("****************")
        print(response)
        print("----")
        return str(response)


