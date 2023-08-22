from parse import Token, Tokens


class TokenTrie:
    def __init__(self, token: Token = None):
        self.token = token
        self.children = {}

    def insert(self, token: Token, lang: str = "en", *, mode: str = "all"):
        if lang not in token.langs:
            raise ValueError(f"lang {lang} not found")

        match mode.lower():
            case "display":
                names = [token.langs[lang].display]

            case "accessible":
                names = [token.langs[lang].accessible]

            case _:
                names = token.langs[lang].names()

        for name in names:
            current = self
            for char in name:
                if char not in current.children:
                    current.children[char] = TokenTrie()

                current = current.children[char]

            current.token = tokens.bytes[tokens.langs[lang][name]]

    @staticmethod
    def from_tokens(tokens: Tokens, lang: str = "en", *, mode: str = "all"):
        if lang not in tokens.langs:
            raise ValueError(f"lang {lang} not found")

        root = TokenTrie()
        for token in tokens.bytes.values():
            root.insert(token, lang, mode=mode)

        return root

    def get_tokens(self, string: str) -> list[tuple[Token, str]]:
        tokens = []

        if string:
            tokens += self.children[string[0]].get_tokens(string[1:])

        if self.token:
            tokens.append((self.token, string))

        return tokens

    def get_longest_token(self, string: str) -> tuple[Token, str]:
        return self.get_tokens(string)[0]
