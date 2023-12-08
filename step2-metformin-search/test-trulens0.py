import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI
from trulens_eval import Tru
from trulens_eval.tru_custom_app import instrument
from trulens_eval import Feedback, Select
from trulens_eval.feedback import Groundedness
from trulens_eval.feedback.provider.openai import OpenAI as fOpenAI
import numpy as np
from trulens_eval import TruCustomApp

os.environ["OPENAI_API_KEY"] = "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"

oai_client = OpenAI()

embedding_function = OpenAIEmbeddingFunction(api_key=os.environ.get('OPENAI_API_KEY'), model_name="text-embedding-ada-002")

chroma_client = chromadb.PersistentClient(path="./chromadb")

vector_store = chroma_client.get_or_create_collection(name="Universities", embedding_function=embedding_function)

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

fopenai = fOpenAI()

grounded = Groundedness(groundedness_provider=fopenai)

f_groundedness = (
    Feedback(grounded.groundedness_measure_with_cot_reasons, name = "Groundedness")
    .on(Select.RecordCalls.retrieve.rets.collect())
    .on_output()
    .aggregate(grounded.grounded_statements_aggregator)
)

f_qa_relevance = (
    Feedback(fopenai.relevance_with_cot_reasons, name = "Answer Relevance")
    .on(Select.RecordCalls.retrieve.args.query)
    .on_output()
)

f_context_relevance = (
    Feedback(fopenai.qs_relevance_with_cot_reasons, name = "Context Relevance")
    .on(Select.RecordCalls.retrieve.args.query)
    .on(Select.RecordCalls.retrieve.rets.collect())
    .aggregate(np.mean)
)

def run_rag(filename,university_info):
    print("------------------------------")
    print(content)
    oai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=university_info
    )
    vector_store = chroma_client.get_or_create_collection(name="Universities", embedding_function=embedding_function)

    vector_store.add("uni_info", documents=university_info)
    tru_rag = TruCustomApp(rag, app_id = filename, feedbacks = [f_groundedness, f_qa_relevance, f_context_relevance])

    with tru_rag as recording:
        rag.query("Is metformin capable of increasing lifespan?")

    chroma_client.delete_collection("Universities")

# main 
tru.run_dashboard()

directory = 'edirectm'

for filename in os.listdir(directory):
    if filename.endswith(".txt"):
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            run_rag(filename,content)
            

