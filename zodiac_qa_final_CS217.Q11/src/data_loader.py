import json
import os
import ast
import unicodedata
from src.config import RELATIONS_PATH, CONCEPTS_PATH

class DataLoader:
    def __init__(self):
        self.relations = self._load_json(RELATIONS_PATH)
        self.concepts = self._load_json(CONCEPTS_PATH)

    def _normalize_comparison(self, text):
        """
        Hàm phụ trợ: Chuẩn hóa text để so sánh (bỏ dấu, viết thường, thay _ bằng space, normalize dashes)
        Ví dụ: "Con_Cừu_Vàng" -> "con cừu vàng"
        """
        if text is None:
            return ""
        # Replace dashes/en-dashes/em-dashes với hyphen trước NFD
        text = text.replace("–", "-").replace("—", "-")
        # Bỏ dấu tiếng Việt
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower().strip().replace("_", " ")
        return text

    def _load_json(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                return ast.literal_eval(content)
            except:
                return json.loads(content)

    def get_relation_value(self, subject_id, relation_type):
        results = []
        # Xử lý trường hợp subject_id là list
        if isinstance(subject_id, list):
            subject_id = subject_id[0] if subject_id else None
        
        if subject_id is None:
            return results
            
        if relation_type in self.relations:
            pairs = self.relations[relation_type]
            for item in pairs:
                if item[0].lower() == subject_id.lower():
                    results.append(item[1])
                elif item[1].lower() == subject_id.lower():
                    results.append(item[0])
        return results

    def get_vietnamese_name(self, concept_id):
        """Lấy tên Việt của một concept từ ID (ví dụ: Aries -> Bạch Dương)"""
        # Xử lý trường hợp concept_id là list
        if isinstance(concept_id, list):
            concept_id = concept_id[0] if concept_id else None
        
        if concept_id is None:
            return None
            
        details = self.get_concept_details(concept_id)
        if details and "Tên_Việt" in details:
            return details["Tên_Việt"]
        return concept_id  # Nếu không tìm được, trả về ID gốc
    
    # def get_source_from_target(self, target_id, relation_type):
    #     """
    #     Tìm Source (Chủ thể/Cha) khi biết Target (Giá trị/Con).
    #     Ví dụ: Biết 'Hamal' (Target), tìm 'Aries' (Source) trong quan hệ 'Có_sao_sáng_nhất'.
    #     """
    #     list = []
    #     if relation_type in self.relations:
    #         pairs = self.relations[relation_type]
    #         for item in pairs:
    #             # So sánh target_id với item[1]
    #             if item[1].lower() == target_id.lower():
    #                 list.append(item[0])
    #             elif item[0].lower() == target_id.lower():
    #                 list.append(item[1])
    #     return list

    def get_concept_attribute(self, concept_id, attribute_key):
        """Tìm thuộc tính trong file Concepts"""
        # Xử lý trường hợp concept_id là list
        if isinstance(concept_id, list):
            concept_id = concept_id[0] if concept_id else None
        
        if concept_id is None:
            return None
            
        # Duyệt qua các nhóm concept (Chòm sao, Ngôi sao, v.v.)
        for group in self.concepts.values():
            if concept_id in group:
                obj = group[concept_id]
                return obj.get(attribute_key)
        return None
        
    def get_concept_details(self, concept_id):
        """Lấy toàn bộ thông tin của một concept"""
        # Xử lý trường hợp concept_id là list
        if isinstance(concept_id, list):
            concept_id = concept_id[0] if concept_id else None
        
        if concept_id is None:
            return None
            
        for group in self.concepts.values():
            if concept_id in group:
                return group[concept_id]
        return None

    def find_concepts_by_attribute(self, attr_keys, value):
        """Tìm concepts dựa trên thuộc tính, attr_keys là list"""
        results = []
        value_lower = self._normalize_comparison(value)
        for group_name, group in self.concepts.items():
            for concept_id, attributes in group.items():
                for attr_key in attr_keys:
                    if attr_key in attributes:
                        attr_val = self._normalize_comparison(str(attributes[attr_key]))
                        if attr_val == value_lower or value_lower in attr_val or attr_val in value_lower:
                            if concept_id not in results:
                                results.append(concept_id)
        return results

    def find_concepts_by_relation_target(self, relation_keys, target_value):
        """Tìm concepts dựa trên quan hệ target, relation_keys là list"""
        results = []
        target_lower = str(target_value).lower().strip()
        for relation_key in relation_keys:
            if relation_key in self.relations:
                pairs = self.relations[relation_key]
                for source, target in pairs:
                    if str(target).lower().strip() == target_lower:
                        results.append(source)
        return results