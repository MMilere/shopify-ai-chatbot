import openai
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Nustatome API raktus iš aplinkos kintamųjų
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

def chat_with_gpt(message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Tu esi pagalbinis AI, kuris bendrauja lietuviškai."},
                  {"role": "user", "content": message}],
        api_key=OPENAI_API_KEY
    )
    return response["choices"][0]["message"]["content"].strip()

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"error": "Nėra žinutės"}), 400

    ai_response = chat_with_gpt(user_message)
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
