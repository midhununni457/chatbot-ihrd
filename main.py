import os
import re
from fuzzywuzzy import fuzz, process

def load_qa_pairs(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        pattern = r'Q: (.*?)\nA: (.*?)(?=\n\nQ:|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        qa_dict = {}
        for question, answer in matches:
            qa_dict[question.strip()] = answer.strip()
        
        return qa_dict
    except Exception:
        return {}

def find_best_match(user_query, questions, threshold=60):
    if not questions:
        return None
    
    try:
        best_match = process.extractOne(user_query, questions, scorer=fuzz.token_set_ratio)
        
        if best_match and best_match[1] >= threshold:
            return best_match[0]
        else:
            return None
    except Exception:
        return None

def chatbot_response(user_query, qa_dict):
    try:
        questions = list(qa_dict.keys())
        best_match = find_best_match(user_query, questions)
        
        if best_match:
            return qa_dict[best_match]
        else:
            return "I'm sorry, I couldn't find information related to your question. Could you please rephrase?"
    except Exception:
        return "I apologize, but I encountered an error while processing your request."

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load QA pairs from all files in the processed directory
    processed_dir = os.path.join(script_dir, "data", "processed")
    
    all_qa_pairs = {}
    for filename in os.listdir(processed_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(processed_dir, filename)
            qa_pairs = load_qa_pairs(file_path)
            all_qa_pairs.update(qa_pairs)
    
    print("IHRD Chatbot")
    print("Type 'exit' or 'quit' to end the conversation.")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        response = chatbot_response(user_input, all_qa_pairs)
        print(f"Bot: {response}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
