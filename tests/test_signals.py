import pytest
from django_scopes import scopes_disabled


@pytest.mark.django_db
def test_speaker_list_has_no_column_without_boxes(orga_client, event, make_talk):
    make_talk("accepted")
    content = orga_client.get(f"/orga/event/{event.slug}/speakers/").content.decode()
    assert "speakers_column.js" not in content


@pytest.mark.django_db
def test_speaker_list_has_no_column_without_accepted_talks(
    orga_client, event, block, make_talk
):
    make_talk("submitted")
    content = orga_client.get(f"/orga/event/{event.slug}/speakers/").content.decode()
    assert "speakers_column.js" not in content


@pytest.mark.django_db
def test_compose_link_has_no_template_if_it_was_deleted(
    orga_client, speaker_user, event, block, make_talk
):
    make_talk("accepted")
    code = speaker_user.get_speaker(event).code
    with scopes_disabled():
        event.mail_templates.filter(role__isnull=True).delete()
    content = orga_client.get(
        f"/orga/event/{event.slug}/mails/compose/sessions/"
    ).content.decode()
    assert f"?speakers={code}" in content
    assert "template=" not in content
