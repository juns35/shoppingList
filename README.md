# 🛒 쇼핑 리스트

Streamlit으로 만든 가벼운 쇼핑 리스트 웹 앱입니다. 요구사항은 [PRD.md](PRD.md)를 참고하세요.

## 로컬 실행

Python 3.10 이상, Streamlit 1.51 이상이 필요합니다.

```bash
pip install -r requirements.txt
streamlit run app.py
```

실행 후 브라우저에서 http://localhost:8501 로 접속합니다.

## 배포 (Streamlit Community Cloud)

1. 이 폴더를 GitHub 저장소에 push 합니다.
2. https://share.streamlit.io 에 GitHub 계정으로 로그인합니다.
3. **Create app** → 저장소, 브랜치, 메인 파일(`app.py`)을 선택하고 **Deploy** 를 누릅니다.
4. 발급된 `https://<앱이름>.streamlit.app` 주소로 접속해 확인합니다.
5. 이후 해당 브랜치에 push 하면 자동으로 다시 배포됩니다.

참고
- 데이터는 브라우저 세션에만 저장되므로 새로고침하면 리스트가 초기화됩니다.
- 일정 기간 접속이 없으면 앱이 절전 상태가 되며, 다시 깨어나는 데 수십 초가 걸릴 수 있습니다.
