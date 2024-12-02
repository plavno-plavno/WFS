import re

class SentenceAccumulator:
    def __init__(self):
        # Initialize an empty string to accumulate the sentence buffer
        self.sentence = ""
        # Define sentence-ending punctuation marks
        self.sentence_endings = r'[.!؟?]'  # Period, exclamation mark, question mark (including Arabic)

    def process_segment(self, text):
        """
        Accumulates text from each segment and returns completed sentences
        when sentence-ending punctuation is found. Remaining text is kept in
        the buffer for next iterations.

        Args:
            text (str): The input text segment to process.

        Returns:
            str or None: The completed sentence if found, otherwise None.
        """
        # Add the text from the current segment to the buffer
        self.sentence += text.strip() + " "

        # Find all occurrences of sentence-ending punctuation
        matches = list(re.finditer(self.sentence_endings, self.sentence))

        if matches:
            # Get the last occurrence of sentence-ending punctuation
            last_match = matches[-1]
            last_punct_pos = last_match.end()

            # Extract the completed sentence up to the last punctuation mark
            completed_sentence = self.sentence[:last_punct_pos].strip()

            # Keep the remaining text in the buffer for the next iteration
            self.sentence = self.sentence[last_punct_pos:].lstrip()

            return completed_sentence  # Return the completed sentence