"""Access to the RT ticket of a proposal, as provided by pretalx-rt.

The plugin needs pretalx-rt, installed and enabled for the event: otherwise
nothing of this plugin is active (see ``rt_active``) and organisers get a
message instead."""

from urllib.parse import quote, urlparse

try:
    from pretalx_rt.models import EventSettings, Ticket
except ImportError:  # pragma: no cover
    EventSettings = Ticket = None

MAIL_DOMAIN = "cccv.de"


def rt_installed():
    return Ticket is not None


def rt_active(event):
    """pretalx-rt is installed and enabled for this event."""
    return rt_installed() and event is not None and "pretalx_rt" in event.plugin_list


def ticket_for_submission(submission):
    if Ticket is None:
        return None
    return Ticket.for_submission(submission)


def build_mailto(event_id, rt_id, title):
    """Build the mailto link to the RT queue, e.g. subject
    ``[rt.cccv.de #137864] - Proposal title``."""
    settings = EventSettings.for_event(event_id)
    if settings is None:
        return ""
    host = urlparse(settings.base_url).netloc
    subject = f"[{host} #{rt_id}] - {title}"
    address = f"{quote(settings.queue, safe='')}@{MAIL_DOMAIN}"
    return f"mailto:{address}?subject={quote(subject, safe='')}"


def mailto_for_ticket(ticket, submission):
    return build_mailto(ticket.event_id, ticket.rt_id, submission.title)
