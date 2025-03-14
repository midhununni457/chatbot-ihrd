import os
import re
from fuzzywuzzy import fuzz, process

def load_qa_pairs(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    pattern = r'Q: (.*?)\nA: (.*?)(?=\n\nQ:|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    qa_dict = {}
    for question, answer in matches:
        qa_dict[question.strip()] = answer.strip()
    
    return qa_dict

def find_best_match(user_query, questions, threshold=60):
    best_match = process.extractOne(user_query, questions, scorer=fuzz.token_set_ratio)
    
    if best_match and best_match[1] >= threshold:
        return best_match[0]
    return None

def chatbot_response(user_query, qa_dict):
    questions = list(qa_dict.keys())
    best_match = find_best_match(user_query, questions)
    
    if best_match:
        return qa_dict[best_match]
    else:
        return "I'm sorry, I couldn't find information related to your question. Could you please rephrase?"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    qa_file_path = os.path.join(script_dir, "data", "processed", "it_activities.txt")
    qa_pairs = load_qa_pairs(qa_file_path)
    
    print("IHRD Chatbot")
    print("Type 'exit' or 'quit' to end the conversation.")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        response = chatbot_response(user_input, qa_pairs)
        print(f"Bot: {response}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
