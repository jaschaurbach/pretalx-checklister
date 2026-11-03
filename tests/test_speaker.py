import pytest
from django_scopes import scopes_disabled

from pretalx.person.models import SpeakerProfile

from pretalx_checklister.models import Acknowledgement, InfoBlock
from pretalx_checklister.speaker import (
    acknowledgement_status,
    all_acknowledged,
    boxes_for_user,
    new_box,
    preview_boxes,
    speaker_groups,
)


def box(pk, acknowledged):
    return {"block": InfoBlock(pk=pk), "acknowledged": acknowledged}


@pytest.fixture
def newer_block(event, block):
    with scopes_disabled():
        return InfoBlock.objects.create(event=event, title="Newer", text="y")


@pytest.fixture
def managed_speaker(event):
    with scopes_disabled():
        return SpeakerProfile.objects.create(event=event, name="Managed")


# boxes_for_user


@pytest.mark.django_db
def test_boxes_for_user_without_boxes(event, speaker_user, make_talk):
    make_talk("accepted")
    with scopes_disabled():
        assert boxes_for_user(event, speaker_user) == []


@pytest.mark.django_db
def test_boxes_for_user_without_user(event, block, make_talk):
    make_talk("accepted")
    with scopes_disabled():
        assert boxes_for_user(event, None) == []


@pytest.mark.django_db
def test_boxes_for_user_without_accepted_talk(event, speaker_user, block, make_talk):
    make_talk("submitted")
    with scopes_disabled():
        assert boxes_for_user(event, speaker_user) == []


@pytest.mark.django_db
def test_boxes_for_user_marks_confirmed_boxes(
    event, speaker_user, block, newer_block, make_talk
):
    make_talk("accepted")
    with scopes_disabled():
        Acknowledgement.objects.create(block=block, user=speaker_user)
        boxes = boxes_for_user(event, speaker_user)
    assert [(b["block"], b["acknowledged"]) for b in boxes] == [
        (block, True),
        (newer_block, False),
    ]


# all_acknowledged / new_box


def test_all_acknowledged():
    assert all_acknowledged([box(1, True), box(2, True)])
    assert not all_acknowledged([box(1, True), box(2, False)])
    assert not all_acknowledged([])


def test_new_box_is_none_on_first_visit():
    assert new_box([box(1, False), box(2, False)]) is None


def test_new_box_is_none_if_everything_is_confirmed():
    assert new_box([box(1, True), box(2, True)]) is None


def test_new_box_is_none_if_the_newest_box_is_the_first_one():
    assert new_box([box(3, False), box(1, True)]) is None


def test_new_box_is_the_newest_unconfirmed_box():
    boxes = [box(1, True), box(2, False), box(3, False)]
    assert new_box(boxes) is boxes[2]


# acknowledgement_status


@pytest.mark.django_db
def test_status_without_boxes(event, make_talk):
    make_talk("accepted")
    with scopes_disabled():
        assert acknowledgement_status(event) == {}


@pytest.mark.django_db
def test_status_per_speaker(event, speaker_user, block, newer_block, make_talk):
    make_talk("accepted")
    code = speaker_user.get_speaker(event).code
    with scopes_disabled():
        assert acknowledgement_status(event) == {code: False}
        Acknowledgement.objects.create(block=block, user=speaker_user)
        assert acknowledgement_status(event) == {code: False}
        Acknowledgement.objects.create(block=newer_block, user=speaker_user)
        assert acknowledgement_status(event) == {code: True}


@pytest.mark.django_db
def test_status_ignores_speakers_without_account(
    event, speaker_user, block, make_talk, managed_speaker
):
    submission = make_talk("accepted")
    with scopes_disabled():
        submission.speakers.add(managed_speaker)
        status = acknowledgement_status(event)
    assert list(status) == [speaker_user.get_speaker(event).code]


# speaker_groups


@pytest.mark.django_db
def test_groups_without_boxes(event, make_talk):
    make_talk("accepted")
    with scopes_disabled():
        assert speaker_groups(event) == {"unread": [], "new": []}


@pytest.mark.django_db
def test_groups_count_a_speaker_with_several_talks_once(
    event, speaker_user, block, make_talk
):
    make_talk("accepted", title="First talk")
    make_talk("confirmed", title="Second talk")
    code = speaker_user.get_speaker(event).code
    with scopes_disabled():
        assert speaker_groups(event) == {"unread": [code], "new": []}


@pytest.mark.django_db
def test_groups_ignore_speakers_without_account(
    event, speaker_user, block, make_talk, managed_speaker
):
    submission = make_talk("accepted")
    with scopes_disabled():
        submission.speakers.add(managed_speaker)
        groups = speaker_groups(event)
    assert groups == {"unread": [speaker_user.get_speaker(event).code], "new": []}


# preview_boxes


@pytest.mark.django_db
def test_preview_boxes_use_example_values(event, block):
    with scopes_disabled():
        boxes = preview_boxes(event)
    assert [b["block"] for b in boxes] == [block]
    assert "ticket 12345" in boxes[0]["text"]
    assert not boxes[0]["acknowledged"]
