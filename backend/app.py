from flask import Flask, request, jsonify
import os
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

embed = GoogleGenerativeAIEmbeddings(google_api_key=API_KEY, model="models/embedding-001")

USER_DATA_FILE = "user_data.txt"
folder_name = "store"


@app.route('/update_user', methods=['POST'])
def update_user():
    try:
        # Get JSON data from request
        data = request.get_json()
        user_id = data["user_id"]
        if user_id is None:
            return jsonify({'error': 'user_id is required'}), 400
        user_folder = os.path.join(folder_name, user_id)
        # os.makedirs(user_folder, exist_ok=True)
        vector_store_path = os.path.join(user_folder)

        # Ensure required fields exist
        required_fields = ["user_id", "amount", "transaction_type", "category", "description"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        
        
        transaction_text = f"{data['amount']} {data['transaction_type']} {data['category']} {data['description']}"
        embedding = embed.embed_query(transaction_text)

        if not os.path.exists(vector_store_path):
            print("--------------------New Folder is there")
            vector_store = FAISS.from_texts(
                texts=[transaction_text], embedding=embed)
            vector_store.save_local(vector_store_path)
        else:
            print("--------------------here")
            vector_store = FAISS.load_local(
                vector_store_path, embeddings=embed, allow_dangerous_deserialization=True)
            vector_store.add_texts([transaction_text], embeddings=[embedding])
            vector_store.save_local(vector_store_path)

        # Append data to the text file
        with open(os.path.join( user_folder ,USER_DATA_FILE), "a") as f:
            f.write(str(data) + "\n")

        return jsonify({"message": "User data updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)
