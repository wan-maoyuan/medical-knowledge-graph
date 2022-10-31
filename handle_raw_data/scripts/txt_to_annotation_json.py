import logging
import os
import json
from typing import *

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

SOURCE_TXT_DIR = os.path.join("..", "data", "txt")
SOURCE_ANNOTATION_JSON_DIR = os.path.join("..", "data", "annotation_json")


def convert_txt2json():
    for file in os.listdir(SOURCE_TXT_DIR):
        if file.endswith(".txt"):
            file_path = os.path.join(SOURCE_TXT_DIR, file)
            logging.info("fileName: %s, fileDir: %s" % (file, file_path))
            contentList = read_txt_content(file_path)
            dictData = convert_content2dict(contentList)
            save_path = os.path.join(SOURCE_ANNOTATION_JSON_DIR, file[:-4]+".json")
            save_dict2json(dictData, save_path)


def read_txt_content(path: str) -> List:
    lines = []
    with open(path, 'r', encoding='utf-8')as txt:
        for line in txt.readlines():
            line = line.removesuffix("\n")
            if line == "":
                continue
            lines.append(line)

    return lines


def convert_content2dict(content: List) -> Dict:
    examples = dict()
    examples['common_examples'] = []
    for line in content:
        examples['common_examples'].append({
            'text': line,
            'intent': '',
            'entities': []
        })
    data = dict()
    data['rasa_nlu_data'] = examples
    return data


def save_dict2json(data: Dict, save_path: str):
    with open(save_path, "w", encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4, separators=(',', ':')))


if __name__ == '__main__':
    convert_txt2json()
