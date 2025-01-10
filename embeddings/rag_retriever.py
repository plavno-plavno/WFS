import json
from typing import List,Dict
import os
from cerebras.cloud.sdk import Cerebras
import logging
from utils.decorators import timer_decorator

class RAGRetriever:

    def __init__(
            self,
        ):
        CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "csk-wdpk43pkx2n439jc9c8pf9wy5vrhtje6c8pyfcyvy9x3jnhc")
        self.client =Cerebras(api_key = CEREBRAS_API_KEY)
        self.model = "llama3.3-70b"

    @timer_decorator
    def retrieve_context(self, documents: List[Dict[str, str]], user_input: str) -> dict:
        """
        Generates a response to the user's question based on provided documents.

        Args:
            documents (List[Dict[str, str]]): A list of document dictionaries containing 'pageContent'.
            user_input (str): The user's question.

        Returns:
            str: The generated response extracted from the JSON response.
        """
        combined_text = "\n\n".join(doc['pageContent'] for doc in documents)

        context = f"""You are a book expert and librarian. Please respond to the user's question below using the provided context.

    **Important Rules:**
    1. If the context does not contain the close information use your knowledge about book asked, otherwise simply respond with "I don't know"
    2. Keep your answer concise, not less then 100 words, but not exceeding 200 words.
    3. Respond with JSON format only {{"response":"*response string here*"}}

    **CONTEXT:**
    {combined_text}

    **USER QUESTION:**
    {user_input}
    """

        messages = [
            {
                "role": "system",
                "content": context
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        try:
            completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.3,
                top_p=1.0  # Adjust if you want more randomness
            )
            response_content = completion.choices[0].message.content.strip()
            response_json = json.loads(response_content)
            return response_json
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response.")
            return "I'm sorry, but I couldn't process your request at this time."
        except Exception as e:
            logging.error(f"Chat completion failed: {e}")
            return "I'm sorry, but I couldn't process your request at this time."
