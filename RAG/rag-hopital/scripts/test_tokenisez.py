from transformers import AutoTokenizer
from rag_hopital.config import settings

tokenizer = AutoTokenizer.from_pretrained(
    settings.embedder_path,
    local_files_only=True,
)

text = "Le patient présente une insuffisance rénale chronique."

print("Tokenizer:", tokenizer.name_or_path)
print("Tokens:", len(tokenizer.encode(text)))