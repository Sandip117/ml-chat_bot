from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from pymongo import MongoClient
import urllib


def store_from_URL(url: str) -> str:
    try:
        loader=WebBaseLoader([url])
        doc=loader.load()
        splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=0,separators=["\n\n","\n","(?<=\.)"," "],length_function=len)
        docs=splitter.split_documents(doc)
        embeddings=OpenAIEmbeddings()
        client=MongoClient()

        uri = "mongodb://admin:admin@atlas:27017/?directConnection=true"
        # Create a new client and connect to the server
        client = MongoClient(uri)
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        collection=client["llm_tutorial"]["langchain"]
        docsearch=MongoDBAtlasVectorSearch.from_documents(docs,embeddings,collection=collection,index_name="tutorial_35")
     
        collection.create_search_index(
        {"definition":
            {"mappings": {"dynamic": True, "fields": {
                "embedding" : {
                    "dimensions": 1536,
                    "similarity": "dotProduct",
                    "type": "knnVector"
                    }}}},
         "name": "tutorial_35"
        }
        )
        return f"Documents are stored into mongodb vector store successfully!"
    except Exception as e:
        return str(e)
