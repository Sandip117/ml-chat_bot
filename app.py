import os
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from pymongo import MongoClient
import urllib
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from ingestor import store_from_URL

prompt = hub.pull("hwchase17/openai-tools-agent")
llm=ChatOpenAI(model="gpt-4",temperature=0,openai_api_key=os.getenv('OPENAI_API_KEY'))

embeddings=OpenAIEmbeddings()

client=MongoClient()

uri = "mongodb://admin:admin@atlas:27017/?directConnection=true"
# Create a new client and connect to the server
client = MongoClient(uri)
app = Flask(__name__)



# Function to get the most similar document based on user query
def get_most_similar_document(query):
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        collection=client["llm_tutorial"]["langchain"]
        vs=MongoDBAtlasVectorSearch(collection,embeddings,index_name="tutorial_35")
        docs=vs.max_marginal_relevance_search(query,k=10)
        str_response = ""
        for doc in docs:
            str_response += doc.page_content + "\n"
        messages = [
        SystemMessage(
        content=f"You are ChRIS assistant. \
                  Use only this context to answer my questions. \
                  Apologize if you can't answer within the context. \
                  Don't look up in the internet for answers. \
                  Nicely format any code that you reply in markdown format. \
                  Here is your context: {str_response}. \
                  ================================================"
        ),
        HumanMessage(
        content=query
        ),
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return str(e)


# Serve static files (images in this case)
@app.route('/static/<path:filename>')
def static_files(filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join(root_dir, 'static'), filename)


# Endpoint for the main chat page
@app.route('/')
def chat():
    return render_template('chat.html')
    
# Endpoint for the storage page
@app.route('/store/')
def store():
    return render_template('store.html')


# Endpoint for question answering
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    user_query = data['question']

    answer = get_most_similar_document(user_query)

    return jsonify({'answer': answer})
    
# Endpoint for question answering
@app.route('/store', methods=['POST'])
def ingest_data():
    data = request.get_json()
    user_query = data['question']
    answer = store_from_URL(user_query)
    return jsonify({'answer': answer})


if __name__ == '__main__':
    app.run(debug=True)
