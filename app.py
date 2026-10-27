"""쇼핑 리스트 Streamlit 앱.

요구사항은 PRD.md를 따른다. 데이터는 st.session_state에만 저장한다(MVP).
상태 변경은 모두 on_click / on_change 콜백에서 처리하여 rerun 시 화면이 꼬이지 않게 한다.
"""

import re
import string
import time
import uuid
from datetime import datetime

import streamlit as st

EMPTY_MESSAGE = "쇼핑 리스트가 비어 있어요. 아이템을 추가해 보세요!"
NAME_MAX_LENGTH = 50
MEMO_MAX_LENGTH = 100
QUANTITY_MIN = 1
QUANTITY_MAX = 999
# 추가 직후 이 시간(초) 안에 들어온 빈 제출은 버튼 연타로 보고 무시한다
DOUBLE_SUBMIT_WINDOW = 1.0

# 마크다운에서 특별한 의미를 갖는 ASCII 문장부호 (CommonMark는 모든 ASCII 문장부호의 백슬래시 이스케이프를 허용)
_MARKDOWN_SPECIAL = re.compile("([" + re.escape(string.punctuation) + "])")
# 백슬래시 이스케이프로 막히지 않는 GFM 자동 링크(URL, www., 이메일)의 시작 부분
_AUTOLINK_TRIGGER = re.compile(r"(?i)(https?|ftp|mailto|www)(?=[:.])|(?<=\S)(?=@)")
_ZERO_WIDTH_SPACE = "\u200b"


# ---------------------------------------------------------------------------
# 상태 초기화
# ---------------------------------------------------------------------------
def init_state():
    """세션 상태에 아이템 리스트와 편집 중인 아이템 id를 초기화한다."""
    if "items" not in st.session_state:
        st.session_state["items"] = []
    if "editing_id" not in st.session_state:
        st.session_state["editing_id"] = None
    if "flash" not in st.session_state:
        # 콜백에서 만든 알림을 다음 렌더링에서 보여주기 위한 임시 저장소: (종류, 메시지) 또는 None
        st.session_state["flash"] = None
    if "edit_error" not in st.session_state:
        st.session_state["edit_error"] = None
    if "last_added" not in st.session_state:
        # 연타 감지용: (추가 시각, (이름, 수량, 메모))
        st.session_state["last_added"] = (0.0, None)


# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------
def escape_markdown(text):
    """사용자 입력이 마크다운 서식이나 자동 링크로 해석되지 않도록 처리한다."""
    # 자동 링크 감지 지점에 폭 없는 공백을 넣어 링크로 바뀌지 않게 한다
    text = _AUTOLINK_TRIGGER.sub(lambda m: m.group(0) + _ZERO_WIDTH_SPACE, text)
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text)


def validate_item(name, quantity, memo=""):
    """이름, 수량, 메모를 검사한다. 문제가 있으면 오류 메시지를, 없으면 None을 반환한다."""
    if not name:
        return "아이템 이름을 입력해 주세요."
    if len(name) > NAME_MAX_LENGTH:
        return f"아이템 이름은 {NAME_MAX_LENGTH}자 이하로 입력해 주세요. (현재 {len(name)}자)"
    if not isinstance(quantity, int) or not QUANTITY_MIN <= quantity <= QUANTITY_MAX:
        return f"수량은 {QUANTITY_MIN}~{QUANTITY_MAX} 사이의 정수로 입력해 주세요."
    if len(memo) > MEMO_MAX_LENGTH:
        return f"메모는 {MEMO_MAX_LENGTH}자 이하로 입력해 주세요. (현재 {len(memo)}자)"
    return None


def find_item(item_id):
    """id로 아이템을 찾는다. 없으면 None을 반환한다."""
    for item in st.session_state["items"]:
        if item["id"] == item_id:
            return item
    return None


