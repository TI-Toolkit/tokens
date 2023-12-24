import json
import re
import xml.etree.ElementTree as ET

from collections import defaultdict

from .parse import OsVersion, OsVersions


def validate(element: ET.Element, byte: str = "", all_tokens: set[str] = None,
             all_accessible_names: dict[str, set[str]] = None, all_variant_names: dict[str, set[str]] = None):
    """
    Validates a token sheet

    :param element: An XML element; call on the root element to validate the entire sheet
    :param byte: The current token byte (should not be set directly)
    :param all_tokens: All previously seen tokens (should not be set directly)
    :param all_accessible_names: All previously seen accessible names per language (should not be set directly)
    :param all_variant_names: All previously seen variant names per language (should not be set directly)
    :return: Whether the element and all its descendants are valid components of the sheet
    """

    byte += element.attrib.get("value", "").lstrip("$")

    all_tokens = all_tokens or set()
    all_accessible_names = all_accessible_names or defaultdict(set)
    all_variant_names = all_variant_names or defaultdict(set)

    class ValidationError(ValueError):
        def __init__(self, message: str):
            super().__init__("token 0x" + byte + ": " + message if byte else "root: " + message)

    def attributes(el: ET.Element, **attribs: str):
        for attrib, regex in attribs.items():
            if attrib not in el.attrib:
                raise ValidationError(f"<{el.tag}> does not have attribute {attrib}")

            if not re.fullmatch(regex, value := el.attrib[attrib]):
                raise ValidationError(f"<{el.tag}> {attrib} '{value}' does not match r'{regex}'")

    def children(el: ET.Element, required: list[str], optional: list[str] = ()):
        options = {*required, *optional}
        tags = set()

        for child in el:
            if child.tag not in options:
                raise ValidationError(f"<{child.tag}> is not a valid child of <{el.tag}>")

            tags.add(child.tag)
            validate(child, byte, all_tokens, all_accessible_names, all_variant_names)

        if dif := {*required} - tags:
            raise ValidationError(f"missing required child <{dif.pop()}> of <{el.tag}>")

    def text(el: ET.Element, regex: str):
        if not re.fullmatch(regex, el.text):
            raise ValidationError(f"<{el.tag}> text '{el.text}' does not match r'{regex}'")

    match element.tag:
        case "tokens":
            children(element, ["token"], ["two-byte"])

        case "two-byte":
            attributes(element, value=r"\$[0-9A-F]{2}")
            children(element, ["token"])

        case "token":
            attributes(element, value=r"\$[0-9A-F]{2}")

            if byte in all_tokens:
                raise ValidationError("token byte must be unique")

            all_tokens.add(byte)

            accessible_names, variant_names = defaultdict(set), defaultdict(set)
            current_version = OsVersions.INITIAL

            for version in element:
                if version.tag != "version":
                    raise ValidationError(f"<{version.tag}> is not a valid child of <token>")

                tags = set()
                for grandchild in version:
                    match grandchild.tag:
                        case "since":
                            if (next_version := OsVersion.from_element(grandchild)) < current_version:
                                raise ValidationError(f"version {next_version} overlaps with {current_version}")

                            children(grandchild, ["model", "os-version"])

                        case "until":
                            current_version = OsVersion.from_element(grandchild)
                            children(grandchild, ["model", "os-version"])

                        case "lang":
                            attributes(grandchild, code=r"[a-z]{2}", **{"ti-ascii": r"([0-9A-F]{2})+"})
                            lang = grandchild.attrib["code"]

                            names = set()
                            for name in grandchild:
                                match name.tag:
                                    case "display":
                                        text(name, r"[\S\s]+")

                                    case "accessible":
                                        text(name, r"[\u0000-\u00FF]*")
                                        accessible_names[lang].add(name.text)

                                    case "variant":
                                        text(name, r".+")
                                        variant_names[lang].add(name.text)

                                    case _:
                                        ValidationError(f"unrecognized tag <{element.tag}>")

                                names.add(name.tag)

                            if dif := {"display", "accessible"} - names:
                                raise ValidationError(f"missing required child <{dif.pop()}> of <lang>")

                        case _:
                            ValidationError(f"unrecognized tag <{element.tag}>")

                    tags.add(grandchild.tag)

                if dif := {"since", "lang"} - tags:
                    raise ValidationError(f"missing required child <{dif.pop()}> of <version>")

            for lang in accessible_names:
                if intersection := accessible_names[lang] & all_accessible_names[lang]:
                    raise ValidationError(f"accessible name '{intersection.pop()}' is not unique")

                if intersection := variant_names[lang] & all_variant_names[lang]:
                    raise ValidationError(f"variant name '{intersection.pop()}' is not unique")

                all_accessible_names[lang] |= accessible_names[lang]
                all_variant_names[lang] |= variant_names[lang]

        case "model":
            text(element, r"TI-\d\d.*")

        case "os-version":
            text(element, r"(\d+\.)+\d+")

        case _:
            raise ValidationError(f"unrecognized tag <{element.tag}>")


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

with open("../8X.xml", encoding="UTF-8") as file:
    validate(ET.fromstring(file.read()))


__all__ = ["to_json", "validate"]
