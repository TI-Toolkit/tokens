from .parse import Token, Tokens


class TokenTrie:
    """
    Basic trie class for tokenizing text
    """
    
    def __init__(self, token: Token = None):
        self.token = token
        self.children = {}

    def insert(self, token: Token, lang: str = "en", *, mode: str = "all"):
        """
        Inserts some or all names of a token into the trie in a given language

        Three modes can be passed to specify which name(s) of the tokens to insert:
            - "display":      insert only the display name
            - "accessible":   insert only the accessible name
            - "all":          insert all names (display, accessible, and variants)

        :param token: The token to insert
        :param lang: The language to insert names from
        :param mode: Type(s) of names to insert (defaults to "all")
        """
        
        if lang not in token.langs:
            raise ValueError(f"lang {lang} not found")

        match mode.lower():
            case "display":
                names = [token.langs[lang].display]

            case "accessible":
                names = [token.langs[lang].accessible]

            case _:
                # Case "all", but can be any unrecognized arg
                names = token.langs[lang].names()

        for name in names:
            current = self
            for char in name:
                if char not in current.children:
                    current.children[char] = TokenTrie()

                current = current.children[char]

            current.token = token

    @staticmethod
    def from_tokens(tokens: Tokens, lang: str = "en", *, mode: str = "all"):
        """
        Inserts all tokens from a token container into the trie

        The lang and mode parameters match those used by a single insert.
        """
        
        if lang not in tokens.langs:
            raise ValueError(f"lang {lang} not found")

        root = TokenTrie()
        for token in tokens.bytes.values():
            root.insert(token, lang, mode=mode)

        return root

    def get_tokens(self, string: str) -> list[tuple[Token, str]]:
        """
        Finds all tokens which can be parsed from a given input string

        Each token is returned with the portion of the input string still remaining.
        Output is sorted by decreasing length of the consumed input.

        :return: A list of tuples each containing a token and its remaining input
        """
        
        tokens = []

        if string and string[0] in self.children:
            tokens += self.children[string[0]].get_tokens(string[1:])

        if self.token:
            tokens.append((self.token, string))

        return tokens

    def get_longest_token(self, string: str) -> tuple[Token, str]:
        """
        Finds the longest token which can be parsed from a given input string

        :return: A tuple of a token and the remaining input after parsing
        """
        
        return self.get_tokens(string)[0]
