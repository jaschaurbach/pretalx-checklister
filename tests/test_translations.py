import pytest
from django.utils.translation import gettext, override


def test_plugin_texts_are_translated_to_german():
    with override("de"):
        assert gettext("There is crucial information for you.") == (
            "Es gibt wichtige Informationen für dich."
        )
        assert gettext("Speaker Checklist") == "Checkliste für Vortragende"
        assert gettext("Checkboxes confirmed") == "Checkboxen bestätigt"


def test_english_is_the_default():
    with override("en"):
        assert gettext("Checkboxes confirmed") == "Checkboxes confirmed"


@pytest.mark.django_db
def test_speaker_pages_are_shown_in_german(speaker_client, event, block, make_talk):
    event.locales = ["en", "de"]
    event.save()
    make_talk("accepted")
    response = speaker_client.get(f"/{event.slug}/me/submissions/notes?lang=de")
    content = response.content.decode()
    assert "Wichtige Informationen" in content
    assert "Ich habe dies gelesen und verstanden." in content
    assert "Important information" not in content
