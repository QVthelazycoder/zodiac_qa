# app.py
import os
import streamlit as st
import base64
from streamlit_lottie import st_lottie
import requests
from src.search_engine import SearchEngine

# Đường dẫn tuyệt đối của m
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_FOLDER = os.path.join(BASE_DIR, "assets", "pictures")

IMAGE_ENTITY_MAP = {
    # --- CÁC NGÔI SAO SÁNG (Dựa trên danh sách file mới nhất của m) ---
    "hamal": "Hamal", "2.01": "Hamal",
    "aldebaran": "Aldebaran", "0.87": "Aldebaran",
    "regulus": "Regulus", "1.36": "Regulus",
    "spica": "Spica", "0.98": "Spica",
    "antares": "Antares", "1.06": "Antares",
    "pollux": "Pollux", "1.16": "Pollux",
    "al tarf": "Al_Tarf", "3.5": "Al_Tarf",
    "deneb algedi": "Deneb_Algedi", "2.87": "Deneb_Algedi",
    "eta piscium": "Eta_Piscium", "3.61": "Eta_Piscium",
    "kaus australis": "Kaus_Australis", "1.85": "Kaus_Australis",
    "sadalsuud": "Sadalsuud", "2.88": "Sadalsuud",
    "zubeneschamali": "Zubeneschamali", "2.61": "Zubeneschamali",

    # --- 12 CUNG HOÀNG ĐẠO ---
    "bạch dương": "Aries", "aries": "Aries", "the ram": "Aries",
    "kim ngưu": "Taurus", "trâu vàng": "Taurus", "taurus": "Taurus", "the bull": "Taurus",
    "song tử": "Gemini", "song nam": "Gemini", "cặp song sinh": "Gemini", "gemini": "Gemini", "the twins": "Gemini",
    "cự giải": "Cancer", "con cua": "Cancer", "bắc giải": "Cancer", "cancer": "Cancer", "the crab": "Cancer",
    "sư tử": "Leo", "hải sư": "Leo", "leo": "Leo", "the lion": "Leo",
    "xử nữ": "Virgo", "trinh nữ": "Virgo", "thất nữ": "Virgo", "virgo": "Virgo", "the virgin": "Virgo",
    "thiên bình": "Libra", "thiên xứng": "Libra", "cân": "Libra", "libra": "Libra", "the scales": "Libra",
    "bọ cạp": "Scorpius", "thần nông": "Scorpius", "hổ cáp": "Scorpius", "thiên yết": "Scorpius", "scorpio": "Scorpius", "scorpius": "Scorpius", "the scorpion": "Scorpius",
    "nhân mã": "Sagittarius", "xạ thủ": "Sagittarius", "sagittarius": "Sagittarius", "the archer": "Sagittarius",
    "ma kết": "Capricorn", "dê biển": "Capricorn", "capricorn": "Capricorn", "the sea-goat": "Capricorn",
    "bảo bình": "Aquarius", "thủy bình": "Aquarius", "aquarius": "Aquarius", "the water bearer": "Aquarius",
    "song ngư": "Pisces", "hai con cá": "Pisces", "pisces": "Pisces", "the fish": "Pisces",

    # --- NHÂN VẬT THẦN THOẠI & QUÁI VẬT ---
    "castor": "Castor", "Một trong cặp song sinh Dioscuri, nổi tiếng về kỹ năng cưỡi ngựa.": "Castor",
    "anh em castor và pollux": "Anh_em_Castor_va_Pollux", "Pollux được ban cho sự bất tử nhưng anh kiên quyết chia sẻ điều này với Castor": "Anh_em_Castor_va_Pollux",
    "zeus": "Zeus", "Vị thần tối cao cai quản bầu trời và sấm sét.": "Zeus",
    "hera": "Hera", "Nữ hoàng của các vị thần, vợ của Zeus, thường ghen tức và đối đầu với Hercules.": "Hera",
    "hercules": "Hercules", "Vị anh hùng con của Zeus, thực hiện mười hai kỳ công.": "Hercules",
    "hermes": "Hermes", "Sứ giả của các vị thần, người ban con cừu vàng cho hai anh em.": "Hermes",
    "artemis": "Artemis", "Nữ thần săn bắn và mặt trăng, em gái song sinh của Apollo.": "Artemis",
    "aphrodite": "Aphrodite", "Nữ thần tình yêu và sắc đẹp, sinh ra từ bọt biển.": "Aphrodite",
    "eros": "Eros", "Thần tình yêu với cây cung phép, con trai của Aphrodite.": "Eros",
    "nữ thần aphrodite và eros": "Nữ_thần_Aphrodite_và_Eros", "Nữ thần sắc đẹp Aphrodite và con trai Eros biến thành hai con cá và buộc đuôi vào nhau": "Nữ_thần_Aphrodite_và_Eros",
    "thần pan": "Thần_Pan", "Một vị thần dạng dê, thân nửa dê nửa cá": "Thần_Pan",
    "aigipan": "Aigipan", "Sinh vật nửa dê nửa người, trợ giúp Zeus trong cuộc chiến với Typhon.": "Aigipan",
    "europa": "Europa", "Nàng công chúa Phoenicia được Zeus hóa thành bò trắng đưa đến Crete.": "Europa",
    "gaia": "Gaia", "Nữ thần Đất Mẹ, cội nguồn của các vị thần và muôn loài.": "Gaia",
    "themis": "Themis", "Nữ thần Công lý và Trật tự thiêng liêng, hiện thân của luật lệ và lẽ phải.": "Themis",
    "typhon": "Typhon", "Quái vật rồng khổng lồ, kẻ thù đáng sợ nhất của Zeus.": "Typhon",
    "astraea": "Astraea", "Nữ thần công lý cuối cùng rời bỏ nhân gian, gắn với chòm sao Xử Nữ.": "Astraea",
    "ganymede": "Ganymede", "Hoàng tử thành Troy nổi tiếng vì sắc đẹp": "Ganymede",
    "kheiron": "Kheiron", "Centaurs hiền minh và bất tử, thầy của nhiều anh hùng như Achilles và Hercules.": "Kheiron",
    "nhân mã chiron": "Nhân_mã_Chiron", "Trưởng lão và thông thái nhất trong các nhân mã, người con bất tử": "Nhân_mã_Chiron",
    "leda": "Leda", "Hoàng hậu xứ Sparta, người được Zeus hóa thành thiên nga quyến rũ.": "Leda",
    "helle": "Helle", "Chị của Phrixus, rơi xuống biển khi đang cưỡi con cừu vàng.": "Helle",
    "phrixus": "Phrixus", "Hoàng tử được con cừu vàng cứu thoát đến Colchis.": "Phrixus",
    "orion": "Orion", "Thợ săn khổng lồ nổi tiếng, gắn với chòm sao Orion.": "Orion",
    "bò mộng cretan": "Bò_Mộng_Cretan", "Con bò trắng thần thoại từ Crete, được Poseidon ban cho vua Minos.": "Bò_Mộng_Cretan",
    "cán cân công lý": "Cán_cân_Công_lý", "Phản ánh vai trò của các vị thần trong việc duy trì trật tự và sự công bằng giữa con người": "Cán_cân_Công_lý",
    "con bọ cạp": "Con Bọ Cạp Orion", "Con bọ cạp khổng lồ": "Con Bọ Cạp Orion",
    "con cua": "Con_Cua_Carcinus", "Con cua khổng lồ với lớp da cứng cáp và nhiều gai sắt nhọn": "Con_Cua_Carcinus",
    "sư tử nemean": "Sư_tử_Nemean", "Quái thú có bộ da không thể xuyên thủng bởi vũ khí, quấy nhiễu vùng Nemea": "Sư_tử_Nemean",
    "con cừu vàng": "Con_Cừu_Vàng", "Con cừu đực có bộ lông bằng vàng của thần Hermes.": "Con_Cừu_Vàng",
    "carcinus": "Carcinus", "Con cua khổng lồ Hera sai đến cản đường Hercules trong trận chiến với Hydra.": "Carcinus",
}

