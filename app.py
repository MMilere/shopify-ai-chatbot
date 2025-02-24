import openai
from flask import Flask, request, jsonify
import os
import requests
import time
import threading

app = Flask(__name__)

# Nustatome API raktus iš aplinkos kintamųjų
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL = "https://guodzius-dobilaite.myshopify.com"

def chat_with_gpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Tu esi pagalbinis AI, kuris bendrauja lietuviškai."},
                      {"role": "user", "content": message}],
            api_key=OPENAI_API_KEY
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"OpenAI klaida: {str(e)}")
        return "Atsiprašome, įvyko klaida."

def check_new_messages():
    while True:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
            }
            response = requests.get(f"{SHOPIFY_STORE_URL}/admin/api/2023-01/conversations.json", headers=headers)
            
            if response.status_code == 200:
                conversations = response.json().get("conversations", [])
                for convo in conversations:
                    messages = convo.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if last_message.get("from", "") == "customer":
                            message_text = last_message.get("message", "")
                            convo_id = convo.get("id")
                            
                            ai_response = chat_with_gpt(message_text)
                            
                            message_data = {"message": ai_response}
                            response = requests.post(
                                f"{SHOPIFY_STORE_URL}/admin/api/2023-01/conversations/{convo_id}/messages.json",
                                json=message_data,
                                headers=headers
                            )
                            print(f"Atsakymas į {convo_id}: {ai_response}")
            else:
                print(f"Shopify API klaida: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Klaida tikrinant žinutes: {str(e)}")
        time.sleep(10)

# Paleidžiame atskirą giją, kuri tikrina Shopify Inbox kas 10 sek.
threading.Thread(target=check_new_messages, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
