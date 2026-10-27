# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 현황
Streamlit(Python)으로 만든 가벼운 쇼핑 리스트 웹 앱입니다. `PROMPTS.md`의 1~4단계(뼈대 → 기능 → UI → Playwright 검토)와 검토에서 나온 버그 수정까지 모두 끝났습니다. 남은 작업은 Streamlit Community Cloud 배포와 PRD 4.6의 영구 저장(M4)입니다.

- `PRD.md` — 요구사항의 기준 문서. 기능 우선순위(P0/P1/P2), 데이터 모델, 화면 구성, 배포 계획
- `PROMPTS.md` — 단계별 개발 프롬프트(모두 완료)
- `REVIEW.md` — 4단계 검토 결과(PRD 체크표, 버그 7건)와 "6. 수정 결과". 아직 확인하지 못한 항목(Safari·Firefox, 아이템 100개 성능)도 여기 있음
- `review_screenshots/` — 검토·수정 검증 스크린샷. `REVIEW.md`가 파일명으로 참조하므로 이름을 바꾸지 말 것

## 명령어
```bash
pip install -r requirements.txt
streamlit run app.py
# Playwright 검토용 헤드리스 실행
streamlit run app.py --server.headless true --server.port 8501
```
이 PC에서 `python`은 Microsoft Store 바로가기라 동작하지 않음. Anaconda 인터프리터를 직접 지정할 것: `/c/Users/User/anaconda3/python.exe -m streamlit run app.py` (Python 3.14, Streamlit 1.58). 한글·이모지를 콘솔에 출력할 때는 `PYTHONIOENCODING=utf-8` 필요(기본 cp949). `-I` 옵션을 쓰면 이 환경변수가 무시되므로 대신 `-X utf8` 사용.

`.streamlit/config.toml`(테마) 변경은 서버를 재시작해야 반영됨. `app.py` 변경은 실행 중인 서버에도 다음 조작부터 반영되지만, 저장 직후 몇 초간은 제출이 무시될 수 있음.

## 테스트
저장소에 테스트 파일이나 린트 설정은 없음. 검증은 두 가지로 함.
- **AppTest**: `streamlit.testing.v1.AppTest.from_file('app.py').run()`으로 위젯을 조작하고 `session_state`·경고·toast를 확인. 빠르지만 브라우저에서만 일어나는 동작(연타 시 요청 순서, 붙여넣기, 실제 렌더링된 마크다운·자동 링크, 접근성 이름)은 재현하지 못함
- **Playwright MCP**: 실행 중인 앱을 실제 브라우저로 조작. 위 항목은 반드시 여기서 확인
  - 스크린샷은 프로젝트 폴더 안에만 저장 가능. 작업 후 자동 생성되는 `.playwright-mcp/` 폴더는 삭제
  - 체크박스 `<input>`은 화면에 숨겨져 있어 바로 클릭되지 않음. `locator('xpath=ancestor::label[1]')`로 감싼 라벨을 클릭
  - 동작마다 화면 전체를 다시 그리므로, 조작 후 잠깐 기다린 다음 확인. 다시 그리는 중에는 같은 요소가 2개 잡힐 수 있음

## 아키텍처
- 단일 파일 `app.py`. 상태는 `st.session_state["items"]`(아이템 dict 리스트)와 `["editing_id"]`(인라인 편집 중인 아이템 id, 동시에 하나만). 보조 상태: `flash`(콜백에서 만든 알림을 다음 렌더링에서 표시), `edit_error`, `last_added`(연타 감지용 (시각, 제출값))
- 아이템 필드: `id`(uuid4), `name`(최대 50자), `quantity`(1~999), `memo`(최대 100자), `checked`, `created_at`(ISO 8601). 제한값은 파일 상단 상수(`NAME_MAX_LENGTH` 등)
- 계층: 데이터 조작 함수(`add_item`, `update_item`, `delete_item`, `set_checked`, `clear_checked`, `clear_all`, `get_summary`) → 콜백(`on_add_submit`, `on_toggle`, `on_start_edit`, `on_save_edit`, `on_cancel_edit`) → 렌더링 함수(`render_header`, `render_input_form`, `render_item_list`, `render_footer_actions`). `main()`이 렌더링 함수를 순서대로 호출
- 유효성 검사는 `validate_item()` 한 곳에서만 함. 입력 위젯에 `max_chars`/`min_value`/`max_value`를 쓰지 않음(범위 밖 입력이 안내 없이 무시됨). 추가 폼과 편집 카드의 이름·수량 입력은 `render_name_quantity_inputs()`를 공유
- 추가 폼은 `clear_on_submit`을 쓰지 않고, 성공했을 때만 `on_add_submit()`에서 입력값을 비움(실패 시 입력 보존). 그래서 연타하면 입력창이 비기 전에 같은 값이 다시 제출될 수 있어, 1초(`DOUBLE_SUBMIT_WINDOW`) 안에 같은 값이나 빈 값이 다시 들어오면 무시함
- 전체 초기화 확인 체크(`confirm_clear_all`)는 목록이 비면 `render_footer_actions()`에서 해제
- 표시 순서: 미완료 먼저, 완료 나중. 같은 그룹 안에서는 `created_at` 순(초 단위라 같은 초는 추가 순서 유지)
- 저장: MVP는 session_state만 사용(새로고침하면 초기화). Streamlit Community Cloud는 파일 시스템이 영구적이지 않으므로 영구 저장은 외부 DB로 구현해야 함
- 배포: GitHub 저장소 → Streamlit Community Cloud. 절차는 `README.md`

## 구현 규칙
- 위젯 key는 반드시 아이템 id 기반(`f"check_{item['id']}"`)으로 고유하게 만들고, 상태 변경은 `on_click`/`on_change` 콜백에서 처리. 체크박스는 저장값을 뒤집지 말고 위젯 값을 그대로 대입(`on_toggle`)
- 마크다운으로 렌더링되는 곳(`st.markdown`, `st.caption`, `st.toast` 등)에 사용자 입력을 넣을 때는 반드시 `escape_markdown()`을 거칠 것(문장부호 이스케이프 + URL·이메일 자동 링크 차단). 예외: 위젯 `label`은 스크린리더가 읽는 이름이 되므로 원문 그대로 둠
- 버튼에 `icon=":material/..."`을 쓰지 말 것. 아이콘 이름("edit" 등)이 접근성 이름에 섞임
- 소스에 보이지 않는 문자를 직접 넣지 말고 `"\u200b"`처럼 이스케이프로 쓸 것. Edit·Write 도구는 `\u200b`를 실제 문자로 바꿔 저장하므로, 쓴 뒤 `od -c`로 바이트를 확인
- `unsafe_allow_html`과 커스텀 CSS 주입 금지. 스타일은 Streamlit 기본 기능과 `.streamlit/config.toml` 테마로만 처리
- 의존성은 `streamlit`과 표준 라이브러리만 사용. 최소 버전은 Streamlit 1.51(`requirements.txt`). 새 Streamlit API를 쓰면 그 API가 생긴 버전과 비교해 하한을 갱신할 것
- 모바일 폭(약 375px)에서 아이템 한 줄(체크박스 | 이름·수량·메모 | 수정 | 삭제)이 깨지지 않아야 함. `st.columns`는 좁은 화면에서 세로로 쌓이므로 한 줄로 유지할 곳은 `st.container(horizontal=True)`를 사용. 수정·삭제는 폭을 줄이려고 `type="tertiary"` 버튼 사용
- 테마는 `config.toml`의 `[theme.light]`/`[theme.dark]`로 모드별로 정의(`base`를 고정하지 않아 사용자가 모드를 선택 가능)
