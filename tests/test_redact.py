from app.services.redact import apply_redactions


def test_apply_redactions_replaces_spans_with_category_labels():
    text = "Meera Kalra called from 98765 43210 today"
    spans = [(0, 11, "Person"), (24, 11, "PhoneNumber")]
    assert apply_redactions(text, spans) == "[PERSON] called from [PHONENUMBER] today"


def test_apply_redactions_merges_overlapping_spans_into_one_label():
    assert apply_redactions("Meera Kalra spoke", [(0, 11, "Person"), (6, 5, "Person")]) == "[PERSON] spoke"


def test_apply_redactions_with_no_spans_returns_text_unchanged():
    assert apply_redactions("nothing sensitive here", []) == "nothing sensitive here"


def test_apply_redactions_keeps_devanagari_text_intact_around_span():
    text = "मेरा नाम मीरा कालरा है"
    start = text.index("मीरा")
    assert apply_redactions(text, [(start, len("मीरा कालरा"), "Person")]) == "मेरा नाम [PERSON] है"
