import google.generativeai as genai
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="스마트 일본어 단어장", page_icon="🇯🇵", layout="centered"
)

st.title("🇯🇵 AI 스마트 일본어 학습 단어장")
st.markdown(
    "한국어, 일본어, 혹은 **'츠쿠에'** 같은 한국식 발음으로 검색해도 완벽하게 찾아줍니다!"
)

# 사이드바 설정 (API 키 입력)
with st.sidebar:
  st.header("⚙️ 설정")
  api_key = st.text_input(
      "Gemini API Key 입력",
      type="password",
      help="Google AI Studio에서 발급받은 API 키를 입력하세요.",
  )
  st.markdown("---")
  st.markdown("💡 **팁**: 한 번 입력하면 앱이 켜져 있는 동안 유지됩니다.")

# 검색 입력창
query = st.text_input(
    "검색할 단어를 입력하세요",
    placeholder="예: 책상, 机, 츠쿠에, 사랑, 사쿠라 등",
)

if st.button("🔍 검색하기", type="primary"):
  if not api_key:
    st.warning("⚠️ 사이드바에 Gemini API Key를 먼저 입력해주세요!")
  elif not query.strip():
    st.warning("⚠️ 검색어를 입력해주세요!")
  else:
    # API 설정
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 프롬프트 작성
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

    with st.spinner("✨ 단어 분석 및 예문 생성 중..."):
      try:
        response = model.generate_content(prompt)
        st.markdown("---")
        st.markdown(response.text)
      except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")