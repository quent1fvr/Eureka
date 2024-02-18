from chromadb.utils import embedding_functions

def create_embedding_model(use_open_source_embeddings: bool):
    """
    Factory function to create and return an embedding model.
    
    :param use_open_source: Boolean flag to determine which embedding model to use.
    :return: Instance of the chosen embedding model.
    """

