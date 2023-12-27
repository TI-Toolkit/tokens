import json
import xml.etree.ElementTree as ET

from .formats import *


with open("8X.xml", encoding="UTF-8") as infile:
    root = ET.fromstring(src := infile.read())

    with open("built/8X.xml", "w+", encoding="UTF-8") as outfile:
        validate(root)
        outfile.write(src)

    with open("built/8X.json", "w+", encoding="UTF-8") as outfile:
        json.dump(to_json(root), outfile, indent=2, ensure_ascii=False)
