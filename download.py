from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "t5-small"
local_dir = r"C:\Users\Dell\Documents\blah"

# Download and save the model locally
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=(r"C:\Users\Dell\Documents\blah"))
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=(r"C:\Users\Dell\Documents\blah"))
