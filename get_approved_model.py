import google.generativeai as genai

# Use your existing API Key configuration
genai.configure(api_key="AIzaSyCPqC4LGsVmimpg9rBDgwUTqaYY9kTa3bQ") 

print("Available models for your API Key:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        # We want to see the exact 'name' string
        print(f"-> {m.name}")

