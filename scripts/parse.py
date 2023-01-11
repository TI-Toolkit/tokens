import functools
import xml.etree.ElementTree as ET
from collections import namedtuple

# Models ordered such that models earlier in the list are earlier in the evolution of the token tables
MODEL_ORDER = {
    "TI-82": 10,

    "TI-83": 20,

    "TI-83+": 30,

    "TI-84+": 40,
    "TI-84+T": 40,
    "TI-82A": 40,

    "TI-84+CSE": 50,

    "TI-84+CE": 60,
    "TI-84+CET": 60,
    "TI-83+CE": 60,
    "TI-83+PCEEP": 60,
    "TI-84+PCEPY": 60,
    "TI-84+CETPE": 60,

    "latest": 9999999
}


@functools.total_ordering
class ModelVersion(namedtuple("ModelVersion", ["model", "version"])):
    __slots__ = ()

    def __lt__(self, other):
        order1 = MODEL_ORDER[self.model]
        order2 = MODEL_ORDER[other.model]

        if order1 < order2:
            return True
        elif order1 > order2:
            return False
        else:
            if self.version == "latest":
                return False
            elif other.version == "latest":
                return True
            else:
                return any(
                    map(lambda a: a[0] < a[1], zip(map(int, self.version.split(".")), map(int, other.version.split(".")))))

    def __eq__(self, other):
        return MODEL_ORDER[self.model] == MODEL_ORDER[other.model] and self.version == other.version

    @staticmethod
    def from_element(element) -> 'ModelVersion':
        model = ""
        version = ""

        for child in element:
            if child.tag == "model":
                model = child.text
            elif child.tag == "version":
                version = child.text
            else:
                raise ValueError("Unrecognized tag in " + element.name + ": " + child.name)

        if version == "":
            raise ValueError("<" + element.name + "> has a missing or empty <version> tag.")
        elif model == "":
            raise ValueError("<" + element.name + "> has a missing or empty <model> tag.")

        if model not in MODEL_ORDER or model == "latest":  # "latest" is for user convenience, not the sheet itself
            raise ValueError("Unrecognized <model>: " + model)

        if any([c != '.' and not c.isnumeric() for c in version]):
            raise ValueError(
                "Invalid <version> string \"" + version + "\", must be a sequence of numbers separated by periods.")

        return ModelVersion(model, version)


class Token:
    def __init__(self, bits: bytes, langs: dict[str, dict[str, bytes]], attrs: dict[str, str] = None,
                 since: ModelVersion = None,
                 until: ModelVersion = None) -> object:
        self.bits = bits
        self.langs = langs
        self.attrs = attrs
        self.since = since
        self.until = until

    def existed_at(self, model_version: ModelVersion):
        return ((self.since is None) or (self.since < model_version)) and ((self.until is None) or (self.until >= model_version))

    @staticmethod
    def from_element(element, bits):
        since = None
        until = None

        langs: dict[str, dict[str, bytes]] = {}

        for child in element:
            match child.tag:
                case "since":
                    if since is None:
                        since = ModelVersion.from_element(child)
                    else:
                        raise ValueError("Cannot have multiple <since> elements.")

                case "until":
                    if until is None:
                        until = ModelVersion.from_element(child)
                    else:
                        raise ValueError("Cannot have multiple <until> elements.")

                case "lang":
                    if "code" in child.attrib and len(child.attrib["code"]) == 2:
                        code = child.attrib["code"]

                        langs[code] = {}

                        for grandchild in child:
                            if grandchild.tag == "name":
                                langs[code][grandchild.text] = bits
                            else:
                                raise ValueError("Unrecognized tag in <lang>, only <name> is allowed.")
                    else:
                        raise ValueError("Missing or unrecognized localization code.")

        return Token(bits, langs, attrs=element.attrib, since=since, until=until)

class Tokens:
    def __init__(self, bytes, langs):
        self.bytes = bytes
        self.langs = langs

    @staticmethod
    def from_xml_string(xml_str: str):
        return Tokens.from_element(ET.fromstring(xml_str))

    @staticmethod
    def from_element(root, model_version=ModelVersion("latest", "")):
        if root.tag != "tokens":
            raise ValueError("Not a tokens xml.")

        all_bytes: dict[bytes, Token] = {}
        all_langs: dict[str, dict[str, bytes]] = {}

        def parse_page(element, bits=b""):
            nonlocal all_bytes
            nonlocal all_langs

            if element.tag == "token":
                token = Token.from_element(element, bits)

                if token.existed_at(model_version):
                    all_bytes[bits] = token
                    for lang, names in token.langs:
                        if lang not in all_langs:
                            all_langs[lang] = {}

                        for name in names:
                            all_langs[lang][name] = bits

            for child in element:
                if child.tag == "byte":
                    parse_page(child, bits + bytes.fromhex(child.attrib["value"][1:]))
                else:
                    parse_page(child, bits)

        parse_page(root)

        return Tokens(all_bytes, all_langs)
