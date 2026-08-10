"""VOICEVOX text prep — especially は as /ha/ vs particle /wa/."""

from backend.app.speech.text import force_lexical_ha, prepare_for_voicevox, speakable_text


def test_mother_haha_not_wawa():
    assert force_lexical_ha("はは") == "ハハ"
    assert force_lexical_ha("ははです") == "ハハです"
    assert prepare_for_voicevox("はは") == "ハハ"


def test_eight_hachi_not_wachi():
    assert force_lexical_ha("はち") == "ハチ"
    assert force_lexical_ha("じゅうはち") == "じゅうハチ"
    assert force_lexical_ha("にじゅうはち") == "にじゅうハチ"


def test_topic_particle_ha_left_alone():
    # Particle は stays hiragana so VOICEVOX keeps /wa/.
    assert force_lexical_ha("わたしは学生です") == "わたしは学生です"
    assert force_lexical_ha("これは本です") == "これは本です"
    # Lexical mother after a particle topic still forced to /ha/.
    assert force_lexical_ha("わたしはははです") == "わたしはハハです"


def test_speakable_applies_ha_fix():
    assert "ハハ" in speakable_text("リナさん、ははです")
