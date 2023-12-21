import json
import xml.etree.ElementTree as ET


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


__all__ = ["to_json"]
