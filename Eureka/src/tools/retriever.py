from src.model.block import Block
from src.model.doc import Doc
from src.Llm.llm import LlmAgent
from mistralai.client import MistralClient

client = MistralClient(api_key="n70UAHiVwZLbJW5jj1xpT5zRDCRtpozp")

class Retriever:
    """
    The Retriever class is responsible for processing and summarizing documents.
    It supports operations such as summarizing individual blocks of text, organizing
    text into a hierarchy, and conducting similarity searches within a collection of documents.
    
    Attributes:
        collection: A collection object where summaries and metadata are stored.
        llmagent: An instance of LlmAgent used for generating summaries.
    """

    def __init__(self, doc: Doc = None, collection=None, llmagent: LlmAgent = None):
        """
        Initializes the Retriever class with a document, a collection, and a language model agent.

        Args:
            doc: A document object containing text blocks to be processed.
            collection: A collection object to store summaries and metadata.
            llmagent: An instance of LlmAgent for generating summaries.
        """

        if doc is not None:
            self.collection = collection
            blocks_good_format = doc.blocks  # List of Block objects from the document.

            # Process each block in the document.
            for block in blocks_good_format:
                print(f"block index : {block.index}")
                print(doc.title)

                # If block content is longer than 4500 characters, split and summarize separately.
                print(f"block content:{len(block.content)}")
                if len(block.content) > 4000:
                    
                    new_blocks = block.separate_1_block_in_n(max_size=3000)
                    print(f"new_blocks : {len(new_blocks)}")
                    for new_block in new_blocks:
                        summary = llmagent.summarize_paragraph_v2(prompt=new_block.content, title_doc=doc.title, title_para=block.title)
                        
                        if "<summary>" in summary:
                            summary = summary.split("<summary>")[1]

                        embeddings_batch_response = client.embeddings(model="mistral-embed", input=[summary])
                        embedded_summary =    embeddings_batch_response.data[0].embedding                            
                        self.collection.add(
                            documents= [summary],
                            embeddings=[embedded_summary],
                            ids=[new_block.index],
                            metadatas= [new_block.to_dict()]
                        )
                else:
                    # Summarize the block as is if it's shorter than 4500 characters.
                    print(doc.title)
                    summary = llmagent.summarize_paragraph_v2(prompt=block.content, title_doc=doc.title, title_para=block.title)
                    embeddings_batch_response = client.embeddings(model="mistral-embed", input=[summary])
                    embedded_summary =    embeddings_batch_response.data[0].embedding
                    if "<summary>" in summary:
                        summary = summary.split("<summary>")[1]
                    self.collection.add(
                        documents= [summary],
                        embeddings=[embedded_summary],
                        ids=[block.index],
                        metadatas= [block.to_dict()],
                    )
                    print(block.to_dict())
                    print(self.collection.name)
            # Summarize blocks by their hierarchy level after individual processing.
            self.summarize_by_hierarchy(blocks_good_format, llmagent, doc.title)
        else:
            self.collection = collection
            
    def summarize_by_hierarchy(self, blocks, llmagent, doc_title):
        """
        Summarizes blocks based on their hierarchical levels.

        Args:
            blocks: A list of Block objects to be summarized.
            llmagent: An instance of LlmAgent used for generating summaries.
            doc_title: The title of the document being processed.
        """
        hierarchy = self.create_hierarchy(blocks)
        deepest_blocks_indices = self.find_deepest_blocks(blocks)
        print("Hierarchy levels identified:", hierarchy.keys())
        print("Deepest block indices:", [block.index for block in deepest_blocks_indices])
            
        for level, level_blocks in hierarchy.items():
            # Summarize only if the level has more than one block and contains deepest blocks.
            print(level)
            print(level_blocks)
            print(deepest_blocks_indices)
            print(len(level_blocks))
            if len(level_blocks) > 1 and any(block.index in deepest_blocks_indices for block in level_blocks):
                level_content = " ".join(block.content for block in level_blocks)
                
                print(f"Summarizing level {level} with content from blocks: {[block.index for block in level_blocks]}")
                level_summary = llmagent.summarize_paragraph_v2(prompt=level_content, title_doc=doc_title, title_para=f"Summary of section : {level}")                
                
                level_summary_id = f"summary_{level}"
        # Initialize a new Block object with properties from the first block
        
                first_block = level_blocks[0]
                combined_block = Block(
                    doc=first_block.doc, 
                    title=first_block.title, 
                    content=" ".join(block.content for block in level_blocks),
                    index=first_block.index, 
                    rank=first_block.rank, 
                    level=first_block.level, 
                    distance=first_block.distance
                )

                embeddings_batch_response = client.embeddings(model="mistral-embed", input=[level_summary])
                embedded_summary =    embeddings_batch_response.data[0].embedding
                self.collection.add(
                   documents= [level_summary],
                    embeddings=[embedded_summary],
                    ids=[ level_summary_id],
                    metadatas=[combined_block.to_dict()]
                )
                 # List of dictionaries, each representing a block
                
                print(f"Added summary for level {level} to the collection.")
            else:
                # Skip summarization for levels that are deepest blocks.
                print(f"Skipping level {level} as it is deepest blocks.")


    def create_hierarchy(self, blocks):
        """
        Creates a hierarchical structure of the blocks based on their indices.

        Args:
            blocks: A list of Block objects to be organized into a hierarchy.

        Returns:
            A dictionary representing the hierarchy of blocks.
        """
        hierarchy = {}
        for block in blocks:
            levels = self.extract_levels(block.index)
            for level in levels:
                hierarchy.setdefault(level, []).append(block)
        return hierarchy


    def extract_levels(self, index):
        """
        Extracts all hierarchical levels from a block index.

        Args:
            index: The index string of a block.

        Returns:
            A list of levels extracted from the index.
        """
        # Splits the index string and creates a list of hierarchical levels.
        parts = index.split('.')
        levels = ['.'.join(parts[:i]) for i in range(1, len(parts) + 1)]
        return levels
    
    
    def find_deepest_blocks(self, blocks):
        """
        Identifies the deepest blocks in the hierarchy.

        Args:
            blocks: A list of Block objects.

        Returns:
            A set of indices representing the deepest blocks.
        """
        deepest_blocks = set()
        block_indices = {block.index for block in blocks}
        for block in blocks:
            # A block is considered deepest if no other block's index extends it.
            if not any(b_index != block.index and b_index.startswith(block.index + '.') for b_index in block_indices):
                deepest_blocks.add(block.index)
        return deepest_blocks



    def similarity_search(self, queries: str, folder, document_or_folder, documents) -> {}:
        """
        Performs a similarity search in the collection based on given queries.

        Args:
            queries: A string or list of strings representing the query or queries.

        Returns:
            A list of Block objects that are similar to the given queries.
        """
        # Query the collection and retrieve blocks based on similarity.
        import json
        with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Eureka/src/ressources/dict_of_folders.json', 'r') as file:
            Dict_of_folders = json.load(file)

        condition = {}
        if document_or_folder == "Folder":
            # Handle folder-based search
            if folder:
                # Fetch files from specified folders
                files_for_folder = [f["files"] for f in Dict_of_folders["entries"] if f["name"] in folder]
                if files_for_folder:
                    # Flatten the list of lists to a single list of files
                    condition = {"doc": {"$in": [file for sublist in files_for_folder for file in sublist]}}
        elif document_or_folder == "Document(s)":
            # Handle document-based search
            if documents:
                condition = {"doc": {"$in": documents}}
        embed_query = client.embeddings(
            model="mistral-embed",
            input=[queries])
        embed_query = embed_query.data[0].embedding

        res = self.collection.query(query_embeddings=embed_query, n_results=8, where=condition)
        
        block_dict_sources = res['metadatas'][0]
        distances = res['distances'][0]

        blocks = []
        for bd, d in zip(block_dict_sources, distances):
            b = Block().from_dict(bd)
            b.distance = d
            blocks.append(b)

        return blocks



    def keyword(self, queries,  keywords, folder, document_or_folder, documents) -> {}:
        """
        Performs a similarity search in the collection based on given queries.

        Args:
            queries: A string or list of strings representing the query or queries.

        Returns:
            A list of Block objects that are similar to the given queries.
        """
        # Query the collection and retrieve blocks based on similarity.
        import json
        with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Eureka/src/ressources/dict_of_folders.json', 'r') as file:
            Dict_of_folders = json.load(file)

        condition = {}
        if document_or_folder == "Folder":
            # Handle folder-based search
            if folder:
                # Fetch files from specified folders
                files_for_folder = [f["files"] for f in Dict_of_folders["entries"] if f["name"] in folder]
                if files_for_folder:
                    # Flatten the list of lists to a single list of files
                    
                    condition = {"doc": {"$in": [file for sublist in files_for_folder for file in sublist]}}
        elif document_or_folder == "Document(s)":
            # Handle document-based search
            if documents:
                condition = {"doc": {"$in": documents},}
                
        embed_query = client.embeddings(
            model="mistral-embed",
            input=[queries])
        embed_query = embed_query.data[0].embedding
        blocks = []

        for i in range(len(keywords)):
            print ("&&&&&&&&&&&")
            print (keywords[i])
            where_document={"$contains": keywords[i]}
            res = self.collection.query(query_embeddings=embed_query, n_results=8, where=condition,where_document=where_document)
            block_dict_sources = res['metadatas'][0]
            distances = res['distances'][0]

            for bd, d in zip(block_dict_sources, distances):
                b = Block().from_dict(bd)
                b.distance = d
                blocks.append(b)

        return blocks

