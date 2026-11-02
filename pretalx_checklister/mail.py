from django.utils.translation import gettext_lazy as _

from pretalx.mail.domain.placeholders import LinkMailTextPlaceholder

from .rt import rt_active

SETTINGS_KEY = "pretalx_checklister_mail_templates"
UNREAD, NEW = "unread", "new"
_SUBJECT_HINTS = {UNREAD: "crucial information for", NEW: "New information for"}

TEMPLATES = (
    {
        "subject": {
            "en": "Please read the crucial information for {event_name}",
            "de": "Bitte lies die wichtigen Informationen für {event_name}",
        },
        "text": {
            "en": (
                "Hello {name},\n\n"
                "there is crucial information for you as a speaker at {event_name} "
                "that you have not confirmed yet. Please read it and confirm "
                "it here:\n\n{notes_url}\n\nThank you!"
            ),
            "de": (
                "Hallo {name},\n\n"
                "es gibt wichtige Informationen für dich als Speaker bei {event_name}, "
                "die du noch nicht bestätigt hast. Bitte lies sie und bestätige "
                "sie hier:\n\n{notes_url}\n\nVielen Dank!"
            ),
        },
    },
    {
        "subject": {
            "en": "New information for {event_name}",
            "de": "Neue Informationen für {event_name}",
        },
        "text": {
            "en": (
                "Hello {name},\n\n"
                "there is new information for you as a speaker at {event_name}. "
                "Please visit:\n\n{notes_url}\n\nThank you!"
            ),
            "de": (
                "Hallo {name},\n\n"
                "es gibt neue Informationen für dich als Speaker bei {event_name}. "
                "Bitte besuche:\n\n{notes_url}\n\nVielen Dank!"
            ),
        },
    },
)


def notes_placeholders():
    return LinkMailTextPlaceholder(
        "notes_url",
        ["event", "user"],
        lambda event, user: event.urls.user_submissions.full() + "notes",
        "https://pretalx.example.com/democon/me/submissions/notes",
        _("URL to the page with the crucial information for speakers"),
    )


def ensure_mail_templates(event):
    """Create the two mail templates once per event. They are normal
    templates afterwards, so organisers can edit or delete them."""
    if not rt_active(event) or event.settings.get(
        SETTINGS_KEY, as_type=bool, default=False
    ):
        return
    for key, template in zip((UNREAD, NEW), TEMPLATES, strict=True):
        created = event.mail_templates.create(**template)
        event.settings.set(f"{SETTINGS_KEY}_{key}", created.pk)
    event.settings.set(SETTINGS_KEY, True)


def template_pk(event, key):
    """The primary key of the template created for ``key`` (UNREAD or NEW),
    or None if it was deleted."""
    pk = event.settings.get(f"{SETTINGS_KEY}_{key}", as_type=int, default=None)
    templates = event.mail_templates.filter(role__isnull=True)
    if pk and templates.filter(pk=pk).exists():
        return pk
    if pk is None:  # created before the primary keys were remembered
        found = templates.filter(subject__icontains=_SUBJECT_HINTS[key]).first()
        return found.pk if found else None
    return None
