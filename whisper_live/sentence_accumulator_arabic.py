import nltk
import re
from nltk.tokenize import PunktSentenceTokenizer

class SentenceAccumulatorArabic:
    def __init__(self):
        # Initialize an empty buffer to accumulate text
        self.buffer = ""

        # Ensure the required NLTK data is downloaded
        nltk.download('punkt', quiet=True)

        # Initialize and train the PunktSentenceTokenizer for Arabic
        self.tokenizer = PunktSentenceTokenizer()

    def process_segment(self, text):
        """
        Accumulates text from each segment and returns completed sentences
        when detected by the tokenizer. Remaining text is kept in the buffer.

        Args:
            text (str): The input Arabic text segment to process.

        Returns:
            list: A list of completed sentences detected in the input text.
        """
        # Add the text from the current segment to the buffer
        self.buffer += text.strip() + " "

        self.buffer = re.sub("؟", "?", self.buffer)

        # Tokenize the buffer into sentences
        delimiters = r'[.!؟?؛،]'  # Adding Arabic semicolon (؛) and Arabic comma (،)

        # Manually split text based on the additional delimiters
        sentences = re.split(delimiters, self.buffer)
        print('sen  ')
        print(sentences)


        # If more than one sentence is detected, process them
        if len(sentences) > 1:
            # All sentences except the last are complete
            completed_sentences = sentences[:-1]
            # The last sentence may be incomplete, keep it in the buffer
            self.buffer = sentences[-1]
            print(completed_sentences)
            return completed_sentences
        else:
            # No complete sentences yet
            return None