import pytest
from django_scopes import scopes_disabled
from pretalx_rt.models import EventSettings

from pretalx.event.domain.plugins import disable_plugin

from pretalx_checklister.rt import (
    mailto_for_ticket,
    rt_active,
    rt_installed,
    ticket_for_submission,
)


@pytest.mark.django_db
def test_rt_installed(event):
    assert rt_installed()


def test_rt_not_installed(no_rt):
    assert not rt_installed()


@pytest.mark.django_db
def test_rt_active_for_event_with_rt_enabled(event):
    assert rt_active(event)


@pytest.mark.django_db
def test_rt_not_active_for_event_without_rt_enabled(event):
    with scopes_disabled():
        disable_plugin(event, "pretalx_rt")
    assert not rt_active(event)


def test_rt_not_active_without_event():
    assert not rt_active(None)


@pytest.mark.django_db
def test_rt_not_active_if_not_installed(event, no_rt):
    assert not rt_active(event)


@pytest.mark.django_db
def test_ticket_for_submission(event, make_talk):
    submission = make_talk("accepted", rt_id=4711)
    with scopes_disabled():
        assert ticket_for_submission(submission).rt_id == 4711


@pytest.mark.django_db
def test_no_ticket_for_submission_without_ticket(event, make_talk):
    submission = make_talk("accepted", with_ticket=False)
    with scopes_disabled():
        assert ticket_for_submission(submission) is None


@pytest.mark.django_db
def test_no_ticket_if_rt_is_not_installed(event, make_talk, no_rt):
    submission = make_talk("accepted", rt_id=4711)
    assert ticket_for_submission(submission) is None


@pytest.mark.django_db
def test_mailto_from_queue_host_ticket_and_title(event, make_talk):
    submission = make_talk("accepted", rt_id=137864, title="My talk")
    with scopes_disabled():
        EventSettings.objects.filter(event=event).update(
            base_url="https://rt.cccv.de/", queue="speakers"
        )
        link = mailto_for_ticket(submission.rt_ticket, submission)
    assert link == (
        "mailto:speakers@cccv.de?subject=%5Brt.cccv.de%20%23137864%5D%20-%20My%20talk"
    )


@pytest.mark.django_db
def test_mailto_encodes_special_characters(event, make_talk):
    submission = make_talk("accepted", rt_id=1, title="Q&A: 100% (new)?")
    with scopes_disabled():
        EventSettings.objects.filter(event=event).update(queue="Talks & More")
        link = mailto_for_ticket(submission.rt_ticket, submission)
    assert link.startswith("mailto:Talks%20%26%20More@cccv.de?subject=")
    assert "Q%26A%3A%20100%25%20%28new%29%3F" in link
    assert "&" not in link.split("?", 1)[1]


@pytest.mark.django_db
def test_no_mailto_without_rt_settings(event, make_talk):
    submission = make_talk("accepted")
    with scopes_disabled():
        EventSettings.objects.filter(event=event).delete()
        assert mailto_for_ticket(submission.rt_ticket, submission) == ""
