import json
import re
import xml.etree.ElementTree as ET

from collections import defaultdict

from .parse import OsVersion, OsVersions


def validate(root: ET.Element):
    """
    Validates a token sheet, raising an error if an invalid component is found

    :param root: An XML element; call on the root element to validate the entire sheet
    """

    if root.tag != "tokens":
        raise ValueError("not a token sheet")

    all_tokens = set()
    all_names = {}

    current_lang, current_names = "", {}
    prev_version = current_version = None

    def visit(element: ET.Element, byte: str = ""):
        nonlocal current_lang, current_names
        nonlocal prev_version, current_version

        byte += element.attrib.get("value", "").lstrip("$")

        class ValidationError(ValueError):
            def __init__(self, message: str):
                super().__init__("token 0x" + byte + ": " + message if byte else "root: " + message)

        def attributes(**attrs: str):
            attrib = element.attrib.copy()

            for attr, regex in attrs.items():
                if attr not in attrib:
                    raise ValidationError(f"<{element.tag}> does not have attribute {attr}")

                if not re.fullmatch(regex, value := attrib.pop(attr)):
                    raise ValidationError(f"<{element.tag}> {attr} '{value}' does not match r'{regex}'")

            if attrib:
                raise ValidationError(f"<{element.tag}> has unexpected attribute {[*attrib.values()][0]}")

        def children(required: list[str], optional: list[str] = ()):
            options = {*required, *optional}
            tags = set()

            for child in element:
                if child.tag not in options:
                    raise ValidationError(f"<{child.tag}> is not a valid child of <{element.tag}>")

                tags.add(child.tag)
                visit(child, byte)

            if dif := {*required} - tags:
                raise ValidationError(f"missing required child <{dif.pop()}> of <{element.tag}>")

        def text(regex: str):
            if not re.fullmatch(regex, element.text):
                raise ValidationError(f"<{element.tag}> text '{element.text}' does not match r'{regex}'")

        match element.tag:
            case "tokens":
                children(["token"], ["two-byte"])

            case "two-byte":
                attributes(value=r"\$[0-9A-F]{2}")
                children(["token"])

            case "token":
                attributes(value=r"\$[0-9A-F]{2}")

                if byte in all_tokens:
                    raise ValidationError("token byte must be unique")

                all_tokens.add(byte)

                current_names = defaultdict(lambda s: defaultdict(set))
                children(["version"])

            case "version":
                current_names = defaultdict(set)

                prev_version, current_version = OsVersions.INITIAL, None
                children(["since", "lang"], ["until"])
                prev_version, current_version = current_version, None

                for lang in current_names:
                    if intersection := current_names[lang] & all_names[prev_version][lang]:
                        raise ValidationError(f"name '{intersection.pop()}' is not unique within {prev_version}")

                    all_names[prev_version][lang] |= current_names[lang]

            case "since":
                if current_version is not None:
                    raise ValidationError(f"<since> is not first child of <version>")

                if (current_version := OsVersion.from_element(element)) < prev_version:
                    raise ValidationError(f"version {current_version} overlaps with {prev_version}")

                prev_version = None
                children(["model", "os-version"])

                all_names[current_version] = all_names.get(current_version, defaultdict(set))

            case "until":
                if prev_version is not None:
                    raise ValidationError(f"<until> precedes <since> in <version>")

                children(["model", "os-version"])

            case "lang":
                attributes(code=r"[a-z]{2}", **{"ti-ascii": r"([0-9A-F]{2})+"})

                current_lang = element.attrib["code"]
                children(["display", "accessible"], ["variant"])

            case "display":
                text(r"[\S\s]+")

            case "accessible":
                text(r"[\u0000-\u00FF]*")
                current_names[current_lang].add(element.text)

            case "variant":
                text(r".+")
                current_names[current_lang].add(element.text)

            case "model":
                text(r"TI-\d\d.*")

            case "os-version":
                text(r"(\d+\.)+\d+")

            case _:
                raise ValidationError(f"unrecognized tag <{element.tag}>")

    visit(root)


def to_json(element: ET.Element):
    """
    Converts a token sheet to an equivalent JSON representation

    :param element: An XML element; call on the root element to convert the entire sheet
    :return: The element and all its descendants as JSON
    """

    match element.tag:
        case "tokens" | "two-byte":
            return {child.attrib["value"]: to_json(child) for child in element}

        case "token":
            return [to_json(child) for child in element]

        case "version":
            dct = {}
            langs = {}

            for child in element:
                if child.tag == "lang":
                    langs[child.attrib["code"]] = to_json(child)

                else:
                    dct[child.tag] = to_json(child)

            return dct | {"langs": langs}

        case "lang":
            dct = {"ti-ascii": element.attrib["ti-ascii"]}
            variants = []

            for child in element:
                if child.tag == "variant":
                    variants.append(child.text)

                else:
                    dct[child.tag] = child.text

            if variants:
                return dct | {"variants": variants}

            else:
                return dct

        case _:
            if list(element):
                return {child.tag: to_json(child) for child in element}

            else:
                return element.text


# with open("../8X.xml", encoding="UTF-8") as file:
#   json.dumps(to_json(ET.fromstring(file.read())), indent=2)


__all__ = ["to_json", "validate"]
