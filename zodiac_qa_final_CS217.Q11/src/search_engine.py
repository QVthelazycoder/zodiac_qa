# src/search_engine.py
from src.data_loader import DataLoader
from src.nlp_processor import NLPProcessor
import unicodedata
import re

class SearchEngine:
    def __init__(self):
        self.data_loader = DataLoader()
        self.nlp = NLPProcessor()

    def _normalize_comparison(self, text):
        """Chuẩn hóa text để so sánh (bỏ dấu, viết thường, thay ký tự đặc biệt)"""
        if not text:
            return ""
        # Chuyển unicode về dạng cơ bản và loại bỏ dấu
        text = unicodedata.normalize('NFD', str(text)).encode('ascii', 'ignore').decode('ascii')
        text = text.lower().strip().replace("_", " ")
        # Thay thế các loại dấu gạch ngang
        for dash in ["–", "—"]:
            text = text.replace(dash, "-")
        return text

    def search_entity_by_value(self, intent_keys, search_value):
        """Tìm Entity ID dựa trên giá trị thuộc tính hoặc quan hệ"""
        search_value = self._normalize_comparison(search_value)
        found_entities = set()
        
        for intent in intent_keys:
            # 1. Tìm trong bảng quan hệ (Relations)
            if intent in self.data_loader.relations:
                for item in self.data_loader.relations[intent]:
                    target_val = self._normalize_comparison(item[1])
                    if target_val in search_value or search_value in target_val: 
                        found_entities.add(item[0])
            # 2. Tìm trong thuộc tính Concepts
            for group_data in self.data_loader.concepts.values():
                for entity_id, attributes in group_data.items():
                    if intent in attributes:
                        attr_val = self._normalize_comparison(attributes[intent])
                        if attr_val in search_value or search_value in attr_val:
                            found_entities.add(entity_id)
                print(found_entities)

        return list(found_entities)

    def _handle_known_entity(self, entities, intent_keys, has_n):
        """Xử lý trường hợp đã xác định được Entity ID từ câu hỏi"""
        vals = []
        entities_list = entities if isinstance(entities, list) else [entities]

        # Trường hợp chỉ có một entity nhưng có nhiều intent, áp dụng lần lượt intent          
        if len(entities_list) < len(intent_keys) and len(entities_list) == 1:
            entity = entities_list[0]
                    
            if has_n:
                for intent in intent_keys:
                    val = self.data_loader.get_relation_value(entity, intent)
                    if not val:
                        val = self.data_loader.get_concept_attribute(entity, intent)
                    if val:
                        if isinstance(val, list):
                            vals.append(", ".join(str(v) for v in val))
                        else:
                            vals.append(str(val))
                    else:
                        vals.append("Không tìm thấy thông tin")

            else:
                for intent in intent_keys:
                    val = self.data_loader.get_relation_value(entity, intent)
                    if not val:
                        val = self.data_loader.get_concept_attribute(entity, intent)
                    
                    if val:
                        if not isinstance(val, list):
                            entity = val
                        else:
                            if len(val) > 0: 
                                entity = val[0]
                            else: 
                                entity = "Không tìm thấy thông tin." 
                    else:
                        entity = "Không tìm thấy thông tin"
                vals.append(str(entity))

        # Trường hợp chỉ có một intent nhưng có thể có nhiều entity, áp dụng intent cho tất cả entity    
        else:
            for entity in entities_list:
                for intent in intent_keys:
                    val = self.data_loader.get_relation_value(entity, intent)
                    if not val:
                        val = self.data_loader.get_concept_attribute(entity, intent)
                    
                    if val:
                        if isinstance(val, list):
                            vals.append(", ".join(str(v) for v in val))
                        else:
                            vals.append(str(val))
        
        if vals:
            return ", ".join(vals)
        
        return f"Tôi biết {', '.join(str(e) for e in entities_list)} nhưng không tìm thấy thông tin '{', '.join(intent_keys)}'."

    def _handle_unknown_entity(self, nlp_result):
        """Xử lý trường hợp không có Entity ID, phải tìm dựa trên mô tả/giá trị"""
        intent_keys = nlp_result.get('intent_key', [])
        clean_text = nlp_result.get('normalized', '')
        value = nlp_result.get("value", clean_text)

        # Phân loại Intent: Cái nào dùng để tìm (finding) => trung gian, cái nào dùng để lấy dữ liệu (querying) => mục tiêu
        finding_intents = []
        querying_intents = []

        for intent in intent_keys:
            if self.data_loader.find_concepts_by_attribute([intent], value) or \
               self.data_loader.find_concepts_by_relation_target([intent], value):
                finding_intents.append(intent)
            else:
                querying_intents.append(intent)

        # Fallback: Nếu không phân loại được, mặc định intent đầu là finding
        if not finding_intents and intent_keys:
            finding_intents = intent_keys[:1]
            querying_intents = intent_keys[1:]

        # Tìm thực thể phù hợp
        found_ids = self.search_entity_by_value(finding_intents, value)
        if not found_ids:
            # Thử tìm bằng phương thức tìm kiếm chính xác hơn từ data_loader
            found_ids = self.data_loader.find_concepts_by_attribute(finding_intents, value) or \
                        self.data_loader.find_concepts_by_relation_target(finding_intents, value)

            if not found_ids:
                # orig_intent = ", ".join(nlp_result.get('original_intent', []))
                return "Không tìm thấy kết quả."

        # Trả về kết quả: Nếu có intent truy vấn thì lấy giá trị, ngược lại trả về tên thực thể
        if querying_intents:
            main_query_intent = querying_intents[-1]
            results = []
            for fid in found_ids:
                # Xử lý trường hợp fid là list
                if isinstance(fid, list):
                    fid = fid[0] if fid else None
                
                if fid is None:
                    continue
                    
                val = self.data_loader.get_relation_value(fid, main_query_intent) or \
                      self.data_loader.get_concept_attribute(fid, main_query_intent)
                if val:
                    if isinstance(val, list):
                        results.append(", ".join(str(v) for v in val))
                    else:
                        results.append(str(val))
            if results: return ", ".join(results)

        # Mặc định trả về tên Việt của các Entity tìm thấy
        names = []
        for fid in found_ids:
            # Xử lý trường hợp fid là list
            if isinstance(fid, list):
                fid = fid[0] if fid else None
            
            if fid is None:
                continue
                
            # vn_name = self.data_loader.get_concept_attribute(fid, "Tên_Việt")
            # names.append(f"{vn_name} ({fid})" if vn_name else fid)
            names.append(str(fid))
        
        return ", ".join(names)
    
    # Hàm so sánh các thuộc tính có kiểu giá trị số và ngày tháng
    def compare_numeric_n_date_attributes(self, attr_key, value1, value2):
        numeric_attrs = ["Độ_sáng", "Cấp_sao", "Khoảng_cách", "Kích_thước"]
        date_attrs = ["Thời_gian_mặt_trời_bắt_đầu", "Thời_gian_mặt_trời_kết_thúc", "Thời_gian_sinh_bắt_đầu", 
                      "Thời_gian_sinh_kết_thúc"]
        date_range_attrs = ["Thời_gian_mặt_trời_đi_qua", "Thời_gian_sinh"]

        # So sánh giá trị số
        if attr_key in numeric_attrs:
            try:
                num1 = float(value1)
                num2 = float(value2)
                if num1 < num2:
                    return -1
                elif num1 > num2:
                    return 1
                else:
                    return 0
            except ValueError:
                pass  # Nếu không chuyển đổi được, bỏ qua so sánh số

        # So sánh giá trị ngày tháng
        elif attr_key in date_attrs:
            # Giả sử định dạng ngày là "DD/MM" hoặc "DD-MM"
            def parse_date(date_str):
                match = re.match(r'(\d{1,2})[/-](\d{1,2})', date_str)
                if match:
                    day, month = int(match.group(1)), int(match.group(2))
                    return (month, day)  # So sánh theo tháng trước, sau đó ngày
                return None

            date1 = parse_date(value1)
            date2 = parse_date(value2)
            if date1 and date2:
                if date1 < date2:
                    return -1
                elif date1 > date2:
                    return 1
                else:
                    return 0
                
        # So sánh giá trị khoảng ngày tháng
        elif attr_key in date_range_attrs:
            # Giả sử định dạng khoảng ngày là "DD/MM - DD/MM" hoặc "DD-MM - DD-MM"
            def parse_date_range(range_str):
                parts = re.split(r'\s*-\s*', range_str)
                if len(parts) == 2:
                    start = parse_date(parts[0])
                    end = parse_date(parts[1])
                    return (start, end)
                return None

            range1 = parse_date_range(value1)
            range2 = parse_date_range(value2)
            if range1 and range2:
                # So sánh theo ngày bắt đầu
                if range1[0] < range2[0]:
                    return -1
                elif range1[0] > range2[0]:
                    return 1
                else:
                    # Nếu ngày bắt đầu bằng nhau, so sánh ngày kết thúc
                    if range1[1] < range2[1]:
                        return -1
                    elif range1[1] > range2[1]:
                        return 1
                    else:
                        return 0
        return None  # Không thể so sánh
    
    # Hàm trả lời câu hỏi so sánh
    def _handle_comparison_query(self, nlp_result):
        """Xử lý các câu hỏi so sánh dựa trên danh sách thực thể và thuộc tính tìm được"""
        entity_ids = nlp_result.get('entity_id', [])
        intent_keys = nlp_result.get('intent_key', [])
        
        if len(entity_ids) < 2:
            return "Tôi cần ít nhất hai đối tượng để thực hiện so sánh."
        
        if not intent_keys:
            return "Tôi không xác định được thuộc tính cần so sánh."
        
        # Lấy thuộc tính cuối cùng được nhắc đến để so sánh (VD: Cấp_sao hoặc Thời_gian_sinh_bắt_đầu)
        attr_key = intent_keys[-1]
        
        # Thu thập giá trị thực tế của các thực thể
        entity_values = {}
        for eid in entity_ids:
            # Xử lý trường hợp eid là list
            if isinstance(eid, list):
                eid = eid[0] if eid else None
            
            if eid is None:
                continue
                
            # Ưu tiên lấy trực tiếp từ concept hoặc thông qua quan hệ nếu cần
            val = self.data_loader.get_concept_attribute(eid, attr_key)
            if val is not None:
                entity_values[eid] = val
        
        if len(entity_values) < 2:
            return "Tôi không tìm thấy đủ dữ liệu để thực hiện so sánh giữa các đối tượng này."

        # Logic so sánh cho từng loại dữ liệu
        is_brightness = (attr_key == "Độ_sáng") or (attr_key == "Cấp_sao")
        is_distance = (attr_key == "Khoảng_cách")
        is_date_start = attr_key in ["Thời_gian_mặt_trời_bắt_đầu", "Thời_gian_sinh_bắt_đầu"]
        is_date_end = attr_key in ["Thời_gian_mặt_trời_kết_thúc", "Thời_gian_sinh_kết_thúc"]

        if is_brightness:
            # Cấp sao càng nhỏ càng sáng
            sorted_items = sorted(entity_values.items(), key=lambda x: float(x[1]))
            winner = sorted_items[0]
            others = sorted_items[1:]
            
            if len(entity_ids) == 2:
                return f"{winner[0]} ({winner[1]}) sáng hơn {others[0][0]} ({others[0][1]})"
            
            res_str = f"{winner[0]} sáng nhất ({winner[1]})"
            res_str += ", tiếp đến là " + ", ".join([f"{e[0]} ({e[1]})" for e in others])
            return res_str
        
        elif is_distance:
            # Khoảng cách càng nhỏ càng gần
            sorted_items = sorted(entity_values.items(), key=lambda x: float(x[1]))
            winner = sorted_items[0]
            others = sorted_items[1:]
            
            if len(entity_ids) == 2:
                return f"{winner[0]} ({winner[1]} năm ánh sáng) gần hơn {others[0][0]} ({others[0][1]} năm ánh sáng)"
            
            res_str = f"{winner[0]} gần nhất ({winner[1]} năm ánh sáng)"
            res_str += ", tiếp đến là " + ", ".join([f"{e[0]} ({e[1]} năm ánh sáng)" for e in others])
            return res_str

        elif is_date_start:
            def to_date_start_score(date_str):
                # Chuyển "21/03" -> 321 để so sánh
                m = re.search(r'(\d{1,2})/(\d{1,2})', str(date_str))
                return int(m.group(2)) * 100 + int(m.group(1)) if m else 9999

            sorted_items = sorted(entity_values.items(), key=lambda x: to_date_start_score(x[1]))
            winner = sorted_items[0]
            
            if len(entity_ids) == 2:
                other = sorted_items[1]
                if attr_key == "Thời_gian_sinh_bắt_đầu":
                    return f"{winner[0]} ({winner[1]}) có ngày sinh bắt đầu sớm hơn {other[0]} ({other[1]})"
                else:
                    return f"Mặt trời bắt đầu đi qua {winner[0]} ({winner[1]}) sớm hơn {other[0]} ({other[1]})"

            return f"{winner[0]} ({winner[1]}) bắt đầu sớm nhất."
        
        elif is_date_end:
            def to_date_end_score(date_str):
                # Chuyển "21/03" -> 321 để so sánh
                m = re.search(r'(\d{1,2})/(\d{1,2})', str(date_str))
                return int(m.group(2)) * 100 + int(m.group(1)) if m else 0

            sorted_items = sorted(entity_values.items(), key=lambda x: to_date_end_score(x[1]), reverse=True)
            winner = sorted_items[0]
            
            if len(entity_ids) == 2:
                other = sorted_items[1]
                if attr_key == "Thời_gian_sinh_kết_thúc":
                    return f"{winner[0]} ({winner[1]}) có ngày sinh kết thúc muộn hơn {other[0]} ({other[1]})"
                else:
                    return f"Mặt trời kết thúc việc đi qua {winner[0]} ({winner[1]}) muộn hơn {other[0]} ({other[1]})"

            return f"{winner[0]} ({winner[1]}) kết thúc muộn nhất."

        return "Hiện tại tôi chưa hỗ trợ so sánh loại thuộc tính này."

    def answer(self, query):
        """Điểm điều hướng chính của công cụ tìm kiếm"""
        nlp_result = self.nlp.process_query(query)
        entity_id = nlp_result.get('entity_id')
        intent_key = nlp_result.get('intent_key')
        has_n = nlp_result.get('has_n')

        # Luồng 1: Biết rõ thực thể (Ví dụ: "Aries có ngôi sao sáng nhất là sao nào?")
        if entity_id and intent_key:
            # Nếu có yêu cầu so sánh, chuyển sang luồng so sánh
            if nlp_result.get('is_comparison') and len(entity_id) >= 2:
                if intent_key[-1] == "Khoảng_cách":
                    output = self._handle_comparison_query(nlp_result)
                    return output
                return self._handle_comparison_query(nlp_result)
            
            if intent_key[-1] == "Khoảng_cách":
                output = self._handle_known_entity(entity_id, intent_key, has_n) + " năm ánh sáng"
                return output
            return self._handle_known_entity(entity_id, intent_key, has_n)

        # Luồng 2: Tìm thực thể qua mô tả (Ví dụ: "Chòm sao nào có tên tiếng anh là The Lion?")
        if not entity_id and intent_key:
            if intent_key[-1] == "Khoảng_cách":
                output = self._handle_unknown_entity(nlp_result) + " năm ánh sáng"
                return output
            return self._handle_unknown_entity(nlp_result)

        # Luồng 3: Không hiểu câu hỏi hoặc không có thông tin
        return "Xin lỗi, tôi chưa hiểu câu hỏi hoặc không tìm thấy thông tin liên quan."