import datetime as dt

import pytest
from django.core import management
from django_scopes import scopes_disabled
from pretalx_rt.models import EventSettings, Ticket

from pretalx.event.domain.event import initialise_event
from pretalx.event.domain.plugins import enable_plugin
from pretalx.event.models import Event, Organiser, Team
from pretalx.person.models import User
from pretalx.submission.models import Submission, SubmissionType

from pretalx_checklister import rt
from pretalx_checklister.models import InfoBlock


@pytest.fixture(scope="session", autouse=True)
def collect_static(request):
    management.call_command("collectstatic", "--noinput", "--clear")


@pytest.fixture(autouse=True)
def no_rt_server(monkeypatch):
    """pretalx-rt is enabled on the test event but must never contact a server."""
    monkeypatch.setattr("pretalx_rt.signals.is_enabled", lambda event: False)


@pytest.fixture
def organiser():
    with scopes_disabled():
        o = Organiser.objects.create(name="Super Organiser", slug="superorganiser")
        Team.objects.create(
            name="Organisers",
            organiser=o,
            can_create_events=True,
            can_change_teams=True,
            can_change_organiser_settings=True,
            can_change_event_settings=True,
            can_change_submissions=True,
        )
        Team.objects.create(name="Reviewers", organiser=o, is_reviewer=True)
    return o


@pytest.fixture
def event(organiser):
    today = dt.date.today()
    with scopes_disabled():
        event = Event.objects.create(
            name="Fancy testevent",
            is_public=True,
            slug="test",
            email="orga@orga.org",
            date_from=today,
            date_to=today + dt.timedelta(days=3),
            organiser=organiser,
        )
        initialise_event(event)
        enable_plugin(event, "pretalx_rt")
        enable_plugin(event, "pretalx_checklister")
        event.save()
        for team in organiser.teams.all():
            team.limit_events.add(event)
    return event


@pytest.fixture
def orga_user(event):
    with scopes_disabled():
        user = User.objects.create_user(
            password="orgapassw0rd", email="orgauser@orga.org", name="Orga User"
        )
        team = event.organiser.teams.filter(
            can_change_organiser_settings=True, is_reviewer=False
        ).first()
        team.members.add(user)
        team.save()
    return user


@pytest.fixture
def review_user(event):
    with scopes_disabled():
        user = User.objects.create_user(
            password="reviewpassw0rd", email="reviewuser@orga.org", name="Review User"
        )
        team = event.organiser.teams.filter(
            can_change_organiser_settings=False, is_reviewer=True
        ).first()
        team.members.add(user)
        team.save()
    return user


@pytest.fixture
def orga_client(orga_user, client):
    client.force_login(orga_user)
    return client


@pytest.fixture
def review_client(review_user, client):
    client.force_login(review_user)
    return client


@pytest.fixture
def speaker_user(event):
    with scopes_disabled():
        return User.objects.create_user(
            password="speakerpassw0rd", email="speaker@example.org", name="Speaker"
        )


@pytest.fixture
def speaker_client(speaker_user, client):
    client.force_login(speaker_user)
    return client


@pytest.fixture
def make_talk(event, speaker_user):
    """Create a proposal of ``speaker_user`` in the given state, with a fake
    RT ticket (no RT server involved)."""

    counter = iter(range(4200, 5000))

    def _make(state, rt_id=None, title="A talk", with_ticket=True):
        with scopes_disabled():
            EventSettings.objects.get_or_create(
                event=event,
                defaults={
                    "base_url": "https://rt.example.invalid/",
                    "rest_auth_token": "x",
                    "queue": "Talks",
                },
            )
            submission = Submission.objects.create(
                event=event,
                title=title,
                state=state,
                submission_type=SubmissionType.objects.filter(event=event).first(),
            )
            submission.speakers.add(speaker_user.get_speaker(event))
            if with_ticket:
                Ticket.objects.create(
                    event=event,
                    submission=submission,
                    rt_id=rt_id or next(counter),
                    subject=title,
                    status="open",
                    queue="Talks",
                )
        return submission

    return _make


@pytest.fixture
def no_rt(monkeypatch):
    monkeypatch.setattr(rt, "Ticket", None)
    monkeypatch.setattr(rt, "EventSettings", None)


@pytest.fixture
def block(event):
    """An information box that uses the placeholders."""
    with scopes_disabled():
        return InfoBlock.objects.create(
            event=event,
            title="Ticket-Box",
            text="[Write us]({rt_mailto}) ticket {rt_ticket_id}",
        )
