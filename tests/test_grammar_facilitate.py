"""Workbook grammar: full dialogues — listen fixed lines, fill/choose blanks."""

from backend.app import lesson_flow as flow


def test_l04_includes_listen_turns_for_non_blank_lines():
    drills = flow.grammar_drills("L04")
    kinds = [(d.get("point"), (d.get("turn") or {}).get("kind")) for d in drills if d.get("facilitate")]
    listen = [k for k in kinds if k[1] == "listen"]
    fill = [k for k in kinds if k[1] == "fill"]
    choose = [k for k in kinds if k[1] == "choose"]
    # Every numbered dialogue is expanded; fixed lines are listen steps.
    assert len(listen) >= 15, len(listen)
    assert len(fill) == 14, len(fill)  # と×2 + 住む×7 + の×5
    assert len(choose) == 5, len(choose)
    assert len(kinds) == len(listen) + len(fill) + len(choose)


def test_l04_to_item1_has_follow_listen():
    drills = flow.grammar_drills("L04")
    # ❶-1: fill then B’s fixed reply
    first = drills[0]
    second = drills[1]
    assert (first.get("turn") or {}).get("kind") == "fill"
    jp, _en, step = flow.grammar_item(first, 0, len(drills))
    assert step["book_substep"] == "grammar_fill"
    assert (second.get("turn") or {}).get("kind") == "listen"
    jp2, _en2, step2 = flow.grammar_item(second, 1, len(drills))
    assert step2["book_substep"] == "grammar_listen"
    assert "タンです" in jp2
    assert step2["auto_advance_after_audio"] is True


def test_l04_interrogative_multi_listen_then_choose():
    drills = flow.grammar_drills("L04")
    # ❷-3 starts with お名前は？
    idx = next(
        i
        for i, d in enumerate(drills)
        if (d.get("turn") or {}).get("jp") == "お名前は？"
    )
    sequence = [(d.get("turn") or {}).get("kind") for d in drills[idx : idx + 4]]
    assert sequence == ["listen", "listen", "listen", "choose"]


def test_legacy_flat_exercise_expands_partner_then_fill_then_follow():
    ex = {
        "partner_jp": "これ、だれですか？",
        "cue_jp": "兄｜子ども",
        "blank_prompt_jp": "＿。",
        "answers": ["兄の子どもです"],
        "follow_jp": "かわいいですね。",
    }
    turns = flow.grammar_turns(ex)
    assert [t["kind"] for t in turns] == ["listen", "fill", "listen"]
    assert turns[0]["jp"] == "これ、だれですか？"
    assert turns[2]["jp"] == "かわいいですね。"
