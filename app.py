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

def fetch_shopify_messages():
    graphql_query = {
        "query": """
        query {
            conversations(first: 10) {
                edges {
                    node {
                        id
                        messages(first: 5) {
                            edges {
                                node {
                                    id
                                    content
                                    from {
                                        __typename
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }
    
    response = requests.post(f"{SHOPIFY_STORE_URL}/admin/api/2023-01/graphql.json", json=graphql_query, headers=headers)
    return response.json()

def check_new_messages():
    while True:
        try:
            print("Tikrinamos naujos žinutės Shopify (GraphQL API)...")
            data = fetch_shopify_messages()
            conversations = data.get("data", {}).get("conversations", {}).get("edges", [])
            
            for convo in conversations:
                convo_id = convo.get("node", {}).get("id")
                messages = convo.get("node", {}).get("messages", {}).get("edges", [])
                
                if messages:
                    last_message = messages[-1]["node"]
                    message_text = last_message.get("content", "")
                    sender = last_message.get("from", {}).get("__typename", "")
                    
                    if sender == "Customer":
                        ai_response = chat_with_gpt(message_text)
                        send_shopify_reply(convo_id, ai_response)
                    else:
                        print("Paskutinė žinutė ne iš kliento, ignoruojama.")
        except Exception as e:
            print(f"Klaida tikrinant žinutes: {str(e)}")
        time.sleep(3)

def send_shopify_reply(conversation_id, message):
    graphql_mutation = {
        "query": """
        mutation sendMessage($conversationId: ID!, $content: String!) {
            conversationReply(conversationId: $conversationId, content: $content) {
                message {
                    id
                    content
                }
            }
        }
        """,
        "variables": {
            "conversationId": conversation_id,
            "content": message
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }
    
    response = requests.post(f"{SHOPIFY_STORE_URL}/admin/api/2023-01/graphql.json", json=graphql_mutation, headers=headers)
    print(f"Atsakymas išsiųstas į {conversation_id}: {message}")
    return response.json()

# Paleidžiame atskirą giją, kuri tikrina Shopify Inbox kas 3 sek.
threading.Thread(target=check_new_messages, daemon=True).start()

if __name__ == "__main__":
    print("AI Chatbot paleistas ir laukia Shopify žinučių (GraphQL API)...")
    app.run(host="0.0.0.0", port=5000)
