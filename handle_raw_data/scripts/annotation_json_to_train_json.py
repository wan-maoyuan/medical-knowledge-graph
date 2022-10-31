import logging
import os
import json
from typing import *


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


ANNOTATION_JSON_DIR = os.path.join("..", "data", "annotation_json")
TRAIN_JSON_DIR = os.path.join("..", "data", "train_json")


class Entity:
    def __init__(self, entityId, value, entityType, start, end):
        self.entityId = entityId
        self.value = value
        self.entityType = entityType
        self.start = start
        self.end = end

    def to_dict(self) -> Dict:
        return {
            "id": self.entityId,
            "type": self.entityType,
            "value": self.value,
            "start": self.start,
            "end": self.end,
        }


class Relation:
    def __init__(self, sub: List[Entity], obj: List[Entity], name: str):
        self.subjects = sub
        self.objects = obj
        self.relation_name = name

    def to_dict(self) -> Dict:
        data = {
            "subjects": [],
            "objects": [],
            "relation_name": self.relation_name,
        }

        for sub in self.subjects:
            data['subjects'].append(sub.to_dict())

        for obj in self.objects:
            data['objects'].append(obj.to_dict())

        return data


class Sentence:
    def __init__(self, text: str, feature: str, entities: List[Entity], relations: List[Relation]):
        self.text = text
        self.feature = feature
        self.entities = entities
        self.relations = relations

    def to_dict(self) -> Dict:
        data = {
            "text": self.text,
            "feature": self.feature,
            "entities": [],
            "relations": [],
        }

        for item in self.entities:
            data['entities'].append(item.to_dict())

        for item in self.relations:
            data['relations'].append(item.to_dict())

        return data


def handle_all_annotation_json(annotation_dir: str, train_dir: str):
    for file in os.listdir(annotation_dir):
        path = os.path.join(annotation_dir, file)
        json_data = read_json_file(path)
        sentences = convert_json2class(json_data)
        save_path = os.path.join(train_dir, file)
        save_sentences2json(sentences, save_path)


def read_json_file(path: str) -> Dict:
    with open(path, 'r', encoding='utf_8_sig')as f:
        json_data = json.load(f)
        return json_data


def convert_json2class(json_data: Dict) -> List[Sentence]:
    sentenceList = list()

    examples = json_data.get("rasa_nlu_data").get("common_examples")
    for example in examples:
        text = example.get("text")
        feature = ""

        entities = list()
        entityDict = dict()
        for item in example.get("entities"):
            start = item.get("start")
            end = item.get("end")
            if item.get("value") == "特性":
                feature = text[start:end]
            else:
                id_str = item.get("value").split("-")[1]
                en = Entity(int(id_str), text[start:end], item.get("entity"), start, end)
                entities.append(en)
                entityDict[id_str] = en

        relations = list()
        intent = example.get("intent")
        if intent != "":
            sub = list()
            obj = list()
            l = intent.strip().split("->")
            s = l[0][1:-1].split(",")
            for i in s:
                sub.append(entityDict[i])

            o = l[1][1:-1].split(",")
            for i in o:
                obj.append(entityDict[i])
            name = l[2]
            relations.append(Relation(sub, obj, name))

        sentenceList.append(Sentence(text, feature, entities, relations))
    return sentenceList


def save_sentences2json(sentences: List[Sentence], save_path: str):
    data = {
        "sentence_list": []
    }

    for sentence in sentences:
        data['sentence_list'].append(sentence.to_dict())

    with open(save_path, "w", encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4, separators=(',', ':')))


if __name__ == '__main__':
    handle_all_annotation_json(ANNOTATION_JSON_DIR, TRAIN_JSON_DIR)

