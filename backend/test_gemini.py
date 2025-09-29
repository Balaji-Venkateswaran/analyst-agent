import google.generativeai as genai

# 🔑 Your real Gemini AI key
API_KEY = "AIzaSyAZuMj-TSl-mW6EXO1TD684aNVg61GxQwU"

# Configure Gemini client
genai.configure(api_key=API_KEY)


print(">>> Checking available models...")
for m in genai.list_models():
    print(m.name)


# Use flash model instead of pro
model = genai.GenerativeModel("gemini-2.5-flash") 
# Run a simple test
resp = model.generate_content("Hello Gemini Flash, say hi!")

print("✅ Gemini Response:", resp.text)
