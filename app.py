import os
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_socketio import SocketIO, emit
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# global variables
llm=ChatOpenAI(model="gpt-4o",
               temperature=0,
               openai_api_key=os.environ.get('OPENAI_API_KEY'),
               streaming=True)
username = os.environ.get('CUBE_USERNAME')
password = os.environ.get('CUBE_PASSWORD')
url = os.environ.get('CUBE_URL')
protocol = os.environ.get('PROTOCOL')

app = Flask(__name__)
socketio = SocketIO(app)



#  Method to get the CUBE API endpoints from LLM
def get_cube_endpoint(query):
    # Routing
    # cube_url = f"{protocol}://{username}:{password}@{url}"
    cube_docs_url = f"{protocol}://{url}"
    loader=WebBaseLoader([cube_docs_url])
    doc=loader.load()
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,
                                            chunk_overlap=0,
                                            separators=["\n\n","\n","(?<=\.)"," "],
                                            length_function=len)
    docs=splitter.split_documents(doc)
    context = docs

    messages = [
        SystemMessage(
        content=f"You are ChRIS assistant. \
                  Answer only by stating the API endpoint starting with http . \
                  Add authentication credential as {username}:{password} in the API. \
                  Example: {protocol}://{username}:{password}@<api endpoint>. \
                  Do not include any filler words except links. \
                  Use only this context to answer my questions. \
                  Apologize if you can't answer within the context. \
                  Example: My apologies, I am unable to answer your question. \
                  Don't look up in the internet for answers. \
                  Do not use mark down for replying hyperlinks. \
                  Here is your context: {context}. \
                  ================================================"
        ),
        HumanMessage(
        content=query
        ),
        ]
    response = llm.invoke(messages)
    if "apologies," in str(response.content):
        emit('stream_response', {'data': response.content})
        raise Exception(f'I could not find a matching CUBE API endpoint for your question.')
    return response.content

# Summarize API response using LLM
def summarize_cube_response(api: str, question: str):
    # Summarizing
    loader=WebBaseLoader([api])
    doc=loader.load()
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,
                                            chunk_overlap=0,
                                            separators=["\n\n","\n","(?<=\.)"," "],
                                            length_function=len)
    docs=splitter.split_documents(doc)
    messages = [
        SystemMessage(
        content=f"You are ChRIS assistant. \
                  Use only this context to answer my questions. \
                  Apologize if you can't answer within the context. \
                  Don't look up in the internet for answers. \
                  Nicely format any code that you reply in markdown format. \
                  Here is your context: {docs}. \
                  ================================================"
        ),
        HumanMessage(
        content=question
        ),
        ]
    response = llm.stream(messages)
    return response
    


# Serve static files (images in this case)
@app.route('/static/<path:filename>')
def static_files(filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join(root_dir, 'static'), filename)


# Endpoint for the main chat page
@app.route('/')
def chat():
    return render_template('chat.html')

# Endpoint for URL fetch page
@app.route('/fetch')
def fetch():
    return render_template('store.html')

# Endpoint for Summary page
@app.route('/summarize')
def summarize():
    return render_template('store.html')

@app.route('/get_endpoint', methods=['GET'])
def get_api():
    return f"{protocol}://{username}:{password}@{url}"

# SocketIO event to handle message streaming
@socketio.on('start_stream')
def handle_message(data):
    input_data = data['message']
    try:
        cube_api = get_cube_endpoint(input_data)
        LLM_resp = summarize_cube_response(cube_api, input_data)
        # Emit the response back to the frontend in chunks
        for chunk in LLM_resp:
            emit('stream_response', {'data': chunk.content})
        emit('stream_response', {'data': ":~"})
    except Exception as ex:
        emit('stream_response',{'data': f"\n{ex}"})




if __name__ == '__main__':
    socketio.run(debug=True, threaded=True)
