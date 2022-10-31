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
CSV_TABLE_DIR = os.path.join("..", "data", "csv_table")


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


def handle_all_annotation_json(annotation_dir: str, csv_dir: str):
    for file in os.listdir(annotation_dir):
        path = os.path.join(annotation_dir, file)
        json_data = read_json_file(path)
        sentences = convert_json_to_class(json_data)

        entity_path = os.path.join(csv_dir, file[:-5] + "-entity.csv")
        save_sentences_to_entity_csv(sentences, entity_path)

        relation_path = os.path.join(csv_dir, file[:-5] + "-relation.csv")
        save_sentences_to_relation_csv(sentences, relation_path)


def read_json_file(path: str) -> Dict:
    with open(path, 'r', encoding='utf_8_sig')as f:
        json_data = json.load(f)
        return json_data


def convert_json_to_class(json_data: Dict) -> List[Sentence]:
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


def save_sentences_to_entity_csv(sentences: List[Sentence], entity_path: str):
    all_kind_entity = dict()
    for sentence in sentences:
        for en in sentence.entities:
            if en.entityType not in all_kind_entity:
                all_kind_entity[en.entityType] = set()
            all_kind_entity[en.entityType].add(en.value)

    max_count = 1
    for key in all_kind_entity:
        if max_count < len(all_kind_entity[key]):
            max_count = len(all_kind_entity[key])

    type_list = []
    for key in all_kind_entity:
        info = [key]
        for item in all_kind_entity[key]:
            info.append(item)
        for i in range(max_count-len(info)):
            info.append("")
        type_list.append(info)

    with open(entity_path, 'w')as en:
        content = ""
        for y in range(len(type_list)):
            content += type_list[y][0] + ","
        content += "\n"

        for x in range(1, max_count):
            for y in range(len(type_list)):
                content += type_list[y][x] + ","
            content += "\n"

        en.write(content)


def save_sentences_to_relation_csv(sentences: List[Sentence], relation_path: str):
    relation_list = []

    for sentence in sentences:
        for relation in sentence.relations:
            for sub in relation.subjects:
                for obj in relation.objects:
                    relation_list.append(
                        "{},{},{},{},{}".format(
                            relation.relation_name, sub.entityType, sub.value, obj.entityType, obj.value
                        )
                    )

    with open(relation_path, 'w')as rela:
        content = "关系名称,主体类型,主体名称,客体类型,客体名称\n"
        for item in relation_list:
            content += item + "\n"

        rela.write(content)


if __name__ == '__main__':
    handle_all_annotation_json(ANNOTATION_JSON_DIR, CSV_TABLE_DIR)


