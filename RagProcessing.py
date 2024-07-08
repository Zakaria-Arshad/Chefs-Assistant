import os
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from langchain import hub

class RagProcessing:
    def __init__(self):
        self.vectorStore = None
        self.docs = []
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

    def storeInVectorStore(self, route):
        loader = TextLoader(route)
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100, add_start_index=True
        )
        all_splits = text_splitter.split_documents(data)
        self.vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings(openai_api_key=self.openai_api_key))

    def retrieve(self):
        retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        return retriever

    def generate(self, query="What did the quick brown dog jump over?"):
        llm = ChatOpenAI(model="gpt-3.5-turbo-0125", openai_api_key=self.openai_api_key)
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
        for chunk in rag_chain.stream(query):
            print(chunk, end="", flush=True)





