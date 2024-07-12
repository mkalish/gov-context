from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI
from langchain.retrievers import MergerRetriever

# from langchain.retrievers import ContextualCompressionRetriever
# from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.storage._lc_store import create_kv_docstore
from langchain.storage.file_system import LocalFileStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter

metadata_field_info = [
    AttributeInfo(
        name="source",
        description="What original source the document is from",
        type="string",
    ),
    AttributeInfo(
        name="year", description="The year the meeting occurred", type="integer"
    ),
    AttributeInfo(
        name="month",
        description="The month of the year the meeting occurred",
        type="integer",
    ),
    AttributeInfo(
        name="day",
        description="The day of the month the meeting occurred",
        type="integer",
    ),
    AttributeInfo(
        name="type",
        description="the type of original source document",
        type="'transcript' or  'summary'",
    ),
]


def get_vector_db(persist_directory: str = "docs/chroma/") -> Chroma:
    embedding = OpenAIEmbeddings()
    vectordb = Chroma(embedding_function=embedding, persist_directory=persist_directory)
    return vectordb


def get_vector_db_retriever() -> MergerRetriever:
    vectordb = get_vector_db()
    fs = LocalFileStore("docs/parent-retriever/store_location")
    store = create_kv_docstore(fs)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

    parent_document_retriever = ParentDocumentRetriever(
        vectorstore=vectordb,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    self_query_retriever = SelfQueryRetriever.from_llm(
        llm,
        vectordb,
        "Transcripts from fairfax county board of supervisor meetings",
        metadata_field_info,
        verbose=True,
    )
    # compressor = LLMChainExtractor.from_llm(llm)
    # compression_retriever = ContextualCompressionRetriever(
    #     base_compressor=compressor,
    #     base_retriever=vectordb.as_retriever(search_kwargs={"k": 20}),
    # )
    return MergerRetriever(retrievers=[self_query_retriever, parent_document_retriever])
