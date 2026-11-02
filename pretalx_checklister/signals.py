import json
from urllib.parse import urlencode

from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _

from pretalx.cfp.signals import html_above_submission_list
from pretalx.cfp.signals import html_head as cfp_html_head
from pretalx.mail.signals import register_mail_placeholders
from pretalx.orga.signals import html_above_orga_page
from pretalx.orga.signals import html_head as nav_event_html_head

from .mail import NEW, UNREAD, notes_placeholders, template_pk
from .rt import rt_active, rt_installed
from .speaker import (
    acknowledgement_status,
    all_acknowledged,
    boxes_for_user,
    speaker_groups,
)


@receiver(nav_event_html_head)
def pretalx_checklister_nav(sender, request, **kwargs):
    """Add the menu entry below "Speakers" -> "Speakers".

    The sidebar has no plugin slot inside the speakers menu, so a small script
    (inline scripts are blocked by the CSP) inserts the entry."""
    if not rt_active(request.event) or not request.user.has_perm(
        "event.update_event", request.event
    ):
        return ""
    url = reverse(
        "plugins:pretalx_checklister:settings", kwargs={"event": request.event.slug}
    )
    return render_to_string(
        "pretalx_checklister/nav.html",
        {
            "url": url,
            "label": _("Speaker Checklist"),
            "active": request.path.startswith(url),
        },
    )


def _notes_url(event):
    return reverse("plugins:pretalx_checklister:notes", kwargs={"event": event.slug})


def _notice_html(event, boxes):
    return render_to_string(
        "pretalx_checklister/notice.html",
        {"url": _notes_url(event), "done": all_acknowledged(boxes)},
    )


@receiver(html_above_submission_list)
def pretalx_checklister_notice(sender, request, **kwargs):
    """Point the speaker to the crucial information."""
    boxes = boxes_for_user(sender, request.user)
    return _notice_html(sender, boxes) if boxes else ""


@receiver(cfp_html_head)
def pretalx_checklister_speaker_pages(sender, request, **kwargs):
    """Add the link to the user menu and, on the event start page, the notice.

    Neither has a plugin slot, so a small script (inline scripts are blocked by
    the CSP) inserts them."""
    boxes = boxes_for_user(sender, request.user)
    if not boxes:
        return ""
    start_page = request.path == sender.urls.base.rstrip("/") + "/"
    return render_to_string(
        "pretalx_checklister/speaker_pages.html",
        {
            "url": _notes_url(sender),
            "label": _("Crucial information"),
            "profile_url": sender.urls.user,
            "html": _notice_html(sender, boxes) if start_page else "",
        },
    )


@receiver(nav_event_html_head)
def pretalx_checklister_speakers_column(sender, request, **kwargs):
    """Add the "Checkboxes confirmed" column to the speaker list."""
    if (
        not rt_active(sender)
        or request.path != sender.orga_urls.speakers
        or not request.user.has_perm("event.update_event", sender)
    ):
        return ""
    status = acknowledgement_status(sender)
    if not status:
        return ""
    return render_to_string(
        "pretalx_checklister/speakers_column.html",
        {"label": _("Checkboxes confirmed"), "status": json.dumps(status)},
    )


@receiver(register_mail_placeholders)
def pretalx_checklister_mail_placeholders(sender, **kwargs):
    return notes_placeholders() if rt_active(sender) else []


@receiver(html_above_orga_page)
def pretalx_checklister_rt_missing(sender, request, **kwargs):
    """Tell organisers why the plugin does nothing."""
    if rt_active(sender):
        return ""
    return render_to_string(
        "pretalx_checklister/rt_missing.html", {"installed": rt_installed()}
    )


def _compose_url(event, codes, template):
    query = {"speakers": ",".join(codes)}
    if template:
        query["template"] = template
    return f"{event.orga_urls.compose_mails_sessions}?{urlencode(query, safe=',')}"


@receiver(nav_event_html_head)
def pretalx_checklister_compose_links(sender, request, **kwargs):
    """Offer to preselect the speakers on the "write emails to proposals" page.

    The compose form accepts ``speakers`` and ``template`` in the URL; there is
    no plugin hook for recipient filters."""
    if (
        not rt_active(sender)
        or request.path != sender.orga_urls.compose_mails_sessions
        or not request.user.has_perm("mail.send_queuedmail", sender)
    ):
        return ""
    groups = speaker_groups(sender)
    if not (groups["unread"] or groups["new"]):
        return ""
    return render_to_string(
        "pretalx_checklister/compose_links.html",
        {
            "unread_label": _("Speakers who have confirmed no information yet"),
            "unread_count": len(groups["unread"]),
            "unread_url": _compose_url(
                sender, groups["unread"], template_pk(sender, UNREAD)
            ),
            "new_label": _("Speakers with new information"),
            "new_count": len(groups["new"]),
            "new_url": _compose_url(sender, groups["new"], template_pk(sender, NEW)),
        },
    )
