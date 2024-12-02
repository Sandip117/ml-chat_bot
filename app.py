import os
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

llm=ChatOpenAI(model="gpt-4o",temperature=0,openai_api_key=os.environ.get('OPENAI_API_KEY'),streaming=True, )
username = os.environ.get('CUBE_USERNAME')
password = os.environ.get('CUBE_PASSWORD')
url = os.environ.get('CUBE_URL')
protocol = os.environ.get('PROTOCOL')

app = Flask(__name__)



# Function to get the most similar document based on user query
def get_most_similar_document(query):
    loader=WebBaseLoader([f"{protocol}://{username}:{password}@{url}"])
    doc=loader.load()
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=0,separators=["\n\n","\n","(?<=\.)"," "],length_function=len)
    docs=splitter.split_documents(doc)
    context = docs

    messages = [
        SystemMessage(
        content=f"You are ChRIS assistant. \
                  Answer only by stating the API endpoint starting with https . \
                  Add authentication credential as sandip:sandip1234 in the API. \
                  Example: {protocol}://{username}:{password}@<api endpoint>. \
                  Do not include any filler words except links. \
                  Use only this context to answer my questions. \
                  Apologize if you can't answer within the context. \
                  Example: My apologies, I am unable to answer your question. \
                  Don't look up in the internet for answers. \
                  Do not use mark down for replying hyperlinks. \
                  Nicely format any code that you reply in markdown format. \
                  Here is your context: {context}. \
                  ================================================"
        ),
        HumanMessage(
        content=query
        ),
        ]
    response = llm.invoke(messages)
    if "apologies," in str(response.content):
        return response.content

    loader=WebBaseLoader([str(response.content)])
    doc=loader.load()
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=0,separators=["\n\n","\n","(?<=\.)"," "],length_function=len)
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
        content=query
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
    

# Endpoint for question answering
@app.route('/ask', methods=['POST'])
def ask_question():
    user_query = request.json.get('question', '')

    def generate(user_query):

        # user_query = data['question']
        answer = get_most_similar_document(user_query)
        # Yield each part of the response as it comes in
        for part in answer:
            if 'choices' in part and 'delta' in part['choices'][0]:
                content = part['choices'][0]['delta'].get('content', '')
                yield f"data: {content}\n\n"  # Server-Sent Event format

    #return jsonify({'answer': answer})
    # Return the response as a stream
    print(generate(user_query))
    return Response(generate(user_query), content_type='text/event-stream')
    


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
