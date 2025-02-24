import openai
from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Nustatome API raktus iš aplinkos kintamųjų
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL = "https://guodzius-dobilaite.myshopify.com"

def chat_with_gpt(message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Tu esi pagalbinis AI, kuris bendrauja lietuviškai."},
                  {"role": "user", "content": message}],
        api_key=OPENAI_API_KEY
    )
    return response["choices"][0]["message"]["content"].strip()

@app.route("/shopify/inbox", methods=["POST"])
def shopify_inbox():
    data = request.get_json()
    cart_id = data.get("id", "")
    customer = data.get("customer", {})
    customer_email = customer.get("email", "")
    
    if not cart_id or not customer_email:
        return jsonify({"error": "Trūksta duomenų"}), 400
    
    ai_response = chat_with_gpt(f"Klientas įsidėjo prekę į krepšelį #{cart_id}. Ar galiu padėti su papildoma informacija?")
    
    # Siųsti el. laišką klientui
    email_data = {
        "email": customer_email,
        "subject": "Jūsų pirkinių krepšelis",
        "body": ai_response
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }
    response = requests.post(
        f"{SHOPIFY_STORE_URL}/admin/api/2023-01/carts/{cart_id}/notes.json",
        json=email_data,
        headers=headers
    )
    
    return jsonify({"response": ai_response, "shopify_status": response.status_code})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
