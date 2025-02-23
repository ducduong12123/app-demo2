# --- START OF FILE app.py ---
import streamlit as st
import google.generativeai as genai
import datetime
import json
import os
import random # Import random for generating diverse AI responses

# Cấu hình API Key (Thay YOUR_API_KEY bằng API key của bạn)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Lấy từ biến môi trường
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input("Google API Key:", type="password")
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

# Chọn mô hình
model = genai.GenerativeModel("gemini-2.0-flash")

# --- Quản lý người dùng ---
def get_user_id():
    """Lấy hoặc tạo ID người dùng duy nhất."""
    user_id = st.session_state.get('user_id') # Kiểm tra session state trước
    if not user_id:
        user_id = st.text_input("Nhập tên người dùng của bạn:", key="username_input") # Thêm key để quản lý state
        if user_id:
             st.session_state['user_id'] = user_id # Lưu vào session state khi có input
        else:
            st.stop() # Dừng app nếu chưa có username
    return st.session_state.get('user_id') # Trả lại user_id từ session state


def save_chat_history(history, user_id):
    """Lưu lịch sử trò chuyện vào file JSON theo user_id."""
    filename = f"chat_history_{user_id}.json" # Sử dụng user_id trong tên file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def load_chat_history(user_id):
    """Tải lịch sử trò chuyện từ file JSON theo user_id (nếu có)."""
    filename = f"chat_history_{user_id}.json" # Sử dụng user_id trong tên file
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# --- Hàm tạo phản hồi AI gợi mở ---
def generate_ai_response(user_input):
    """Tạo phản hồi AI gợi mở và đồng cảm hơn."""
    prompts = [
        "Tôi hiểu bạn đang chia sẻ điều này. Bạn có thể nói thêm về cảm xúc của bạn lúc này không?",
        "Nghe có vẻ bạn đang trải qua điều gì đó khó khăn. Điều gì khiến bạn cảm thấy như vậy?",
        "Cảm ơn bạn đã chia sẻ với tôi. Bạn muốn tôi giúp bạn điều gì?",
        "Tôi đang lắng nghe bạn. Hãy thoải mái chia sẻ thêm nhé.",
        "Bạn đã nghĩ về điều này bao lâu rồi? Bạn có thể kể thêm cho tôi nghe được không?"
    ]
    prompt = random.choice(prompts) # Chọn ngẫu nhiên một prompt để đa dạng phản hồi
    response = model.generate_content(f"{prompt} {user_input}").text
    return response


# --- Hàm phân tích lo âu (cải tiến) ---
def phan_tich_lo_au(hoi_thoai, analysis_type='recent'): # Thêm tham số analysis_type
    """
    Phân tích đoạn hội thoại để phát hiện dấu hiệu lo âu, có 2 loại phân tích:
    - 'recent': Phân tích 5-10 tin nhắn cuối để phát hiện dấu hiệu lo âu gần đây.
    - 'progress': Phân tích toàn bộ hội thoại để theo dõi tiến trình cảm xúc.

    Args:
        hoi_thoai (str): Chuỗi hội thoại giữa người dùng và chatbot.
        analysis_type (str): Loại phân tích ('recent' hoặc 'progress'). Mặc định là 'recent'.

    Returns:
        str: Nhận định phân tích, hoặc thông báo nếu không đủ thông tin.
    """

    if analysis_type == 'recent':
        prompt_prefix = """
        Bạn là một trợ lý AI có khả năng phân tích ngôn ngữ để phát hiện dấu hiệu lo âu GẦN ĐÂY.
        Hãy phân tích ĐOẠN HỘI THOẠI GẦN ĐÂY (5-10 tin nhắn cuối) sau và trả lời các câu hỏi sau:
        """
        prompt_suffix = """
        Lưu ý: Tập trung vào các biểu hiện NGÔN NGỮ GẦN ĐÂY, cảm xúc, và chủ đề trò chuyện TRONG 5-10 TIN NHẮN CUỐI.
        """
    elif analysis_type == 'progress':
        prompt_prefix = """
        Bạn là một trợ lý AI có khả năng phân tích ngôn ngữ để THEO DÕI TIẾN TRÌNH cảm xúc và suy nghĩ của người dùng.
        Hãy phân tích TOÀN BỘ ĐOẠN HỘI THOẠI sau và trả lời các câu hỏi sau để theo dõi sự thay đổi:
        """
        prompt_suffix = """
        Lưu ý: Tập trung vào sự THAY ĐỔI TRONG NGÔN NGỮ, cảm xúc, và chủ đề trò chuyện xuyên suốt cuộc hội thoại.
        """
    else:
        return "Loại phân tích không hợp lệ." # Xử lý trường hợp type không hợp lệ

    prompt_questions = """
    1. Người dùng có biểu hiện bất kỳ dấu hiệu lo âu nào không (ví dụ: lo lắng, sợ hãi, căng thẳng, mất ngủ, khó tập trung, né tránh,...)?
    2. Nếu có, hãy liệt kê các dấu hiệu cụ thể (dựa trên ngôn ngữ, biểu cảm, chủ đề trò chuyện).
    3. Đánh giá mức độ lo âu (nếu có): Nhẹ, Trung bình, hay Nặng? (Giải thích lý do).
    4. Dựa trên TOÀN BỘ cuộc hội thoại (đối với phân tích tiến trình) hoặc ĐOẠN HỘI THOẠI GẦN ĐÂY (đối với phân tích gần đây), có sự thay đổi nào trong cảm xúc, suy nghĩ của người dùng không? Nếu có, hãy mô tả sự thay đổi đó.
    5. Nếu không có đủ thông tin để đánh giá, hãy ghi rõ "Không đủ thông tin".

    """

    prompt = f"""
    {prompt_prefix}
    {prompt_questions}

    Đoạn hội thoại:
    {hoi_thoai}

    {prompt_suffix}

    Trả lời:
    """

    response = model.generate_content(prompt)
    return response.text