# ---------------------------------------------------------------------------
# 데이터 조작
# ---------------------------------------------------------------------------
def create_item(name, quantity=1, memo=""):
    """PRD 5장 데이터 모델에 맞는 새 아이템 dict를 만든다."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "quantity": quantity,
        "memo": memo,
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def add_item(name, quantity=1, memo=""):
    """유효성 검사를 거쳐 리스트에 아이템을 추가한다. 실패하면 오류 메시지를 반환한다."""
    name = name.strip()
    memo = memo.strip()
    error = validate_item(name, quantity, memo)
    if error:
        return error
    st.session_state["items"].append(create_item(name, quantity, memo))
    return None


def update_item(item_id, name, quantity, memo):
    """지정한 아이템의 이름, 수량, 메모를 수정한다. 실패하면 오류 메시지를 반환한다."""
    item = find_item(item_id)
    if item is None:
        return "수정할 아이템을 찾을 수 없어요."
    name = name.strip()
    memo = memo.strip()
    error = validate_item(name, quantity, memo)
    if error:
        return error
    item.update(name=name, quantity=quantity, memo=memo)
    return None


def delete_item(item_id):
    """지정한 아이템을 삭제한다."""
    st.session_state["items"] = [
        item for item in st.session_state["items"] if item["id"] != item_id
    ]
    if st.session_state["editing_id"] == item_id:
        st.session_state["editing_id"] = None
        st.session_state["edit_error"] = None


def set_checked(item_id, checked):
    """지정한 아이템의 구매 완료 상태를 설정한다."""
    item = find_item(item_id)
    if item is not None:
        item["checked"] = checked


def clear_checked():
    """구매 완료된 아이템을 모두 삭제한다."""
    checked_ids = {item["id"] for item in st.session_state["items"] if item["checked"]}
    st.session_state["items"] = [
        item for item in st.session_state["items"] if not item["checked"]
    ]
    if st.session_state["editing_id"] in checked_ids:
        st.session_state["editing_id"] = None
        st.session_state["edit_error"] = None


def clear_all():
    """리스트를 전부 비운다."""
    st.session_state["items"] = []
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = None


def get_summary():
    """전체, 남은, 완료 아이템 개수를 계산한다."""
    items = st.session_state["items"]
    done = sum(1 for item in items if item["checked"])
    return {"total": len(items), "remaining": len(items) - done, "done": done}


def get_sorted_items():
    """미완료 아이템을 위, 완료 아이템을 아래로 정렬한다. 같은 그룹은 생성 순서를 유지한다."""
    return sorted(
        st.session_state["items"],
        key=lambda item: (item["checked"], item["created_at"]),
    )


# ---------------------------------------------------------------------------
# 콜백 (위젯 이벤트 처리)
# ---------------------------------------------------------------------------
def on_add_submit():
    """입력 폼 제출 시 아이템을 추가하고 결과 알림을 남긴다.

    실패하면 입력값을 그대로 두어 사용자가 고쳐서 다시 제출할 수 있게 하고,
    성공했을 때만 입력창을 비운다.
    """
    raw_name = st.session_state["new_name"]
    submitted = (raw_name, st.session_state["new_quantity"], st.session_state["new_memo"])
    last_time, last_submitted = st.session_state["last_added"]
    # 연타로 들어온 제출은 직전과 같은 값이거나(입력창이 비워지기 전), 방금 비운 빈 값이므로 조용히 무시한다
    if time.monotonic() - last_time < DOUBLE_SUBMIT_WINDOW and (submitted == last_submitted or raw_name == ""):
        return
    name = raw_name.strip()
    error = add_item(name, st.session_state["new_quantity"], st.session_state["new_memo"])
    if error:
        st.session_state["flash"] = ("warning", error)
        return
    st.session_state["last_added"] = (time.monotonic(), submitted)
    st.session_state["flash"] = ("success", f"'{escape_markdown(name)}'을(를) 추가했어요.")
    st.session_state["new_name"] = ""
    st.session_state["new_quantity"] = 1
    st.session_state["new_memo"] = ""


def on_toggle(item_id):
    """체크박스 값을 그대로 아이템에 반영한다."""
    set_checked(item_id, st.session_state[f"check_{item_id}"])


def on_start_edit(item_id):
    """편집 모드로 전환하고 편집 입력값을 현재 아이템 값으로 채운다."""
    item = find_item(item_id)
    if item is None:
        return
    st.session_state["editing_id"] = item_id
    st.session_state["edit_error"] = None
    st.session_state[f"edit_name_{item_id}"] = item["name"]
    st.session_state[f"edit_quantity_{item_id}"] = item["quantity"]
    st.session_state[f"edit_memo_{item_id}"] = item["memo"]


def on_save_edit(item_id):
    """편집 내용을 저장한다. 검증에 실패하면 편집 모드를 유지한다."""
    error = update_item(
        item_id,
        st.session_state[f"edit_name_{item_id}"],
        st.session_state[f"edit_quantity_{item_id}"],
        st.session_state[f"edit_memo_{item_id}"],
    )
    if error:
        st.session_state["edit_error"] = error
        return
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = None
    st.session_state["flash"] = ("success", "수정했어요.")


def on_cancel_edit():
    """편집을 취소하고 원래 값을 유지한다."""
    st.session_state["editing_id"] = None
    st.session_state["edit_error"] = None


# ---------------------------------------------------------------------------
# 화면 렌더링
# ---------------------------------------------------------------------------
def render_name_quantity_inputs(name_key, quantity_key):
    """이름과 수량 입력란을 한 줄에 그린다.

    max_chars, min_value, max_value를 쓰면 범위를 벗어난 입력이 안내 없이 무시되므로,
    범위 검사는 validate_item()에 맡기고 경고 문구로 알려준다.
    """
    # st.columns는 좁은 화면에서 세로로 쌓이므로 가로 컨테이너로 한 줄을 유지한다
    with st.container(horizontal=True, vertical_alignment="bottom"):
        st.text_input(
            "아이템 이름",
            key=name_key,
            placeholder="예: 우유",
            help=f"최대 {NAME_MAX_LENGTH}자",
        )
        st.number_input(
            "수량",
            key=quantity_key,
            step=1,
            help=f"{QUANTITY_MIN}~{QUANTITY_MAX}",
            width=110,
        )


def render_header():
    """앱 제목과 요약 정보 영역을 그린다."""
    st.title("🛒 쇼핑 리스트")
    summary = get_summary()
    st.write(
        f"전체 {summary['total']}개 · 남은 {summary['remaining']}개 · 완료 {summary['done']}개"
    )
    if summary["total"] > 0:
        ratio = summary["done"] / summary["total"]
        st.progress(ratio, text=f"{ratio:.0%}")
        if summary["remaining"] == 0:
            st.success("모두 구매했어요! 🎉")


def render_input_form():
    """아이템 추가 입력 폼을 그린다. 이름과 수량은 한 줄, 메모는 아래 줄에 배치한다."""
    if "new_quantity" not in st.session_state:
        st.session_state["new_quantity"] = 1
    with st.form("add_form"):
        render_name_quantity_inputs("new_name", "new_quantity")
        st.text_input(
            "메모 (선택)",
            key="new_memo",
            placeholder="예: 저지방",
            help=f"최대 {MEMO_MAX_LENGTH}자",
        )
        st.form_submit_button("추가", type="primary", width="stretch", on_click=on_add_submit)

    flash = st.session_state["flash"]
    st.session_state["flash"] = None
    if flash:
        kind, message = flash
        if kind == "warning":
            st.warning(message)
        else:
            st.toast(message)


def render_item_row(item):
    """아이템 카드(보기 모드)를 그린다: [체크박스 | 이름 x수량 / 메모 | 수정 | 삭제]."""
    item_id = item["id"]
    name = escape_markdown(item["name"])
    quantity = f"x{item['quantity']}"
    with st.container(border=True):
        # 가로 컨테이너는 모바일 폭에서도 세로로 쌓이지 않아 한 줄 배치가 유지된다
        with st.container(horizontal=True, vertical_alignment="center"):
            # 라벨은 화면에 숨겨지고 스크린리더가 읽는 이름으로 쓰이므로 이스케이프하지 않은 원문을 넣는다
            st.checkbox(
                item["name"],
                key=f"check_{item_id}",
                value=item["checked"],
                on_change=on_toggle,
                args=(item_id,),
                label_visibility="collapsed",
            )
            with st.container(gap=None):
                if item["checked"]:
                    st.markdown(f":gray[~~{name}~~ :small[{quantity}]]")
                else:
                    st.markdown(f"**{name}** :small[:gray[{quantity}]]")
                if item["memo"]:
                    st.caption(escape_markdown(item["memo"]))
            # 아이콘(:material/...)은 접근성 이름에 "edit" 같은 글자로 섞이므로 텍스트 라벨만 쓴다.
            # 모바일 폭에서 한 줄에 들어가도록 여백이 적은 tertiary 버튼을 쓴다
            st.button("수정", key=f"edit_{item_id}", type="tertiary", on_click=on_start_edit, args=(item_id,))
            st.button("삭제", key=f"delete_{item_id}", type="tertiary", on_click=delete_item, args=(item_id,))


def render_edit_row(item):
    """아이템 카드(편집 모드)를 그린다."""
    item_id = item["id"]
    with st.container(border=True):
        render_name_quantity_inputs(f"edit_name_{item_id}", f"edit_quantity_{item_id}")
        st.text_input("메모 (선택)", key=f"edit_memo_{item_id}", help=f"최대 {MEMO_MAX_LENGTH}자")
        if st.session_state["edit_error"]:
            st.warning(st.session_state["edit_error"])
        with st.container(horizontal=True):
            st.button("저장", key=f"save_{item_id}", type="primary", width="stretch", on_click=on_save_edit, args=(item_id,))
            st.button("취소", key=f"cancel_{item_id}", width="stretch", on_click=on_cancel_edit)


def render_item_list():
    """아이템 목록을 그린다. 비어 있으면 안내 문구를 보여준다."""
    items = get_sorted_items()
    if not items:
        st.info(EMPTY_MESSAGE)
        return
    for item in items:
        if item["id"] == st.session_state["editing_id"]:
            render_edit_row(item)
        else:
            render_item_row(item)


def render_footer_actions():
    """완료 항목 삭제, 전체 초기화 버튼 영역을 그린다."""
    summary = get_summary()
    if summary["total"] == 0:
        # 리스트가 비면 확인 체크를 해제해, 다음에 초기화할 때 다시 확인받게 한다
        st.session_state["confirm_clear_all"] = False
    st.divider()
    st.button(
        "완료 항목 모두 삭제",
        icon="🧹",
        width="stretch",
        help="체크한 아이템만 삭제",
        on_click=clear_checked,
        disabled=summary["done"] == 0,
    )
    with st.expander("전체 초기화", icon="⚠️"):
        confirmed = st.checkbox(
            "정말 전체를 삭제할까요?",
            key="confirm_clear_all",
            disabled=summary["total"] == 0,
        )
        st.button(
            "전체 초기화",
            width="stretch",
            help="리스트의 모든 아이템 삭제",
            on_click=clear_all,
            disabled=summary["total"] == 0 or not confirmed,
        )
    st.caption("새로고침하면 리스트가 초기화됩니다.")


def main():
    st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")
    init_state()
    render_header()
    render_input_form()
    render_item_list()
    render_footer_actions()


if __name__ == "__main__":
    main()
