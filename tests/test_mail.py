import pytest
from django_scopes import scopes_disabled

from pretalx.mail.domain.render import render_template_to_mail

from pretalx_checklister.mail import (
    NEW,
    SETTINGS_KEY,
    UNREAD,
    ensure_mail_templates,
    template_pk,
)
from pretalx_checklister.signals import pretalx_checklister_mail_placeholders


@pytest.mark.django_db
def test_mail_templates_created_on_install(event):
    with scopes_disabled():
        event.mail_templates.filter(role__isnull=True).delete()
        event.settings.delete("pretalx_checklister_mail_templates")
        ensure_mail_templates(event)
        templates = event.mail_templates.filter(role__isnull=True)
        subjects = [str(template.subject) for template in templates]
        assert any("crucial information" in subject for subject in subjects)
        assert any("New information" in subject for subject in subjects)
        assert all("{notes_url}" in str(template.text) for template in templates)
        # opening the checklist page does not create them again
        ensure_mail_templates(event)
        assert event.mail_templates.filter(role__isnull=True).count() == 2


@pytest.mark.django_db
def test_mail_templates_created_when_opening_the_page(orga_client, event):
    with scopes_disabled():
        event.mail_templates.filter(role__isnull=True).delete()
        event.settings.delete("pretalx_checklister_mail_templates")
    orga_client.get(f"/orga/event/{event.slug}/settings/p/pretalx_checklister/")
    with scopes_disabled():
        assert event.mail_templates.filter(role__isnull=True).count() == 2


@pytest.mark.django_db
def test_mail_templates_render_notes_url(event, speaker_user):
    with scopes_disabled():
        for template in event.mail_templates.filter(role__isnull=True):
            mail = render_template_to_mail(
                template, context_kwargs={"user": speaker_user, "event": event}
            )
            assert f"/{event.slug}/me/submissions/notes" in mail.text
            assert "{" not in mail.text


@pytest.mark.django_db
def test_without_rt_no_mail_templates_or_placeholder(event, no_rt):
    with scopes_disabled():
        event.mail_templates.filter(role__isnull=True).delete()
        event.settings.delete("pretalx_checklister_mail_templates")
        ensure_mail_templates(event)
        assert not event.mail_templates.filter(role__isnull=True).exists()
    assert pretalx_checklister_mail_placeholders(event) == []


@pytest.fixture
def templates(event):
    """The two templates the plugin created, by key."""
    with scopes_disabled():
        return {
            UNREAD: event.mail_templates.get(subject__icontains="crucial information"),
            NEW: event.mail_templates.get(subject__icontains="New information"),
        }


@pytest.mark.django_db
def test_template_pk_finds_the_created_templates(event, templates):
    with scopes_disabled():
        assert template_pk(event, UNREAD) == templates[UNREAD].pk
        assert template_pk(event, NEW) == templates[NEW].pk


@pytest.mark.django_db
def test_template_pk_is_none_after_the_template_was_deleted(event, templates):
    with scopes_disabled():
        templates[UNREAD].delete()
        assert template_pk(event, UNREAD) is None
        assert template_pk(event, NEW) == templates[NEW].pk


@pytest.mark.django_db
def test_template_pk_finds_templates_by_subject_if_no_pk_was_stored(event, templates):
    with scopes_disabled():
        for key in (UNREAD, NEW):
            event.settings.delete(f"{SETTINGS_KEY}_{key}")
        assert template_pk(event, UNREAD) == templates[UNREAD].pk
        assert template_pk(event, NEW) == templates[NEW].pk


@pytest.mark.django_db
def test_template_pk_is_none_if_nothing_is_found(event, templates):
    with scopes_disabled():
        for key in (UNREAD, NEW):
            event.settings.delete(f"{SETTINGS_KEY}_{key}")
        event.mail_templates.filter(role__isnull=True).delete()
        assert template_pk(event, UNREAD) is None
