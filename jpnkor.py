import io
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

# 검색 기록을 파일로 저장
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


# 공통 검색 실행 함수 (기록 클릭 시 즉시 검색 지원)
def perform_search(q):
  if not api_key:
    st.warning("⚠️ API 키가 설정되지 않았습니다!")
    return

  if q in st.session_state.history:
    st.session_state.history.remove(q)
  st.session_state.history.append(q)
  save_history(st.session_state.history)

  genai.configure(api_key=api_key)
  model = genai.GenerativeModel("gemini-3.5-flash-lite")

  prompt = f"""
    사용자가 일본어 학습을 위해 다음 단어를 검색했습니다: "{q}"
    올바른 일본어 단어를 찾아 아래 양식에 맞추어 마크다운 형식으로 **정확히 한 번만** 상세히 설명해주세요. 
    절대 내용을 반복해서 출력하지 마세요.

    반드시 다음 항목들을 명확히 구분해서 출력해 주세요:
    1. **단어 기본 정보** (일본어 표기 및 대표 형태)
    2. **한자** (한자가 없는 단어면 '없음' 표시)
    3. **히라가나**
    4. **한글 뜻**
    5. **훈독** (없으면 '없음')
    6. **음독** (없으면 '없음')
    7. **실생활 예문 3개** (반드시 아래 형식을 정확히 지켜주세요. [일본어 원문]에는 **절대로 한글을 쓰지 말고 순수 일본어(한자/가나)**만 작성하고, [히라가나 읽기]는 **오직 히라가나**로만 작성하세요.)

    [EX1]
    - **[일본어 원문]**: (순수 일본어 문장만 작성, 한글 금지)
    - **[히라가나 읽기]**: (오직 히라가나로만 작성)
    - **[한글 뜻]**: (한국어 번역)

    [EX2]
    - **[일본어 원문]**: (순수 일본어 문장만 작성, 한글 금지)
    - **[히라가나 읽기]**: (오직 히라가나로만 작성)
    - **[한글 뜻]**: (한국어 번역)

    [EX3]
    - **[일본어 원문]**: (순수 일본어 문장만 작성, 한글 금지)
    - **[히라가나 읽기]**: (오직 히라가나로만 작성)
    - **[한글 뜻]**: (한국어 번역)

    가독성이 좋고 깔끔한 마크다운 형식으로 출력해 주세요.
    """

  with st.spinner("✨ AI가 단어를 분석하고 예문을 만드는 중..."):
    try:
      response = model.generate_content(prompt)
      st.session_state.current_result = response.text
    except Exception as e:
      st.error(f"오류가 발생했습니다: {e}")


st.title("🇯🇵 AI 스마트 일본어 단어장")
st.markdown("검색하고, 예문마다 **일본어 원문만 깔끔하게** 음성으로 들어보세요!")

# Streamlit Secrets에서 API 키 자동 불러오기
api_key = ""
try:
  if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
  elif "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
  pass

# 사이드바 설정 (기록 클릭 시 즉시 검색 실행)
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
    for item in reversed(st.session_state.history[-15:]):
      if st.button(f"🔍 {item}", key=f"hist_{item}"):
        st.session_state.current_query = item
        perform_search(item)
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
  perform_search(query)
  st.rerun()

# 결과 출력 및 예문별 개별 음성 플레이어 배치
if st.session_state.current_result:
  st.markdown("---")
  text = st.session_state.current_result

  ex_matches = re.findall(
      r"(?:###\s*)?\[EX([123])\]\s*(.*?)(?=(?:###\s*)?\[EX[123]\]|$)",
      text,
      re.DOTALL | re.IGNORECASE,
  )

  # 단어 기본 정보 출력 ([EX1] 등장 전까지의 내용)
  base_info = re.split(r"\[EX1\]", text, flags=re.IGNORECASE)[0]
  st.markdown(base_info)

  # 예문별 개별 음성 플레이어 생성 (중복 출력 방지 및 안전한 원문 추출)
  if ex_matches:
    st.markdown("### 🔊 실생활 예문")
    seen_exs = set()  # 모델이 답변을 반복 출력하는 경우 중복 방지용 세트

    for num, content in ex_matches:
      if num in seen_exs:
        continue
      seen_exs.add(num)

      content = content.strip()

      # 화면에는 AI가 작성한 자연스러운 마크다운 텍스트 전체 출력
      st.markdown(content)

      # [일본어 원문] 줄에서 순수 일본어 원문만 정밀 추출
      clean_jp = ""
      for line in content.split("\n"):
        if "원문" in line:
          text_part = re.sub(
              r".*?(\[일본어 원문\]|일본어 원문|원문)\s*[:]?\s*", "", line
          )
          clean_jp = re.sub(r"[\*\#\_\-\`\~]", "", text_part).strip()
          break

      # 이중 안전장치: 혹시라도 한글이 섞였다면 오직 일본어 문자(한자, 히라가나, 가타카나)만 골라냄
      jp_chars = re.findall(
          r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u30FC\u3005\s]+", clean_jp
      )
      clean_jp = "".join(jp_chars).strip()

      if clean_jp:
        try:
          tts = gTTS(text=clean_jp, lang="ja")
          fp = io.BytesIO()
          tts.write_to_fp(fp)
          fp.seek(0)
          st.audio(fp.read(), format="audio/mp3")
        except:
          pass

      st.markdown("<br>", unsafe_allow_html=True)
  else:
    st.markdown(text)
