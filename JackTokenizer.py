import string
from Shared import TOKEN_TYPE, jack_symbols, keyword_str_to_constant


class JackToken:
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value
        self.done = False

    def __str__(self):
        return f"Token({self.token_type}, {self.value})"


class JackTokenizer:
    """
    Ignores all comments and white space in the input stream and serializes it into Jack language tokens.
    The token types are specified according to Jack grammar.
    """

    def __init__(self, file):
        """Initialize the tokenizer with an input file.

        Args:
            file (TextIOWrapper): The input file to tokenize.
        """
        self.file = file
        # Initially there is no current token
        self.current_token = None
        self.next_token = None
        self.advance()

    # GENERAL
    def has_more_tokens(self):
        """Check if there are more tokens in the input.

        Returns:
            bool: True if there are more tokens to process, False otherwise.
        """
        return self.current_token is not None

    def advance(self):
        """Get the next token from the input and make it the current token.

        This method should only be called if has_more_tokens() returns True.
        """
        self.current_token = self.next_token
        self.next_token = None

        char = self.file.read(1)
        if not char:
            return

        # Loop to skip comments and whitespaces as long as we can
        while True:
            while char in string.whitespace:
                char = self.file.read(1)
                if not char:
                    return

            if char != "/":
                break

            previous_position = self.file.tell()
            previous_char = char
            char = self.file.read(1)
            if not char:
                return

            if char == "/":  # Line comment //
                while True:
                    char = self.file.read(1)
                    if not char:
                        return

                    if char == "\n":  # Seen \n
                        break
            elif char == "*":  # Block comment /* */
                # Skip until */
                while True:
                    char = self.file.read(1)
                    if not char:
                        return

                    if char == "*":

                        char = self.file.read(1)
                        if not char:
                            return

                        if char == "/":
                            char = self.file.read(1)
                            if not char:
                                return

                            break  # Seen */
            else:
                # We have to reverse looking ahead one character
                self.file.seek(previous_position)
                char = previous_char
                break

        # Look ahead one character
        if char in jack_symbols:
            self.current_token = JackToken(TOKEN_TYPE.SYMBOL, char)
            return

        # INT_CONST
        if char.isnumeric():
            value = char
            while True:
                current_position = self.file.tell()
                char = self.file.read(1)
                if not char or not char.isnumeric():
                    self.file.seek(current_position)
                    break
                value = value + char
            self.current_token = JackToken(TOKEN_TYPE.INT_CONST, value)
            return

        # STRING_CONST
        if char == "\"":
            value = ""
            char = self.file.read(1)
            while char and char != "\"":
                value = value + char
                char = self.file.read(1)
            if value:
                self.current_token = JackToken(TOKEN_TYPE.STRING_CONST, value)
            return

        value = char
        while True:
            current_position = self.file.tell()
            char = self.file.read(1)
            if not char or char in string.whitespace or char in jack_symbols:
                self.file.seek(current_position)
                break
            value = value + char
        if value in keyword_str_to_constant:
            # KEYWORD
            self.current_token = JackToken(TOKEN_TYPE.KEYWORD, value)
        else:  # IDENTIFIER
            if value:
                self.current_token = JackToken(TOKEN_TYPE.IDENTIFIER, value)
        return

    def token_type(self):
        """Get the type of the current token.

        Returns:
            TOKEN_TYPE: The type of the current token as a constant.
        """
        return self.current_token.token_type

    def key_word(self):
        """Get the keyword which is the current token.

        Should be called only when token_type() is TOKEN_TYPE.KEYWORD.

        Returns:
            KEYWORD: The keyword of the current token as a constant
        """
        return self.current_token.value

    def symbol(self):
        """Returns the character which is the curren token.

        Should be called only when token_type() is TOKEN_TYPE.SYMBOL.

        Returns:
            str: The character that is the current token
        """
        return self.current_token.value

    def identifier(self):
        """Returns the identifier which is the curren token.

        Should be called only when token_type() is TOKEN_TYPE.IDENTIFIER.

        Returns:
            str: The identifier which is the current token.
        """
        return self.current_token.value

    def int_const(self):
        """Returns the integer value of the current token

        Should be called only when token_type() is TOKEN_TYPE.INT_CONST.

        Returns:
            int: The integer value of the current token
        """
        return int(self.current_token.value)

    def string_const(self):
        """Returns the string value of the current token, without the two enclosing double quotes

        Should be called only when token_type() is TOKEN_TYPE.STRING_CONST.

        Returns:
            int: The string value of the current token, without the two enclosing double quotes
        """
        return self.current_token.value
