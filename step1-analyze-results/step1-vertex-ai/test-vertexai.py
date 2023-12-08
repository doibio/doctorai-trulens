import vertexai
from vertexai.language_models import TextGenerationModel

import sys

def read_file(filename):
    """Reads the content of a file and returns it."""
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "File not found."

content = "Please write two convincing sentences as a chat message for a "

if len(sys.argv) != 3:
    print("Usage: script.py <filename> age")
else:
    filename = sys.argv[1]
    age = sys.argv[2]
    content += age
    content += " year old who is interested in life extension about why exercise can help you live longer.  Do not mention her age please.  Use the following information."
    content += read_file(filename)
    
vertexai.init(project="amiable-elf-396321", location="us-central1")
parameters = {
    "candidate_count": 1,
    "max_output_tokens": 1024,
    "temperature": 1.0,
    "top_p": 0.99,
    "top_k": 40
}

model = TextGenerationModel.from_pretrained("text-bison")
response = model.predict(
    content,
    **parameters
)
print(response.text)

