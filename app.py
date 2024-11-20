from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scrapper import QuestionDatabaseManager
from hugchat import hugchat
from hugchat.login import Login

class JEEPrepBotDB:
    def __init__(self, db_url: str = "sqlite:///questions.db"):
        """Initialize the bot with database connection."""
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db_manager = QuestionDatabaseManager(db_url)
        self.refresh_questions()  # Load questions at initialization

    def __init__(self, db_url: str = "sqlite:///questions.db", email: str = "arnabdeepnath@gmail.com", passwd: str = "21J@n2014"):
        """Initialize the bot with database connection and HugChat API."""
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db_manager = QuestionDatabaseManager(db_url)
        self.cookie_path_dir = "./cookies/"
        
        # Log in to HugChat
        self.login_hugchat(email, passwd)
        self.chatbot = hugchat.ChatBot(cookies=self.cookies.get_dict())
        
        self.refresh_questions()  # Load questions at initialization

    def login_hugchat(self, email: str, passwd: str):
        """Log in to HugChat and save cookies."""
        sign = Login(email, passwd)
        self.cookies = sign.login(cookie_dir_path=self.cookie_path_dir, save_cookies=True)

    def answer_question(self, query: str) -> str:
        """Generate response for student query using HugChat."""
        # First, check if a similar question exists in the database
        similar_question = self.find_similar_question(query)
        
        if similar_question:
            return self.solve_question_with_llm(similar_question, query)

        # If no similar question found, search the web using the LLM
        return self.search_web_with_llm(query)

    def find_similar_question(self, query: str):
        """Check for similar questions in the database."""
        # Implement logic to find a similar question
        similar_problems = self.find_similar_problems(query)
        return similar_problems[0]["problem"] if similar_problems else None

    def solve_question_with_llm(self, question: Dict, query: str) -> str:
        """Use the LLM to solve the given question."""
        llm_prompt = f"Question: {question['question']}\nOptions: {question['options']}\n" \
                     f"Can you provide a detailed solution to the question: {query}?"
        
        response = self.call_hugchat(llm_prompt)
        return response

    def search_web_with_llm(self, query: str) -> str:
        """Use the LLM to generate a web search result."""
        llm_prompt = f"I couldn't find a matching question in my database. Can you help me find an answer to this question: {query}?"
        
        response = self.call_hugchat(llm_prompt, web_search=True)
        return response

    def call_hugchat(self, prompt: str, web_search: bool = False) -> str:
        """Call HugChat with the provided prompt."""
        if web_search:
            message_result = self.chatbot.chat(prompt, web_search=True)
        else:
            message_result = self.chatbot.chat(prompt)
        
        # Wait until the response is done
        message_str = message_result.wait_until_done()
        
        # If web search is done, print sources
        if web_search:
            for source in message_result.web_search_sources:
                print(source.link)
                print(source.title)
        
        return message_str  # Return the response text
    def refresh_questions(self):
        """Refresh questions from the database."""
        self.questions = self.db_manager.get_all_questions()
        self.embeddings = np.array([q['embedding'] for q in self.questions])

        # Check the shape of embeddings
        # print(f"Embeddings shape before reshaping: {self.embeddings.shape}")  # Debugging line

        # Ensure that embeddings are 2D
        if self.embeddings.ndim == 1:  # If there's only one embedding, reshape it
            self.embeddings = self.embeddings.reshape(1, -1)
        elif self.embeddings.ndim > 2:  # If the embeddings are 3D, take the first slice
            self.embeddings = self.embeddings.reshape(self.embeddings.shape[0], -1)  # Reshape to 2D

        # Check the shape after processing
        # print(f"Embeddings shape after reshaping: {self.embeddings.shape}")  # Debugging line

    
    def find_similar_problems(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find similar problems based on the query."""
        # Encode the query
        query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        
        # Ensure query_embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)  # Reshape if 1D
        
        # Compute similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)

        # Ensure that similarities are in the correct format
        if similarities.ndim > 1:
            similarities = similarities.flatten()  # Flatten if needed

        top_indices = np.argsort(similarities)[-top_k:][::-1]
        similar_problems = []

        for idx in top_indices:
            question = self.questions[idx]
            similar_problems.append({
                "similarity": similarities[idx],
                "problem": {
                    "question": question['question'],
                    "topic": question['topic'],
                    "options": question['options'],
                    "solution_steps": self._generate_solution_steps(question)
                }
            })

        return similar_problems




    
    def add_sample_question(self):
        """Add a specific question to the database."""
        question_data = {
            "question": "A block P of mass m is placed on a horizontal frictionless plane...",
            "topic": "Friction and Oscillations",
            "correct_answer": "kA/2",
            "options": [
                {"text": "kA/2", "is_correct": True, "explanation": "Explanation for kA/2."},
                {"text": "kA", "is_correct": False, "explanation": None},
                {"text": "μ_s mg", "is_correct": False, "explanation": None},
                {"text": "zero", "is_correct": False, "explanation": None}
            ]
        }
        
        # Pass the data to the database manager for processing
        self.db_manager.add_question(question_data)

    def _generate_solution_steps(self, question: Dict) -> List[str]:
        """Generate solution steps from question data."""
        correct_option = next((opt for opt in question['options'] if opt['is_correct']), None)
        
        steps = [
            f"Topic: {question['topic']}",
            f"Question: {question['question']}",
            f"Correct Answer: {correct_option['text'] if correct_option else 'Not available'}",
        ]
        
        if correct_option and correct_option['explanation']:
            steps.append(f"Explanation: {correct_option['explanation']}")
        
        return steps
    
    def answer_question(self, query: str) -> str:
        """Generate response for student query."""
        similar_problems = self.find_similar_problems(query)
        
        if not similar_problems:
            return "I don't have any similar problems in my database yet."
        
        response = "Here's a similar problem I can help you with:\n\n"
        best_match = similar_problems[0]["problem"]
        
        response += f"Question: {best_match['question']}\nOptions:\n"
        for option in best_match['options']:
            marker = "✓" if option['is_correct'] else " "
            response += f"[{marker}] {option['text']}\n"
        
        response += "Solution Steps:\n"
        for i, step in enumerate(best_match['solution_steps'], 1):
            response += f"{i}. {step}\n"
        
        if len(similar_problems) > 1:
            response += "\nI also found other similar questions you might want to try:"
            for prob in similar_problems[1:]:
                response += f"\n- {prob['problem']['question']}"
        
        return response
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()

# Example usage
if __name__ == "__main__":
    bot = JEEPrepBotDB()
    # bot.add_sample_question()
    
    # Test the bot
    query = "What is the force between two blocks in oscillation?"
    response = bot.answer_question(query)
    print(response)
    
    # Close connections
    bot.close()



