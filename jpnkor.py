import json
import os
import re
import google.generativeai as genai
from gtts import gTTS
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="스마트 일본어 단어장", page_icon="🇯🇵", layout="centered"
)

# 커스텀 CSS
st.markdown(
    """
    <style>
    .stButton button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 검색 기록을 파일로 저장하여 껐다 켜도 유지되도록 처리
HISTORY_FILE = "search_history.json"


def load_history():
  if os.path.exists(HISTORY_FILE):
    try:
      with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return []
  return []


def save_history(history_list):
  try:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
      json.dump(history_list, f, ensure_ascii=False, indent=4)
  except:
    pass


# 세션 스테이트 초기화
if "history" not in st.session_state:
  st.session_state.history = load_history()

if "api_key" not in st.session_state:
  st.session_state.api_key = ""

if "current_query" not in st.session_state:
  st.session_state.current_query = ""

if "current_result" not in st.session_state:
  st.session_state.current_result = ""

st.title("🇯🇵 AI 스마트 일본어 단어장")
st.markdown(
    "검색하고, 예문마다 **개별 원어민 음성**으로 발음을 확인해 보세요!"
)

# 1. Streamlit Secrets(비밀 설정)에서 API 키 자동 불러오기
api_key = ""
try:
  if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
  elif "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
  pass

# 사이드바 설정 (최근 검색 기록만 깔끔하게 유지)
with st.sidebar:
  st.header("⚙️ 설정")
  if api_key:
    st.success("✅ API 키 자동 로드됨")
  else:
    input_key = st.text_input(
        "Gemini API Key 입력",
        value=st.session_state.api_key,
        type="password",
    )
    if input_key:
      st.session_state.api_key = input_key
      api_key = input_key

  st.markdown("---")
  st.header("📜 최근 검색 기록")

  if st.session_state.history:
    # 최근 검색어가 위로 오도록 출력 (최대 15개)
    for item in reversed(st.session_state.history[-15:]):
      if st.button(f"🔍 {item}", key=f"hist_{item}"):
        st.session_state.current_query = item
        st.rerun()

    if st.button("🗑️ 검색 기록 비우기"):
      st.session_state.history = []
      if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
      st.rerun()
  else:
    st.info("검색 기록이 없습니다.")

# 검색 입력창
query = st.text_input(
    "검색할 단어를 입력하세요",
    value=st.session_state.current_query,
    placeholder="예: 책상, 机, 츠쿠에 등",
)

search_clicked = st.button("🔍 검색하기", type="primary")

if search_clicked and query:
  st.session_state.current_query = query
  if not api_key:
    st.warning("⚠️ API 키가 설정되지 않았습니다!")
  else:
    # 검색 기록 추가 및 파일 저장 (껐다 켜도 유지)
    if query in st.session_state.history:
      st.session_state.history.remove(query)
    st.session_state.history.append(query)
    save_history(st.session_state.history)

    # API 설정 (gemini-3.5-flash-lite)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash-lite")

    prompt = f"""
    사용자가 일본어 학습을 위해 다음 단어를 검색했습니다: "{query}"
    이 단어가 한국어이든, 일본어(한자/히라가나/가타카나)이든, 한국식 발음/콩글리시(예: 츠쿠에)이든 상관없이 올바른 일본어 단어를 찾아 아래 양식에 맞추어 보기 좋은 마크다운 형식으로 상세히 설명해주세요.

    반드시 다음 항목들을 명확히 구분해서 출력해 주세요:
    1. **단어 기본 정보** (일본어 표기 및 대표 형태)
    2. **한자** (한자가 없는 단어면 '없음' 표시)
    3. **히라가나**
    4. **한글 뜻**
    5. **훈독** (없으면 '없음')
    6. **음독** (없으면 '없음')
    7. **실생활 예문 3개** (반드시 각 예문 앞에 [EX1], [EX2], [EX3] 태그를 붙여주고, 일본어 원문과 읽기, 한글 뜻을 포함해 주세요.)
    형식 예시:
    [EX1] 일본어문장 (히라가나 읽기) - 한글 뜻
    [EX2] 일본어문장 (히라가나 읽기) - 한글 뜻
    [EX3] 일본어문장 (히라가나 읽기) - 한글 뜻

    가독성이 좋고 깔끔한 마크다운 형식으로 출력해 주세요.
    """

    with st.spinner("✨ AI가 단어를 분석하고 예문을 만드는 중..."):
      try:
        response = model.generate_content(prompt)
        st.session_state.current_result = response.text
      except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# 결과 출력 및 예문별 개별 음성 플레이어 배치
if st.session_state.current_result:
  st.markdown("---")

  text = st.session_state.current_result

  # [EX1], [EX2], [EX3] 태그를 기준으로 결과 분리
  ex_matches = re.findall(r"\[EX([123])\]\s*(.*?)(?=\[EX[123]\]|$)", text, re.DOTALL)

  # 단어 기본 정보 출력 (예문 태그 전까지의 내용)
  base_info = re.split(r"\[EX1\]", text)[0]
  st.markdown(base_info)

  # 예문별 개별 음성 플레이어 생성
  if ex_matches:
    st.markdown("### 🔊 실생활 예문 및 개별 원어민 음성")
    for num, content in ex_matches:
      content = content.strip()
      st.markdown(f"**예문 {num}**: {content}")

      # 일본어 문장만 추출 (첫 번째 괄호나 기호 전까지)
      jp_part = content.split("(")[0].split("-")[0].strip()

      try:
        tts = gTTS(text=jp_part, lang="ja")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp.read(), format="audio/mp3")
      except:
        pass
      st.markdown("")
  else:
    st.markdown(text)
