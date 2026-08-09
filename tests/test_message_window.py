from backend.app.orchestrator import slice_messages_for_payload


def test_slice_messages_full_when_under_window():
    msgs = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    tail, total, offset, assistants = slice_messages_for_payload(msgs, 80)
    assert tail == msgs
    assert total == 2
    assert offset == 0
    assert assistants == 1


def test_slice_messages_tail_and_counts():
    msgs = [{"role": "assistant", "content": str(i)} for i in range(100)]
    tail, total, offset, assistants = slice_messages_for_payload(msgs, 30)
    assert total == 100
    assert offset == 70
    assert len(tail) == 30
    assert tail[0]["content"] == "70"
    assert assistants == 100
