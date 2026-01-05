import re
import unicodedata
from src.config import ENTITY_MAPPING, ATTRIBUTE_MAPPING

class NLPProcessor:
    def __init__(self):
        # Danh sách từ loại bỏ (Stopwords)
        self.stopwords = [
            "là", "của", "tên", "chòm sao", "nào", "có", "ngôi sao",
            "hãy cho biết", "hỏi về", "được", "bởi", "bao nhiêu", "độ sáng"
        ]

    def _normalize_comparison(self, text):
        """
        Hàm phụ trợ: Chuẩn hóa text để so sánh (bỏ dấu, viết thường, thay _ bằng space, normalize dashes)
        """
        if text is None:
            return ""
        # Replace dashes/en-dashes/em-dashes với hyphen trước NFD
        text = text.replace("–", "-").replace("—", "-")
        # Bỏ dấu tiếng Việt
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower().strip().replace("_", " ")
        return text

    def normalize_text(self, text):
        text = text.lower().strip()
        # Giữ lại chữ, số, dấu chấm và dấu gạch chéo
        text = re.sub(r'[^\w\s\./]', '', text)
        return text
    
    def extract_value(self, text, intent_keys):
        text = text.lower()
        if any(i in ["Độ_sáng", "Cấp_sao"] for i in intent_keys):
            match = re.search(r'\d+(\.\d+)?', text)
            return match.group() if match else None
        
        # Priority: nếu có "là", extract từ phần sau "là" (dành cho attribute queries)
        if "là" in text:
            parts = text.split("là")
            # Try from the last part backwards, skip empty or question-only parts
            for i in range(len(parts) - 1, 0, -1):
                value = parts[i].strip().replace("?", "").replace("gì", "").strip()
                if value:
                    return value

        # Nếu không có "là", thử tìm entity
        found_entity = None
        longest_len = 0
        for key in ENTITY_MAPPING:
            if key in text:
                if len(key) > longest_len:
                    longest_len = len(key)
                    found_entity = ENTITY_MAPPING[key]
        if found_entity:
            return found_entity
        
        return text.strip()


    def extract_entity(self, text):
        """
        Bước 3 & 4: Xử lý từ đồng nghĩa và Lọc keyword quan trọng (Entity)
        Tìm xem trong câu hỏi có tên chòm sao hay ngôi sao nào không.
        """
        # Tìm tất cả entities khớp, theo thứ tự xuất hiện
        matches = []
        seen = set()
        for key, value in ENTITY_MAPPING.items():
            start = text.find(key)
            if start != -1 and value not in seen:
                matches.append((start, value))
                seen.add(value)
        
        # Sort by position
        matches.sort(key=lambda x: x[0])
        found_entities = [value for _, value in matches]

        return found_entities if found_entities else None

    def extract_intent(self, text):
        """
        Bước 3 & 4: Xử lý từ đồng nghĩa và Lọc keyword quan trọng (Intent/Attribute)
        Tìm xem người dùng muốn hỏi về thuộc tính mục tiêu gì (sao sáng nhất, cấp sao, v.v.)
        """
        # Dùng chiến thuật "Longest Match" (khớp chuỗi dài nhất trước)
        found_attr_key = []
        longest_len = 0
        matched_keywords = []
        
        # Tìm tất cả thuộc tính khớp, theo thứ tự xuất hiện
        matches = []
        for key, value in ATTRIBUTE_MAPPING.items():
            start = text.find(key)
            if start != -1:
                matches.append((start, value, key))
        
        # Sắp xếp
        matches.sort(key=lambda x: x[0])
        
        seen = set()
        for _, value, key in matches:
            if value in seen:
                # if len(value) > longest_len:
                #     longest_len = len(value)
                #     found_attr_key.append(value)
                #     matched_keywords.append(key)
                #     seen.add(value)
                continue
            else:
                found_attr_key.append(value)
                matched_keywords.append(key)
                seen.add(value)
        return found_attr_key, matched_keywords

    def remove_stopwords(self, text, intent_keywords=[]):
        """Hàm mới: Loại bỏ từ thừa để lấy giá trị tìm kiếm (VD: 2.01)"""
        # 1. Xóa keyword intent (ví dụ: xóa chữ "cấp sao", "độ sáng" nếu nó là intent)
        for intent in intent_keywords:
            text = text.replace(intent, "")
        
        # 2. Xóa stopwords thông thường
        words = text.split()
        # Lọc từ, giữ lại số liệu
        filtered = [w for w in words if w not in self.stopwords]
        return " ".join(filtered).strip()

    # Hàm xác định query (sau khi normalize) là so sánh hay không
    def is_comparison_query(self, text):
        comparison_keywords = ["lớn hơn", "nhỏ hơn", "cao hơn", "thấp hơn", "sớm hơn", 
                               "muộn hơn", "so với", "hơn", "kém", "xa hơn", "gần hơn",
                               "trước", "sau", "bằng", "lớn nhất", "nhỏ nhất", "cao nhất", "thấp nhất",
                               "sáng nhất", "mờ nhất", "gần nhất", "xa nhất", "sáng hơn", "mờ hơn", "tối hơn",
                               "sớm nhất", "muộn nhất", "tối nhất", "sớm hơn", "muộn hơn", "so sánh"]
        
        # Bỏ qua trường hợp "có sao sáng nhất" vì đây là một quan hệ, không phải so sánh
        explicit_exceptions = ["có sao nào sáng nhất", "có ngôi sao sáng nhất", "sao sáng nhất của", "có sao sáng nhất"]
        for keyword in comparison_keywords:
            if keyword in text:
                if not any(exc in text for exc in explicit_exceptions):
                    return True
        return False


    def process_query(self, query):
        flag = True if (("và" in query) or ("," in query)) else False
        normalized_text = self.normalize_text(query)
        comparison_check = self.is_comparison_query(normalized_text)
        entity_id = self.extract_entity(normalized_text)
        intent_key, matched_keywords = self.extract_intent(normalized_text)
        
        # Logic chuẩn bị text cho tìm kiếm ngược
        search_value_text = normalized_text
        # Dùng original query thay vì normalized để giữ lại "là" và dấu
        value = self.extract_value(query.lower(), intent_key)
        if not entity_id and intent_key:
            # Nếu không biết Entity, lọc sạch câu để lấy Value (VD: 2.01)
            search_value_text = self.remove_stopwords(normalized_text, matched_keywords)

        return {
            "original": query,
            "normalized": search_value_text,
            "value": value,  # Giá trị để tìm kiếm
            "entity_id": entity_id,
            "intent_key": intent_key,
            "original_intent": matched_keywords,
            "is_comparison": comparison_check,
            "has_n": flag
        }    
