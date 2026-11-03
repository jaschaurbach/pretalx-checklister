import pytest
from django.urls import reverse
from django_scopes import scopes_disabled
from pretalx_rt.models import EventSettings

from pretalx_checklister.models import InfoBlock
from pretalx_checklister.speaker import boxes_for_user


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


@pytest.fixture
def rt_settings(event):
    with scopes_disabled():
        return EventSettings.objects.create(
            event=event, base_url="https://rt.cccv.de/", rest_auth_token="x", queue="q"
        )


@pytest.mark.django_db
def test_list_page_links_to_the_preview(orga_client, event, block):
    content = orga_client.get(block_url("settings", event)).content.decode()
    assert f'href="{block_url("preview", event)}"' in content


@pytest.mark.django_db
def test_list_page_without_boxes_has_no_preview_link(orga_client, event):
    content = orga_client.get(block_url("settings", event)).content.decode()
    assert block_url("preview", event) not in content


@pytest.mark.django_db
def test_preview_shows_the_speaker_page_with_example_values(
    orga_client, event, block, rt_settings
):
    response = orga_client.get(block_url("preview", event))
    content = response.content.decode()
    assert response.status_code == 200
    assert "Preview:" in content
    assert "Back to the Speaker Checklist" not in content
    assert "Ticket-Box" in content
    assert "ticket 12345" in content
    assert (
        "mailto:q@cccv.de?subject=%5Brt.cccv.de%20%2312345%5D%20-%20Example%20talk"
        in content
    )
    assert "{rt_ticket_id}" not in content
    assert 'name="read_' in content
    assert "disabled" in content
    assert 'type="submit"' not in content.split("Preview:", 1)[1].split("</main>")[0]


@pytest.mark.django_db
def test_preview_without_boxes(orga_client, event):
    content = orga_client.get(block_url("preview", event)).content.decode()
    assert "There is currently no information for you." in content


@pytest.mark.django_db
def test_preview_is_only_for_organisers(review_client, event, block):
    assert review_client.get(block_url("preview", event)).status_code == 404


@pytest.mark.django_db
def test_preview_needs_rt(orga_client, event, block, no_rt):
    assert orga_client.get(block_url("preview", event)).status_code == 404


def titles(event):
    with scopes_disabled():
        return [str(b.title) for b in InfoBlock.objects.filter(event=event)]


@pytest.fixture
def three_blocks(event):
    """Three boxes created without an order, as boxes were before ordering."""
    with scopes_disabled():
        return [
            InfoBlock.objects.create(event=event, title=title, text="x")
            for title in ("A", "B", "C")
        ]


@pytest.mark.django_db
def test_new_box_is_added_at_the_end(orga_client, event, three_blocks):
    orga_client.post(block_url("block.new", event), {"title_0": "D", "text_0": "x"})
    assert titles(event) == ["A", "B", "C", "D"]
    orga_client.post(block_url("block.new", event), {"title_0": "E", "text_0": "x"})
    assert titles(event) == ["A", "B", "C", "D", "E"]


@pytest.mark.django_db
def test_first_box_of_an_event(orga_client, event):
    orga_client.post(block_url("block.new", event), {"title_0": "A", "text_0": "x"})
    assert titles(event) == ["A"]


@pytest.mark.django_db
def test_editing_a_box_keeps_its_place(orga_client, event, three_blocks):
    orga_client.post(
        block_url("block.edit", event, pk=three_blocks[0].pk),
        {"title_0": "A2", "text_0": "x"},
    )
    assert titles(event) == ["A2", "B", "C"]


@pytest.mark.django_db
def test_move_a_box_up(orga_client, event, three_blocks):
    response = orga_client.post(
        block_url("block.move", event, pk=three_blocks[2].pk, direction="up")
    )
    assert response.status_code == 302
    assert titles(event) == ["A", "C", "B"]


@pytest.mark.django_db
def test_move_a_box_down(orga_client, event, three_blocks):
    orga_client.post(
        block_url("block.move", event, pk=three_blocks[0].pk, direction="down")
    )
    assert titles(event) == ["B", "A", "C"]


@pytest.mark.django_db
def test_move_the_first_box_up_and_the_last_box_down_changes_nothing(
    orga_client, event, three_blocks
):
    orga_client.post(
        block_url("block.move", event, pk=three_blocks[0].pk, direction="up")
    )
    orga_client.post(
        block_url("block.move", event, pk=three_blocks[2].pk, direction="down")
    )
    assert titles(event) == ["A", "B", "C"]


@pytest.mark.django_db
def test_move_unknown_box_is_not_found(orga_client, event, three_blocks):
    url = block_url("block.move", event, pk=three_blocks[2].pk + 1, direction="up")
    assert orga_client.post(url).status_code == 404


@pytest.mark.django_db
def test_move_needs_post(orga_client, event, three_blocks):
    url = block_url("block.move", event, pk=three_blocks[1].pk, direction="up")
    assert orga_client.get(url).status_code == 405
    assert titles(event) == ["A", "B", "C"]


@pytest.mark.django_db
def test_move_is_only_for_organisers(review_client, event, three_blocks):
    url = block_url("block.move", event, pk=three_blocks[1].pk, direction="up")
    assert review_client.post(url).status_code == 404
    assert titles(event) == ["A", "B", "C"]


@pytest.mark.django_db
def test_move_needs_rt(orga_client, event, three_blocks, no_rt):
    url = block_url("block.move", event, pk=three_blocks[1].pk, direction="up")
    assert orga_client.post(url).status_code == 404


@pytest.mark.django_db
def test_list_page_shows_the_order_and_move_buttons(orga_client, event, three_blocks):
    content = orga_client.get(block_url("settings", event)).content.decode()
    assert content.index(">A<") < content.index(">B<") < content.index(">C<")
    assert (
        block_url("block.move", event, pk=three_blocks[1].pk, direction="up") in content
    )
    assert "Speakers see the boxes in this order." in content
    # the first box cannot move up, the last one cannot move down
    assert content.count("disabled") == 2


@pytest.mark.django_db
def test_speakers_see_the_boxes_in_the_new_order(
    orga_client, speaker_user, event, three_blocks, make_talk
):
    make_talk("accepted")

    def speaker_order():
        with scopes_disabled():
            return [str(b["title"]) for b in boxes_for_user(event, speaker_user)]

    assert speaker_order() == ["A", "B", "C"]
    orga_client.post(
        block_url("block.move", event, pk=three_blocks[2].pk, direction="up")
    )
    assert speaker_order() == ["A", "C", "B"]
