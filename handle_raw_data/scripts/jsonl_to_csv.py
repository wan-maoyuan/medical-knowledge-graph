import logging
import os
import json
from typing import *


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


JSONL_DIR = os.path.join("..", "data", "jsonl")
CSV_TABLE_DIR = os.path.join("..", "data", "csv_table")


class Entity:
    def __init__(self, entity_id: int, value: str, entity_type: str):
        self.entity_id = entity_id
        self.value = value
        self.entity_type = entity_type

    def __hash__(self):
        return hash(str(self.entity_id) + self.value + self.entity_type)

    def __eq__(self, other):
        if self.entity_id == other.entity_id and self.value == other.value and self.entity_type == other.entity_type:
            return True
        else:
            return False


class Relation:
    def __init__(self, sub: Entity, obj: Entity, name: str):
        self.subjects = sub
        self.objects = obj
        self.relation_name = name

    def __hash__(self):
        return hash(str(self.subjects.__hash__() + self.objects.__hash__()) + self.relation_name)

    def __eq__(self, other):
        if self.subjects == other.subjects and self.objects == other.objects and self.relation_name == other.relation_name:
            return True
        else:
            return False


def handle_all_jsonl(jsonl_dir: str, csv_dir: str):
    for file in os.listdir(jsonl_dir):
        path = os.path.join(jsonl_dir, file)
        dict_list = read_jsonl_file(path)
        entity_set, relation_set = convert_dict_list_to_class(dict_list)

        entity_path = os.path.join(csv_dir, file[:-6] + "-entity.csv")
        save_entity_set_to_csv(entity_set, entity_path)

        relation_path = os.path.join(csv_dir, file[:-6] + "-relation.csv")
        save_relation_set_to_csv(relation_set, relation_path)


def read_jsonl_file(path: str) -> List[Dict]:
    dict_list = list()
    with open(path, 'r', encoding='utf-8')as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            json_data = json.loads(line)
            dict_list.append(json_data)

    return dict_list


def convert_dict_list_to_class(dict_list: List[Dict]) -> (Set[Entity], Set[Relation]):
    entity_list = set()
    relation_list = set()

    for dic in dict_list:
        text = dic['text']
        entities = dic['entities']
        if len(entities) == 0:
            continue

        for entity in entities:
            start = int(entity['start_offset'])
            end = int(entity['end_offset'])
            entity_list.add(
                Entity(int(entity['id']), text[start:end], entity['label'])
            )

        relations = dic['relations']
        for relation in relations:
            sub = get_entity_name_by_id(relation['to_id'], entity_list)
            obj = get_entity_name_by_id(relation['from_id'], entity_list)
            relation_list.add(
                Relation(sub, obj, relation['type'])
            )

    return entity_list, relation_list


def get_entity_name_by_id(entity_id: int, entity_list: Set[Entity]) -> Entity:
    for entity in entity_list:
        if entity.entity_id == entity_id:
            return entity


def save_entity_set_to_csv(entity_set: Set[Entity], save_path: str):
    entity_dict = dict()
    for en in entity_set:
        if en.entity_type not in entity_dict:
            entity_dict[en.entity_type] = list()
        entity_dict[en.entity_type].append(en.value)

    with open(save_path, 'w') as f:
        content = "entity_type,value\n"
        for entity_type in entity_dict:
            for value in entity_dict[entity_type]:
                content += entity_type + "," + value + "\n"
        f.write(content)


def save_relation_set_to_csv(relation_set: Set[Relation], save_path: str):
    relation_dict = dict()
    for re in relation_set:
        if re.relation_name not in relation_dict:
            relation_dict[re.relation_name] = list()
        relation_dict[re.relation_name].append({
            "subject_type": re.subjects.entity_type,
            "subject": re.subjects.value,
            "object_type": re.objects.entity_type,
            "object": re.objects.value,
        })

    with open(save_path, 'w') as f:
        content = "relation_type,subject_type,subject,object_type,object\n"
        for relation_type in relation_dict:
            for item in relation_dict[relation_type]:
                content += relation_type + "," + item['subject_type'] + "," + item['subject'] + "," + item['object_type'] + "," + item['object'] + "\n"
        f.write(content)


if __name__ == '__main__':
    handle_all_jsonl(JSONL_DIR, CSV_TABLE_DIR)
