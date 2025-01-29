from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load pre-trained GPT2 model and tokenizer
model_name = 'gpt2'  # You can also try other models like 'gpt2-medium', 'gpt2-large', etc.
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Function to generate resume text from skills, experience, and education
def generate_resume_text(skills, experience, education):
    input_text = f"Skills: {skills}\nExperience: {experience}\nEducation: {education}\n\nGenerate a professional resume:"
    inputs = tokenizer.encode(input_text, return_tensors="pt")

    # Generate resume text
    output = model.generate(
        inputs, 
        max_length=500, 
        num_return_sequences=1, 
        no_repeat_ngram_size=2, 
        temperature=0.7
    )

    resume = tokenizer.decode(output[0], skip_special_tokens=True)
    return resume