# --- Giao diện Streamlit ---
st.title("Chatbot AI Phát hiện Dấu hiệu Lo âu")

user_id = get_user_id() # Lấy user_id
st.write(f"Chào mừng, {user_id}!") # Hiển thị tên người dùng

# Tải lịch sử trò chuyện (nếu có) cho người dùng hiện tại
history = load_chat_history(user_id)

# Hiển thị lịch sử trò chuyện
for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ô nhập tin nhắn của người dùng
user_input = st.chat_input("Nhắn tin ở đây...")

if user_input:
    # 1. Hiển thị tin nhắn của người dùng
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Thêm tin nhắn vào lịch sử
    timestamp = datetime.datetime.now().isoformat()
    history.append({"role": "user", "content": user_input, "timestamp": timestamp})


    # 3. Tạo phản hồi từ AI (phản hồi cải tiến)
    with st.spinner('Đang suy nghĩ...'):
        ai_response = generate_ai_response(user_input) # Sử dụng hàm tạo phản hồi cải tiến


    # 4. Hiển thị phản hồi của AI
    with st.chat_message("assistant"):
        st.markdown(ai_response)

    # 5. Thêm phản hồi của AI vào lịch sử
    history.append({"role": "assistant", "content": ai_response, "timestamp": timestamp})

    # Lưu lại lịch sử cho người dùng hiện tại
    save_chat_history(history, user_id)

# Nút phân tích
col1, col2 = st.columns(2) # Chia layout thành 2 cột

with col1:
    if st.button("Phân tích Dấu hiệu Lo âu Gần đây"): # Nút phân tích dấu hiệu lo âu gần đây
        with st.spinner('Đang phân tích...'):
            # Tạo chuỗi hội thoại từ history (chỉ lấy 5-10 tin nhắn cuối)
            recent_history = history[-10:] if len(history) >= 10 else history # Lấy 10 tin nhắn cuối hoặc ít hơn nếu lịch sử ngắn
            hoi_thoai_recent = ""
            for message in recent_history:
                hoi_thoai_recent += f"{message['role']}: {message['content']}\n"

            phan_tich = phan_tich_lo_au(hoi_thoai_recent, analysis_type='recent') # Gọi hàm phân tích với type='recent'

        st.subheader("Kết quả Phân tích Dấu hiệu Lo âu Gần đây:") # Thay đổi tiêu đề cho rõ ràng
        st.write(phan_tich)
        st.write("Lưu ý: Đây chỉ là phân tích dựa trên thông tin bạn cung cấp. Để có đánh giá chính xác và hỗ trợ phù hợp, bạn nên tìm kiếm sự tư vấn từ chuyên gia tâm lý.")

with col2:
    if st.button("Phân tích Tiến trình"): # Nút phân tích tiến trình
        with st.spinner('Đang phân tích...'):
            # Tạo chuỗi hội thoại từ history (toàn bộ lịch sử)
            hoi_thoai_progress = "" # Đổi tên biến để rõ ràng
            for message in history:
                hoi_thoai_progress += f"{message['role']}: {message['content']}\n"

            phan_tich = phan_tich_lo_au(hoi_thoai_progress, analysis_type='progress') # Gọi hàm phân tích với type='progress'

        st.subheader("Kết quả Phân tích Tiến trình:") # Tiêu đề cho phân tích tiến trình
        st.write(phan_tich)
        st.write("Lưu ý: Đây chỉ là phân tích dựa trên thông tin bạn cung cấp. Để có đánh giá chính xác và hỗ trợ phù hợp, bạn nên tìm kiếm sự tư vấn từ chuyên gia tâm lý.")

# --- END OF FILE app.py ---