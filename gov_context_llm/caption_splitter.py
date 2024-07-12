from langchain_community.document_loaders import SRTLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from gov_context_llm.vector_db import get_vector_db
from langchain.storage._lc_store import create_kv_docstore
from langchain.storage.file_system import LocalFileStore
from langchain.retrievers import ParentDocumentRetriever
import os
import re

directory = "data/raw/transcripts"

date_regex = re.compile("data/raw/transcripts/(?P<date>\d{4}/\d{1,2}/\d{1,2})")

pages_to_load = []
for root, dirs, files in os.walk(directory):
    for filename in files:
        filepath = os.path.join(root, filename)
        if os.path.isfile(filepath) and ".srt" in filepath:
            search = date_regex.search(filepath)
            if not search:
                continue
            date_parts = search.group("date").split("/")
            year = date_parts[0]
            month = date_parts[1]
            day = date_parts[2]
            loader = SRTLoader(filepath)
            pages = loader.load()
            for page in pages:

                page.metadata = {
                    **page.metadata,
                    "year": year,
                    "month": month,
                    "day": day,
                    "type": "transcript",
                    "meeting_date": f"{month}/{day}/{year}",
                }
                pages_to_load.append(page)


fs = LocalFileStore("docs/parent-retriever/store_location")
store = create_kv_docstore(fs)
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

vectordb = get_vector_db()
retriever = ParentDocumentRetriever(
    vectorstore=vectordb,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
retriever.add_documents(pages_to_load, ids=None)
