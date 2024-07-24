import os
from Database import Database

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_cohere import CohereEmbeddings
from langchain_postgres.vectorstores import PGVector

from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document

class StringLoader(BaseLoader):
    def __init__(self, text: str):
        self.text = text if text else "No info"

    def load(self):
        return [Document(page_content=self.text)]

class RagProcessing:
    def __init__(self):
        self.docs = []
        self.chat_history = []
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.vectorstore = self.getVectorStore()


    def getVectorStore(self):
        collection_name = "testing"
        embeddings = CohereEmbeddings(model="embed-english-v3.0")
        return PGVector(collection_name=collection_name, embeddings=embeddings, connection=Database.getEngine(), use_jsonb=True)

    def storeInVectorStore(self, txt, original_id):
        loader = StringLoader(txt)
        data = loader.load()  # is a list, access first element
        data[0].metadata["original_doc_id"] = original_id  # string of UUID
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100, add_start_index=True
        )
        all_splits = text_splitter.split_documents(data)
        self.vectorstore.add_documents(all_splits)

    def retrieve(self):
        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        return retriever

    def generate(self, query="No question"):
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=self.openai_api_key)
        retriever = self.retrieve()

        custom_prompt_template = PromptTemplate.from_template("""
        Given the following context, and previous conversation you have had with the user, answer the question. In the context, The term "I" refers to the person you are talking with.

        Context and previous chats:
        {context}
        

        Question:
        {question}

        Answer:
        """)

        def format_docs(docs):
            print(docs)
            return "\n\n".join(doc.page_content for doc in docs) + "Previous chat history" + "\n\n".join(self.chat_history)

        # query passed to retriever -> formatted. stored in context. question is the query itself.
        rag_chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | custom_prompt_template
                | llm
                | StrOutputParser()
        )
        response = {"response": " ".join(rag_chain.stream(query))}
        self.chat_history.append(query)
        self.chat_history.append(response["response"])

        return response










