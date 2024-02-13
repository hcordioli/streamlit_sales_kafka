import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader
from llama_index.node_parser import SimpleNodeParser
from llama_index.postprocessor.cohere_rerank import CohereRerank
import os


# Read AWS Credentials from Environment Variable
if "openai_key" not in st.session_state:
    st.secrets.openai_key = os.environ['OPENAI_API_KEY']

# Read AWS Credentials from Environment Variable
if "cohere_api_key" not in st.session_state:
    st.secrets.cohere_api_key = os.environ['COHERE_API_KEY']
    
st.set_page_config(page_title="Balanço Magalu \n Chat powered by LlamaIndex", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

st.title("Demonstrações Financeiras Magalu Dez/2022 com Chat powered by LlamaIndex 💬🦙")
         
if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Qual sua dúvida?"}
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Carregando informações. Isso pode demorar alguns minutos..."):
        reader = SimpleDirectoryReader(input_dir="./magalu", recursive=True)
        docs = reader.load_data()
        node_parser = SimpleNodeParser.from_defaults(chunk_size=512)
        nodes = node_parser.get_nodes_from_documents(docs)
        if "cohere_rerank" not in st.session_state:
            st.session_state['cohere_rerank'] = CohereRerank(api_key=st.secrets.cohere_api_key, top_n=2)
        service_context = ServiceContext.from_defaults(
            llm=OpenAI(
                model="gpt-3.5-turbo", 
                temperature=0.5, 
                system_prompt="O Magazine Luiza, também conhecido como MAGALU, é uma empresa brasileira do setor do varejo multicanal.\
                    Na Bolsa de Valores é cadastrada com o código MGLU3. \
                    Possui mais de 1481 lojas físicas em 21 estados e 819 municípios do país e seu modelo de negócio hoje caracteriza-se como uma plataforma digital com pontos físicos.\
                    Você é um expert nos assuntos financeiros da empresa Magazne Luiza.\
                    Seu trabalho é responder dúvidas dos clientes e investidores do MAGALU.\
                    Assuma que todas as perguntas estão relacionadas ao balanço financeiro do MAGALU que é relativo ao ano de 2022.\
                    Este balanço financeiro foi elaborado pela empresa de consultoria ERNST & YOUNG Auditores Independentes S/S Ltda. \
                    Limite suas respostas em linguagem financeira e baseada em fatos.– não alucine.")
            )
        index = VectorStoreIndex(nodes,service_context=service_context)
        return index

index = load_data()

if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
        #st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)
        st.session_state.chat_engine = index.as_chat_engine(
            chat_mode="condense_question", verbose=True,
            similarity_top_k=10,
            node_postprocessors=[st.session_state['cohere_rerank'] ],
        )
if prompt := st.chat_input("Sua pergunta"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message) # Add response to message history