import os

from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_cohere import CohereEmbeddings
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document

class StringLoader(BaseLoader):
    def __init__(self, text: str):
        self.text = text

    def load(self):
        return [Document(page_content=self.text)]


class RagProcessing:
    def __init__(self):
        self.vectorStore = None
        self.docs = []
        self.chat_history = []
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.host = os.getenv('HOST')
        self.user = os.getenv('USER')
        self.password = os.getenv('PASSWORD')
        self.database = os.getenv('DATABASE')
        self.conn_string = f"postgresql+psycopg://{self.user}:{self.password}@{self.host}/{self.database}"
        self.engine = create_engine(self.conn_string)
        self.Session = sessionmaker(bind=self.engine)


    def getVectorStore(self):
        if self.vectorStore:
            return self.vectorStore
        collection_name = "testing"
        embeddings = CohereEmbeddings(model="embed-english-v3.0")
        return PGVector(collection_name=collection_name, embeddings=embeddings, connection=self.engine, use_jsonb=True)

    def storeInVectorStore(self, txt):
        loader = StringLoader(txt)
        data = loader.load()
        data[0].metadata["original_doc_id"] = 1
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100, add_start_index=True
        )
        all_splits = text_splitter.split_documents(data)
        self.vectorstore = self.getVectorStore()
        self.vectorstore.add_documents(all_splits)
        self.close_connection()

    def retrieve(self):
        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        return retriever

    def generate(self, query="What did the quick brown dog jump over?"):
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=self.openai_api_key)
        retriever = self.retrieve()

        custom_prompt_template = PromptTemplate.from_template("""
        Given the following context, answer the question.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | custom_prompt_template
                | llm
                | StrOutputParser()
        )
        response = {"response": " ".join(rag_chain.stream(query))}
        return response

    def close_connection(self):
        self.engine.dispose()








