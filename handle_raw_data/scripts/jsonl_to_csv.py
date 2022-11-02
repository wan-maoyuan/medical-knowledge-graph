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

        tmp = value.split(" ")
        self.value = "".join(tmp)

        self.entity_type = entity_type

    def equal(self, other) -> bool:
        if self.value != other.value:
            return False

        if self.entity_type != other.entity_type:
            return False

        return True


class Relation:
    def __init__(self, sub: Entity, obj: Entity, name: str):
        self.subjects = sub
        self.objects = obj
        self.relation_name = name

    def equal(self, other) -> bool:
        if not self.subjects.equal(other.subjects):
            return False

        if not self.objects.equal(other.objects):
            return False

        if self.relation_name != other.relation_name:
            return False

        return True


def handle_all_jsonl(jsonl_dir: str, csv_dir: str):
    for file in os.listdir(jsonl_dir):
        path = os.path.join(jsonl_dir, file)
        dict_list = read_jsonl_file(path)
        entity_list, relation_list = convert_dict_list_to_class(dict_list)

        entity_path = os.path.join(csv_dir, file[:-6] + "-entity.csv")
        entity_list = deduplication_entity_list(entity_list)
        save_entity_set_to_csv(entity_list, entity_path)

        relation_path = os.path.join(csv_dir, file[:-6] + "-relation.csv")
        relation_list = deduplication_relation_list(relation_list)
        save_relation_set_to_csv(relation_list, relation_path)


def read_jsonl_file(path: str) -> List[Dict]:
    dict_list = list()
    with open(path, 'r', encoding='utf-8')as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            json_data = json.loads(line)
            dict_list.append(json_data)

    return dict_list


def convert_dict_list_to_class(dict_list: List[Dict]) -> (List[Entity], List[Relation]):
    entity_list = list()
    relation_list = list()

    for dic in dict_list:
        text = dic['text']
        entities = dic['entities']
        if len(entities) == 0:
            continue

        for entity in entities:
            start = int(entity['start_offset'])
            end = int(entity['end_offset'])
            entity_list.append(
                Entity(int(entity['id']), text[start:end], entity['label'])
            )

        relations = dic['relations']
        for relation in relations:
            sub = get_entity_name_by_id(relation['to_id'], entity_list)
            obj = get_entity_name_by_id(relation['from_id'], entity_list)
            relation_list.append(
                Relation(sub, obj, relation['type'])
            )

    return entity_list, relation_list


def get_entity_name_by_id(entity_id: int, entity_list: List[Entity]) -> Entity:
    for entity in entity_list:
        if entity.entity_id == entity_id:
            return entity


def save_entity_set_to_csv(entity_list: List[Entity], save_path: str):
    entity_dict = dict()
    for en in entity_list:
        if en.entity_type not in entity_dict:
            entity_dict[en.entity_type] = list()
        entity_dict[en.entity_type].append(en.value)

    with open(save_path, 'w') as f:
        content = "entity_type,value\n"
        for entity_type in entity_dict:
            for value in entity_dict[entity_type]:
                content += entity_type + "," + value + "\n"
        f.write(content)


def save_relation_set_to_csv(relation_list: List[Relation], save_path: str):
    relation_dict = dict()
    for re in relation_list:
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


def deduplication_entity_list(entity_list: List[Entity]) -> List[Entity]:
    new_list = []
    if len(entity_list) == 0:
        return new_list

    new_list.append(entity_list[0])
    for old_index in range(1, len(entity_list)):
        flag = True
        for item in new_list:
            if entity_list[old_index].equal(item):
                flag = False
                break
        if flag:
            new_list.append(entity_list[old_index])

    return new_list


def deduplication_relation_list(relation_list: List[Relation]) -> List[Relation]:
    new_list = []
    if len(relation_list) == 0:
        return new_list

    new_list.append(relation_list[0])
    for old_index in range(1, len(relation_list)):
        flag = True
        for item in new_list:
            if relation_list[old_index].equal(item):
                flag = False
                break
        if flag:
            new_list.append(relation_list[old_index])

    return new_list


if __name__ == '__main__':
    handle_all_jsonl(JSONL_DIR, CSV_TABLE_DIR)
