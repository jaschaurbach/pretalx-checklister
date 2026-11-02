import pytest
from django.urls import reverse
from django_scopes import scopes_disabled

from pretalx_checklister.models import InfoBlock


def block_url(name, event, **kwargs):
    return reverse(
        f"plugins:pretalx_checklister:{name}", kwargs={"event": event.slug, **kwargs}
    )


@pytest.mark.django_db
def test_orga_sees_existing_block_in_edit_form(orga_client, event, block):
    response = orga_client.get(block_url("block.edit", event, pk=block.pk))
    assert response.status_code == 200
    assert "Ticket-Box" in response.content.decode()


@pytest.mark.django_db
def test_orga_can_edit_a_block(orga_client, event, block):
    response = orga_client.post(
        block_url("block.edit", event, pk=block.pk),
        {"title_0": "New title", "text_0": "New"},
    )
    assert response.status_code == 302
    with scopes_disabled():
        block.refresh_from_db()
        assert str(block.title) == "New title"
        assert InfoBlock.objects.filter(event=event).count() == 1


@pytest.mark.django_db
def test_edit_unknown_block_is_not_found(orga_client, event, block):
    response = orga_client.get(block_url("block.edit", event, pk=block.pk + 1))
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_unknown_block_is_not_found(orga_client, event, block):
    response = orga_client.post(block_url("block.delete", event, pk=block.pk + 1))
    assert response.status_code == 404
    with scopes_disabled():
        assert InfoBlock.objects.filter(pk=block.pk).exists()


@pytest.mark.django_db
def test_notes_page_is_not_found_if_the_event_is_not_public(
    speaker_client, event, block, make_talk
):
    make_talk("accepted")
    event.is_public = False
    event.save()
    response = speaker_client.get(f"/{event.slug}/me/submissions/notes")
    assert response.status_code == 404
