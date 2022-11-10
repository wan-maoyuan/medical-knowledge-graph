import copy
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
    def __init__(self, sentence_id_list: List[str], entity_id: int, value: str, entity_type: str, desc: List[str]):
        self.sentence_id_list = sentence_id_list
        self.entity_id = entity_id

        tmp = value.split(" ")
        self.value = "".join(tmp)

        self.entity_type = entity_type
        self.entity_descriptions = desc

    def equal(self, other) -> bool:
        if self.value != other.value:
            return False

        if self.entity_type != other.entity_type:
            return False

        for i in other.sentence_id_list:
            self.sentence_id_list.append(i)

        for i in other.entity_descriptions:
            self.entity_descriptions.append(i)

        return True


class Relation:
    def __init__(self, sentence_id_list: List[str], sub: Entity, obj: Entity, name: str, desc: List[str]):
        self.sentence_id_list = sentence_id_list
        self.subjects = sub
        self.objects = obj
        self.relation_name = name
        self.relation_descriptions = desc

    def equal(self, other) -> bool:
        if not self.subjects == other.subjects:
            return False

        if not self.objects == other.objects:
            return False

        if self.relation_name != other.relation_name:
            return False

        for i in other.sentence_id_list:
            self.sentence_id_list.append(i)

        for i in other.relation_descriptions:
            self.relation_descriptions.append(i)

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

        entity_descriptions = []
        relation_descriptions = []
        for entity in entities:
            start = int(entity['start_offset'])
            end = int(entity['end_offset'])
            if entity['label'] == "实体描述":
                entity_descriptions.append(text[start:end])

            if entity['label'] == "关系描述":
                relation_descriptions.append(text[start:end])

        for entity in entities:
            start = int(entity['start_offset'])
            end = int(entity['end_offset'])

            if entity['label'] not in ["实体描述", "关系描述"]:
                entity_list.append(
                    Entity([str(dic['id'])], int(entity['id']), text[start:end], entity['label'], copy.deepcopy(entity_descriptions))
                )

        relations = dic['relations']
        for relation in relations:
            sub = get_entity_name_by_id(relation['to_id'], entity_list)
            obj = get_entity_name_by_id(relation['from_id'], entity_list)
            relation_list.append(
                Relation([str(dic['id'])], sub, obj, relation['type'], copy.deepcopy(relation_descriptions))
            )

    return entity_list, relation_list


def get_entity_name_by_id(entity_id: int, entity_list: List[Entity]) -> Entity:
    for entity in entity_list:
        if entity.entity_id == entity_id:
            return entity


def save_entity_set_to_csv(entity_list: List[Entity], save_path: str):
    entity_dict = dict()
    desc_max_len = 0
    for en in entity_list:
        if len(en.entity_descriptions) > desc_max_len:
            desc_max_len = len(en.entity_descriptions)

        if en.entity_type not in entity_dict:
            entity_dict[en.entity_type] = list()
        entity_dict[en.entity_type].append({
            "sentence_id": "-".join(en.sentence_id_list),
            "value": en.value,
            "descriptions": ",".join(en.entity_descriptions)
        })

    with open(save_path, 'w', encoding='utf-8') as f:
        content = "sentence_id,entity_type,value,"
        for i in range(desc_max_len):
            content += "description" + str(i) + ","
        content += "\n"

        for entity_type in entity_dict:
            for item in entity_dict[entity_type]:
                content += item['sentence_id'] + "," + entity_type + "," + item['value'] + "," + item['descriptions'] + "\n"
        f.write(content)


def save_relation_set_to_csv(relation_list: List[Relation], save_path: str):
    relation_dict = dict()
    desc_max_len = 0
    for re in relation_list:
        if re.subjects is None or re.objects is None:
            continue

        if len(re.relation_descriptions) > desc_max_len:
            desc_max_len = len(re.relation_descriptions)

        if re.relation_name not in relation_dict:
            relation_dict[re.relation_name] = list()
        relation_dict[re.relation_name].append({
            "sentence_id": "-".join(re.sentence_id_list),
            "subject_type": re.subjects.entity_type,
            "subject": re.subjects.value,
            "object_type": re.objects.entity_type,
            "object": re.objects.value,
            "descriptions": ",".join(re.relation_descriptions)
        })

    with open(save_path, 'w', encoding='utf-8') as f:
        content = "sentence_id,object_type,object,relation_type,subject_type,subject,"
        for i in range(desc_max_len):
            content += "description" + str(i) + ","
        content += "\n"

        for relation_type in relation_dict:
            for item in relation_dict[relation_type]:
                content += item['sentence_id'] + "," + item['object_type'] + "," + item['object'] + ","
                content += relation_type + "," + item['subject_type'] + "," + item['subject'] + ","
                content += item['descriptions'] + "\n"
        f.write(content)


def deduplication_entity_list(entity_list: List[Entity]) -> List[Entity]:
    new_list = []
    if len(entity_list) == 0:
        return new_list

    new_list.append(entity_list[0])
    for old_index in range(1, len(entity_list)):
        flag = True
        for item in new_list:
            if item.equal(entity_list[old_index]):
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
            if item.equal(relation_list[old_index]):
                flag = False
                break
        if flag:
            new_list.append(relation_list[old_index])

    return new_list


if __name__ == '__main__':
    handle_all_jsonl(JSONL_DIR, CSV_TABLE_DIR)
