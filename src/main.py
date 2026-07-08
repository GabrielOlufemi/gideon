from openrouter import chat


response = chat( 
    messages = [{"role":"user", "content":"say hello"}],
    model= "google/gemini-2.5-flash"
)

print(response)