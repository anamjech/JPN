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
  st.session_state.current_result = None  # JSON 데이터를 저장하기 위해 None으로 초기화


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

  # JSON 형식으로 답변을 강제하여 데이터 꼬임 현상 원천 차단
  prompt = f"""
    사용자가 일본어 학습을 위해 다음 단어를 검색했습니다: "{q}"
    올바른 일본어 단어 정보를 찾아 반드시 아래의 JSON 형식으로만 응답해주세요. 
    다른 설명이나 마크다운 코드 블록 이외의 텍스트는 출력하지 마세요.

    {{
      "word_info": "단어 기본 정보 (일본어 표기 및 대표 형태)",
      "kanji": "한자 (한자가 없으면 '없음')",
      "hiragana": "히라가나",
      "meaning": "한글 뜻",
      "kunyomi": "훈독 (없으면 '없음')",
      "onyomi": "음독 (없으면 '없음')",
      "examples": [
        {{
          "original": "순수 일본어 원문 문장 (절대로 한글을 섞지 말고 일본어만 작성)",
          "reading": "오직 히라가나로만 작성된 읽기",
          "meaning": "한글 뜻 번역"
        }},
        {{
          "original": "순수 일본어 원문 문장 (절대로 한글을 섞지 말고 일본어만 작성)",
          "reading": "오직 히라가나로만 작성된 읽기",
          "meaning": "한글 뜻 번역"
        }},
        {{
          "original": "순수 일본어 원문 문장 (절대로 한글을 섞지 말고 일본어만 작성)",
          "reading": "오직 히라가나로만 작성된 읽기",
          "meaning": "한글 뜻 번역"
        }}
      ]
    }}
    """

  with st.spinner("✨ AI가 단어를 분석하고 정돈된 예문을 만드는 중..."):
    try:
      response = model.generate_content(prompt)
      raw_text = response.text.strip()

      # JSON 형식 외의 불필요한 마크다운 기호 제거
      cleaned_json = re.sub(
          r"^```json\s*|\s*```$", "", raw_text, flags=re.MULTILINE
      ).strip()
      data = json.loads(cleaned_json)
      st.session_state.current_result = data
    except Exception as e:
      st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
      st.session_state.current_result = None


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

# 결과 출력 (JSON 데이터를 안전하게 화면에 렌더링)
if st.session_state.current_result:
  st.markdown("---")
  data = st.session_state.current_result

  # 1. 단어 기본 정보 출력
  st.markdown(f"### 📌 단어 기본 정보")
  st.markdown(f"- **단어**: {data.get('word_info', '')}")
  st.markdown(f"- **한자**: {data.get('kanji', '')}")
  st.markdown(f"- **히라가나**: {data.get('hiragana', '')}")
  st.markdown(f"- **한글 뜻**: {data.get('meaning', '')}")
  st.markdown(f"- **훈독**: {data.get('kunyomi', '')}")
  st.markdown(f"- **음독**: {data.get('onyomi', '')}")

  # 2. 실생활 예문 출력 및 오디오 플레이어 배치
  examples = data.get("examples", [])
  if examples:
    st.markdown("### 🔊 실생활 예문")
    for idx, ex in enumerate(examples, 1):
      orig = ex.get("original", "").strip()
      read = ex.get("reading", "").strip()
      mean = ex.get("meaning", "").strip()

      # 요청하신 정확한 양식으로 마크다운 출력
      st.markdown(f"- **[일본어 원문]**: {orig}")
      st.markdown(f"- **[히라가나 읽기]**: {read}")
      st.markdown(f"- **[한글 뜻]**: {mean}")

      # 오직 [일본어 원문]에 해당하는 내용만 음성으로 변환하여 재생
      if orig:
        try:
          tts = gTTS(text=orig, lang="ja")
          fp = io.BytesIO()
          tts.write_to_fp(fp)
          fp.seek(0)
          st.audio(fp.read(), format="audio/mp3")
        except Exception:
          pass

      st.markdown("<br>", unsafe_allow_html=True)
