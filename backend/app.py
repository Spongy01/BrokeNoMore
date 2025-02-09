from flask import Flask, request, jsonify
import os
from flask_cors import CORS

from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
from classify_questions import classify_question


app = Flask(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

embed = GoogleGenerativeAIEmbeddings(google_api_key=API_KEY, model="models/embedding-001")
genai.configure(api_key=API_KEY)

USER_DATA_FILE = "user_data.txt"
folder_name = "store"
CORS(app)

@app.route('/get_transactions', methods=['GET'])
def get_transactions():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        user_folder = os.path.join(folder_name, user_id)
        file_path = os.path.join(user_folder, USER_DATA_FILE)
        if not os.path.exists(file_path):
            return jsonify({'transactions': []})  # No transactions found
        transactions = []
        with open(file_path, "r") as f:
            for line in f:
                transactions.append(eval(line.strip()))  # Convert string to dictionary
        return jsonify({'transactions': transactions}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_user', methods=['POST'])
def update_user():
    try:
        print("Updating user...")
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
            # print("--------------------New Folder is there")
            vector_store = FAISS.from_texts(
                texts=[transaction_text], embedding=embed)
            vector_store.save_local(vector_store_path)
        else:
            # print("--------------------here")
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


# CORS(app)
@app.route('/query', methods=['POST'])
def query():
    try:
        print("Here inside main")
        data = request.get_json()
        user_id = data['user_id']
        if user_id is None:
            return jsonify({'error': 'user_id is required'}), 400

        conversation = data['conversation']
        if conversation is None:
            return jsonify({'error': 'question is required'}), 400
        
        system_message = {
            "role": "system",
            "content": (
                "You are a highly skilled financial advisor. You have expertise in explaining "
                "financial concepts clearly and concisely. Your role is to assist the user based "
                "on the context of the previous messages. Always make sure your responses are "
                "accurate, helpful, and based on the context of the conversation. "
                "Respond to the last user message considering the context provided above."
            )
        }
        messages = [system_message] + [{"role": message['role'], "content": message['content']} for message in conversation]

        #fetch the last question from the conversation
        question = messages[-1]['content']

        classification = classify_question(question).strip().lower()
        print("Classification : ", classification)

        if classification == "personal budgeting":
            # response = personal_budgeting(user_id, question)
            print("In Personal Budgeting")
            response = personal_budgeting(user_id, question)
        elif classification == "financial education":
            print("In Financial Education")
            response = financial_education(user_id, messages)
        else:
            print("In other")
            response = financial_education(user_id, messages)

        if response['status_code'] == 200:
            return jsonify({'message': 'Successful', 'response': response['message']}), 200
        else:
            return jsonify({'error': 'Failure'}), 500

    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


def financial_education(user_id, question):
    try:
        prompt = f"{question}"
        print("Setting up a model")
        print("Question : ", prompt)
        model = genai.GenerativeModel("gemini-1.5-flash-002")
        print('Model:', model)
        response = model.generate_content(prompt)

        if response and response.text:
            generated_text = response.text
            return {'question': question, 'message': generated_text, 'status_code': 200}
        else:
            return {'error': 'No response from the model', 'status_code': 500}

    except Exception as e:
        return {'error': f"An error occurred: {str(e)}", 'status_code': 500}

def personal_budgeting(user_id, question):
    # in this, after the prompt, add the data from pickle files and add a line saying sue the above data to answer the question if it is relevant and stuff.

    try:
        user_folder = os.path.join(folder_name, user_id)
        vector_store_path = user_folder
        vs = FAISS.load_local(str(vector_store_path),
                          embeddings=embed, allow_dangerous_deserialization=True)
        all_docs = vs.docstore._dict.values()
        if all_docs:
            all_docs_data = "\n".join([doc.page_content for doc in all_docs])
            print( "\n".join([doc.page_content for doc in all_docs]))
        else:
            print("No documents available in the database.")

        prompt = f"{question}"
        # add add_docs_data to the prompt
        prompt = prompt + "\n" + all_docs_data
        prompt = prompt + "\n" + "given the question, answer it based on the database provided and analyze that database and give answer. You can also add on information if you feel something is missing in the database, if there is nothing in the database related generate an appropriate generate response and do not explicitly state that there is nothing in the database in response."
        print("Setting up a model")
        print("Question : ", prompt)
        model = genai.GenerativeModel("gemini-1.5-flash-002")
        print('Model:', model)
        response = model.generate_content(prompt)

        if response and response.text:
            generated_text = response.text
            return {'question': question, 'message': generated_text, 'status_code': 200}
        else:
            return {'error': 'No response from the model', 'status_code': 500}

    except Exception as e:
        return {'error': f"An error occurred: {str(e)}", 'status_code': 500}

if __name__ == '__main__':
    app.run(debug=True)
