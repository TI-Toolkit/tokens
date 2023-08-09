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
    "TI-83PCE": 60,
    "TI-83PCEEP": 60,
    "TI-84+CEPY": 60,
    "TI-84+CETPE": 60,
    "TI-82AEP": 60

    "latest": 9999999
}


@functools.total_ordering
class OsVersion(namedtuple("OsVersion", ["model", "version"])):
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
    def from_element(element) -> 'OsVersion':
        model = ""
        version = ""

        for child in element:
            if child.tag == "model":
                model = child.text
            elif child.tag == "os-version":
                version = child.text
            else:
                raise ValueError("Unrecognized tag in " + element.tag + ": " + child.tag)

        if version == "":
            raise ValueError("<" + element.tag + "> has a missing or empty <os-version> tag.")
        elif model == "":
            raise ValueError("<" + element.tag + "> has a missing or empty <model> tag.")

        if model not in MODEL_ORDER or model == "latest":  # "latest" is for user convenience, not the sheet itself
            raise ValueError("Unrecognized <model>: " + model)

        if any([c != '.' and not c.isnumeric() for c in version]):
            raise ValueError(
                "Invalid <version> string \"" + version + "\", must be a sequence of numbers separated by periods.")

        return OsVersion(model, version)


class Translation:
    def __init__(self, ti_ascii: bytes, display: str, accessible: str, variants: list[str]):
        self.ti_ascii = ti_ascii
        self.display = display
        self.accessible = accessible
        self.variants = variants

    def names(self) -> list[str]:
        return [self.display, self.accessible] + self.variants

    @staticmethod
    def from_element(element) -> (str, 'Translation'):
        code = element.attrib["code"]

        ti_ascii = bytes.fromhex(element.attrib["ti-ascii"])

        display = ""
        accessible = ""
        variants = []

        for child in element:
            match child.tag:
                case "display":
                    display = child.text
                case "accessible":
                    accessible = child.text
                case "variants":
                    variants.append(child.text)

        return code, Translation(ti_ascii, display, accessible, variants)


class Token:
    def __init__(self, bits: bytes, langs: dict[str, Translation], attrs: dict[str, str] = None,
                 since: OsVersion = None,
                 until: OsVersion = None):
        self.bits = bits
        self.langs = langs
        self.attrs = attrs
        self.since = since
        self.until = until

    @staticmethod
    def from_element(element, bits, version=OsVersion("latest", "")):
        since = None
        until = None

        langs: dict[str, Translation] = {}

        done = False
        for version_elem in element:
            for child in version_elem:
                match child.tag:
                    case "since":
                        version_since = OsVersion.from_element(child)
                        if since is None:
                            since = version_since

                        if since > version:
                            done = True

                    case "until":
                        version_until = OsVersion.from_element(child)
                        if until is None or until > version_until:
                            until = version_until

                    case "lang":
                        if not done:
                            code, translation = Translation.from_element(child)
                            langs[code] = translation
        return Token(bits, langs, attrs=element.attrib, since=since, until=until)

class Tokens:
    def __init__(self, bytes, langs):
        self.bytes = bytes
        self.langs = langs

    @staticmethod
    def from_xml_string(xml_str: str, version=OsVersion("latest", "")):
        return Tokens.from_element(ET.fromstring(xml_str), version=version)

    @staticmethod
    def from_element(root, version=OsVersion("latest", "")):
        if root.tag != "tokens":
            raise ValueError("Not a tokens xml.")

        all_bytes: dict[bytes, Token] = {}
        all_langs: dict[str, dict[str, bytes]] = {}

        def parse_page(element, bits=b""):
            nonlocal all_bytes
            nonlocal all_langs

            if element.tag == "token":
                token = Token.from_element(element, bits, version=version)

                all_bytes[bits] = token
                for lang, translation in token.langs.items():
                    if lang not in all_langs:
                        all_langs[lang] = {}

                    for name in translation.names():
                        all_langs[lang][name] = bits

            for child in element:
                if child.tag == "two-byte":
                    parse_page(child, bits=bits + bytes.fromhex(child.attrib["value"][1:]))
                else:
                    parse_page(child, bits=bits)

        parse_page(root)

        return Tokens(all_bytes, all_langs)


# with open("../8X.xml", encoding="UTF-8") as file:
#   Tokens.from_xml_string(file.read())