def get_zodiac_image_path(response_text):
    if not response_text:
        return []
    
    response_text = response_text.lower()
    found_filenames = []
    seen_filenames = set()
    
    # Sắp xếp từ khóa dài nhất lên trước để bắt chính xác (ví dụ "Deneb Algedi" trước "Algedi")
    sorted_keywords = sorted(IMAGE_ENTITY_MAP.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in response_text:
            mapped = IMAGE_ENTITY_MAP[keyword]
            if mapped not in seen_filenames:
                found_filenames.append(mapped)
                seen_filenames.add(mapped)
            
    if not found_filenames:
        return []

    try:
        if not os.path.exists(ASSETS_FOLDER):
            return []

        all_files = os.listdir(ASSETS_FOLDER)
        file_map = {}
        for f in all_files:
            name_part, _ = os.path.splitext(f)
            file_map[name_part.lower()] = f

        image_paths = []
        seen_files = set()
        for found_filename in found_filenames:
            normalized = found_filename.lower().replace(" ", "_")
            f = file_map.get(normalized)
            if f and f not in seen_files:
                image_paths.append(os.path.join(ASSETS_FOLDER, f))
                seen_files.add(f)

        return image_paths
    except:
        return []

# Khởi tạo engine
@st.cache_resource
def load_engine():
    return SearchEngine()

def main():
    st.set_page_config(
        page_title="Zodiac Celestial Oracle", 
        page_icon="✨",
        layout="centered"
    )
    
    # CSS
    st.markdown("""
    <style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Raleway:wght@300;400;600&display=swap');
    
    /* Ẩn header trắng của Streamlit */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        display: none !important;
    }
    
    /* Ẩn toolbar và menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Nền gradient đơn giản */
    .stApp {
        background: linear-gradient(180deg, #0f1020 0%, #1a1a40 50%, #2d1b4e 100%);
        color: #ffffff;
    }
    
    /* Đảm bảo toàn bộ body không có margin/padding */
    .main {
        padding-top: 1rem !important;
    }
    
    /* Ẩn background trắng của Lottie animation */
    iframe[title="streamlit_lottie.st_lottie"] {
        background: transparent !important;
    }
    
    div[data-testid="stImage"] {
        background: transparent !important;
    }
    
    /* Hiệu ứng sao nhỏ */
    .stApp::after {
        content: '✨ ⭐ 🌟 ✨ ⭐ 🌟 ✨ ⭐ 🌟';
        position: fixed;
        top: 10px;
        left: 0;
        right: 0;
        text-align: center;
        font-size: 20px;
        opacity: 0.3;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Tiêu đề */
    h1 {
        font-family: 'Orbitron', sans-serif !important;
        text-align: center !important;
        color: #ffd700 !important;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        font-size: 2.5rem !important;
        margin-top: 1rem !important;
    }
    
    /* Text thường */
    .stMarkdown p {
        font-family: 'Raleway', sans-serif;
        color: #e0e0e0 !important;
    }
    
    /* Input */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #000000 !important;
        border: 2px solid #ffd700 !important;
        border-radius: 20px !important;
        padding: 12px 20px !important;
        font-size: 1rem !important;
        font-family: 'Raleway', sans-serif !important;
    }
    
    .stTextInput input:focus {
        border-color: #ffed4e !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.5) !important;
    }
    
    /* Button */
    .stFormSubmitButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 10px 30px !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100% !important;
    }

    .stFormSubmitButton button:hover {
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Success box */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-left: 4px solid #ffd700 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(26, 26, 62, 0.9) !important;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #ffd700 !important;
        font-family: 'Orbitron', sans-serif !important;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
        color: #d0d0d0 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffd700 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("✨ CELESTIAL ORACLE ✨")
    
    st.markdown("""
    <div style='text-align: center; color: #b8c5d6; font-size: 1.1rem; margin-bottom: 2rem;'>
    🔮 Khám Phá Bí Ẩn Vũ Trụ & 12 Chòm Sao 🔮
    </div>
    """, unsafe_allow_html=True)
    
    # Chèn nhạc nền (optional)
    try:
        with open("./assets/music.mp3", "rb") as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        st.components.v1.html(f"""
        <audio autoplay loop style="display:none;">
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
        </audio>
        """, height=0)
    except:
        pass  # Nếu không có file nhạc thì bỏ qua

    # Load animation Lottie với background trong suốt
    try:
        r = requests.get("https://lottie.host/677cefb7-51ca-40e7-b5be-89c4e0fbc6dc/Zn3WbTssyo.json", timeout=3)
        if r.status_code == 200:
            lottie_star = r.json()
            # Container với background khớp màu nền
            st.markdown("""
            <div style='background: transparent; padding: 20px; border-radius: 15px; margin: 20px 0;'>
            """, unsafe_allow_html=True)
            st_lottie(lottie_star, height=150, key="stars", quality="high")
            st.markdown("</div>", unsafe_allow_html=True)
    except:
        # Nếu không load được animation, hiển thị icons thay thế
        st.markdown("""
        <div style='text-align: center; font-size: 3rem; margin: 20px 0;'>
        🌟 ⭐ ✨ 🌙 🪐
        </div>
        """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 🌟 Câu Hỏi Mẫu")
        st.markdown("---")
        st.markdown("""
        🔸 Aries có ngôi sao sáng nhất là gì?
        
        🔸 Ngôi sao Hamal có cấp sao là bao nhiêu?
        
        🔸 Thần thoại về chòm sao Kim Ngưu?
        
        🔸 Leo thuộc nguyên tố nào?
        
        🔸 Scorpius được chi phối bởi hành tinh nào?
        """)
        
        st.markdown("---")
        st.markdown("### 🪐 Về Hệ Thống")
        st.markdown("AI-powered Q&A về thiên văn học và chòm sao")

    # Spacing
    st.markdown("<br>", unsafe_allow_html=True)

    # # Input
    # st.markdown("#### 💫 Đặt Câu Hỏi Của Bạn")
    # query = st.text_input(
    #     "Nhập câu hỏi:", 
    #     placeholder="Ví dụ: Bạch Dương thuộc nguyên tố nào?",
    #     # label_visibility="collapsed"
    # )

    # st.markdown("<br>", unsafe_allow_html=True)
    
    # # Button
    # submit_button = st.button("🔮 Khám Phá Câu Trả Lời")

    with st.form("question_form"):
        st.markdown("#### 💫 Đặt Câu Hỏi Của Bạn")
        query = st.text_input(
            "Nhập câu hỏi:",
            placeholder="Ví dụ: Bạch Dương thuộc nguyên tố nào?"
        )
        submit_button = st.form_submit_button("🔮 Khám Phá Câu Trả Lời")

    # Load engine
    try:
        engine = load_engine()
    except Exception as e:
        st.error(f"⚠️ Không thể khởi tạo search engine: {str(e)}")
        return

    # Xử lý câu hỏi
    if submit_button and query:
        with st.spinner("✨ Đang kết nối với vũ trụ..."):
            try:
                response = engine.answer(query)
                
                # Hiển thị kết quả
                st.success("🌟 Thông Điệp Từ Vũ Trụ:")
                st.markdown(f"### {response}")
                
                # Hiển thị hình ảnh nếu có
                try:
                    image_paths = get_zodiac_image_path(f"{query} {response}")
                    if image_paths:
                        for image_path in image_paths:
                            # Lấy tên file không bao gồm đuôi .jpg/.png
                            filename = os.path.basename(image_path)
                            caption = os.path.splitext(filename)[0]
                            st.image(image_path, caption=caption, use_container_width=True)
                except:
                    pass  # Nếu không có hình ảnh thì bỏ qua

                # # Debug info
                # with st.expander("🔍 Xem Chi Tiết Xử Lý"):
                #     try:
                #         nlp_debug = engine.nlp.process_query(query)
                #         st.json(nlp_debug)
                #     except Exception as e:
                #         st.write(f"Debug info không khả dụng: {str(e)}")
                        
            except Exception as e:
                st.error("⚠️ Có lỗi xảy ra khi xử lý câu hỏi!")
                # st.error(f"Chi tiết: {str(e)}")
                
    elif submit_button and not query:
        st.warning("⚠️ Vui lòng nhập câu hỏi để khám phá bí ẩn vũ trụ")

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 0.9rem;'>
    ✨ Powered by Cosmic Intelligence | Made with 💫
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()