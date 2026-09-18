import io
import google.generativeai as genai
from gtts import gTTS
import streamlit as st

# 페이지 기본 설정 (모바일 최적화 레이아웃)
st.set_page_config(
    page_title="스마트 일본어 단어장", page_icon="🇯🇵", layout="centered"
)

# 커스텀 CSS로 모바일/웹 UI 다듬기
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

# 세션 스테이트 초기화
if "history" not in st.session_state:
  st.session_state.history = []

if "vocab_book" not in st.session_state:
  st.session_state.vocab_book = {}

if "api_key" not in st.session_state:
  st.session_state.api_key = ""

if "current_query" not in st.session_state:
  st.session_state.current_query = ""

if "current_result" not in st.session_state:
  st.session_state.current_result = ""

if "current_audio" not in st.session_state:
  st.session_state.current_audio = None

st.title("🇯🇵 AI 스마트 일본어 단어장")
st.markdown(
    "검색하고, 단어장에 저장하고, **원어민 음성**으로 발음까지 들어보세요!"
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

# 사이드바 설정
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
  tab_history, tab_vocab = st.tabs(["📜 최근 검색", "⭐ 내 단어장"])

  with tab_history:
    if st.session_state.history:
      for item in reversed(st.session_state.history[-10:]):
        if st.button(f"🔍 {item}", key=f"hist_{item}"):
          st.session_state.current_query = item
          st.rerun()
      if st.button("🗑️ 검색 기록 비우기"):
        st.session_state.history = []
        st.rerun()
    else:
      st.info("검색 기록이 없습니다.")

  with tab_vocab:
    if st.session_state.vocab_book:
      st.markdown(f"**저장된 단어: {len(st.session_state.vocab_book)}개**")
      for vocab_item in list(st.session_state.vocab_book.keys()):
        col1, col2 = st.columns([3, 1])
        with col1:
          if st.button(f"📖 {vocab_item}", key=f"vocab_{vocab_item}"):
            st.session_state.current_query = vocab_item
            st.session_state.current_result = st.session_state.vocab_book[
                vocab_item
            ]["result"]
            st.session_state.current_audio = st.session_state.vocab_book[
                vocab_item
            ]["audio"]
            st.rerun()
        with col2:
          if st.button("❌", key=f"del_{vocab_item}"):
            del st.session_state.vocab_book[vocab_item]
            st.rerun()
    else:
      st.info("저장된 단어가 없습니다.")

# 검색 입력창
query = st.text_input(
    "검색할 단어를 입력하세요",
    value=st.session_state.current_query,
    placeholder="예: 책상, 机, 츠쿠에, 사랑 등",
)

search_clicked = st.button("🔍 검색하기", type="primary")

if search_clicked and query:
  st.session_state.current_query = query
  if not api_key:
    st.warning("⚠️ API 키가 설정되지 않았습니다!")
  else:
    if query in st.session_state.history:
      st.session_state.history.remove(query)
    st.session_state.history.append(query)

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
    7. **실생활 예문 3개** (간단하지만 자주 쓰는 문장으로 구성하되, [일본어 원문] / [히라가나 읽기] / [한글 뜻]을 각각 포함해 주세요.)

    가독성이 좋고 깔끔한 마크다운 형식으로 출력해 주세요.
    """

    with st.spinner("✨ AI가 단어를 분석하고 예문을 만드는 중..."):
      try:
        response = model.generate_content(prompt)
        st.session_state.current_result = response.text

        # gTTS로 읽어줄 텍스트 생성 (검색한 단어와 예문 요약 텍스트를 조합)
        tts_text = f"{query}의 일본어 표현입니다. {response.text}"
        tts = gTTS(text=tts_text, lang="ja")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.session_state.current_audio = fp.read()

      except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# 결과 출력 및 음성 재생, 단어장 저장
if st.session_state.current_result:
  st.markdown("---")

  # 음성 플레이어 출력
  if st.session_state.current_audio:
    st.markdown("### 🔊 원어민 발음 및 예문 듣기")
    st.audio(st.session_state.current_audio, format="audio/mp3")

  # 단어 내용 출력
  st.markdown(st.session_state.current_result)

  current_word = st.session_state.current_query
  is_saved = current_word in st.session_state.vocab_book

  col1, col2 = st.columns([1, 1])
  with col1:
    if not is_saved:
      if st.button("⭐ 이 단어를 내 단어장에 저장하기"):
        st.session_state.vocab_book[current_word] = {
            "result": st.session_state.current_result,
            "audio": st.session_state.current_audio,
        }
        st.success(f"'{current_word}' 저장 완료!")
        st.rerun()
    else:
      st.info("✅ 이미 내 단어장에 저장된 단어입니다.")
  with col2:
    if is_saved:
      if st.button("🗑️ 단어장에서 삭제하기"):
        del st.session_state.vocab_book[current_word]
        st.warning(f"'{current_word}' 삭제됨.")
        st.rerun()
