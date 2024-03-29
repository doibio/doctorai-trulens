import os
import sys

os.environ["OPENAI_API_KEY"] = "***"

from openai import OpenAI
oai_client = OpenAI()

def read_file(filename):
    """Reads the content of a file and returns it."""
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."

university_info = ""

if len(sys.argv) != 3:
    print("Usage: script.py <filename> <filename>")
else:
    filename0 = sys.argv[1]
    university_info = read_file(filename0)
    print(university_info)
    filename1 = sys.argv[2]
    advert = read_file(filename1)

oai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=university_info
    )

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI
oai_client = OpenAI()

embedding_function = OpenAIEmbeddingFunction(api_key=os.environ.get('OPENAI_API_KEY'),
                                             model_name="text-embedding-ada-002")

chroma_client = chromadb.PersistentClient(path="./chromadb")

vector_store = chroma_client.get_or_create_collection(name="Universities",
                                                      embedding_function=embedding_function)

vector_store.add("uni_info", documents=university_info)

from trulens_eval import Tru
from trulens_eval.tru_custom_app import instrument
tru = Tru()

class RAG_from_scratch:
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        results = vector_store.query(
        query_texts=query,
        n_results=2
    )
        return results['documents'][0]

    @instrument
    def generate_completion(self, query: str, context_str: list) -> str:
        """
        Generate answer from context.
        """
        completion = oai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=
        [
            {"role": "user",
            "content": 
            f"We have provided context information below. \n"
            f"---------------------\n"
            f"{context_str}"
            f"\n---------------------\n"
            f"Given this information, please answer the question: {query}"
            }
        ]
        ).choices[0].message.content
        return completion

    @instrument
    def query(self, query: str) -> str:
        context_str = self.retrieve(query)
        completion = self.generate_completion(query, context_str)
        return completion

rag = RAG_from_scratch()

from trulens_eval import Feedback, Select
from trulens_eval.feedback import Groundedness
from trulens_eval.feedback.provider.openai import OpenAI as fOpenAI

import numpy as np

# Initialize provider class
fopenai = fOpenAI()

grounded = Groundedness(groundedness_provider=fopenai)

# Define a groundedness feedback function
f_groundedness = (
    Feedback(grounded.groundedness_measure_with_cot_reasons, name = "Groundedness")
    .on(Select.RecordCalls.retrieve.rets.collect())
    .on_output()
    .aggregate(grounded.grounded_statements_aggregator)
)

# Question/answer relevance between overall question and answer.
f_qa_relevance = (
    Feedback(fopenai.relevance_with_cot_reasons, name = "Answer Relevance")
    .on(Select.RecordCalls.retrieve.args.query)
    .on_output()
)

# Question/statement relevance between question and each context chunk.
f_context_relevance = (
    Feedback(fopenai.qs_relevance_with_cot_reasons, name = "Context Relevance")
    .on(Select.RecordCalls.retrieve.args.query)
    .on(Select.RecordCalls.retrieve.rets.collect())
    .aggregate(np.mean)
)

from trulens_eval import TruCustomApp
tru_rag = TruCustomApp(rag,
    app_id = filename1,
    feedbacks = [f_groundedness, f_qa_relevance, f_context_relevance])

with tru_rag as recording:
    rag.query("Is the following a good way to convince a 40 year old tech startup CEO to exercise? " + advert)

a = tru.get_leaderboard(app_ids=[filename1])
print("----------")
print(a)
print("----------")

tru.run_dashboard()

chroma_client.delete_collection("Universities")

