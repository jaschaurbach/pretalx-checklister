from pretalx.submission.models import SubmissionStates

from .models import Acknowledgement, InfoBlock
from .rt import mailto_for_ticket, rt_active, ticket_for_submission


def accepted_submissions_with_ticket(event, user=None):
    """Accepted or confirmed proposals that have an RT ticket (optionally of
    one user), oldest first."""
    submissions = event.submissions.filter(state__in=SubmissionStates.accepted_states)
    if user is not None:
        submissions = submissions.filter(speakers__user=user)
    return [
        submission
        for submission in submissions.distinct().order_by("pk")
        if ticket_for_submission(submission)
    ]


def _acknowledged_blocks(event, user=None):
    """Maps the id of each user to the set of ids of the boxes they confirmed."""
    acknowledgements = Acknowledgement.objects.filter(block__event=event)
    if user is not None:
        acknowledgements = acknowledgements.filter(user=user)
    result = {}
    for user_id, block_id in acknowledgements.values_list("user_id", "block_id"):
        result.setdefault(user_id, set()).add(block_id)
    return result


def boxes_for_user(event, user):
    """The information boxes this speaker has to read, with their texts
    filled in from the speaker's first accepted proposal that has an RT ticket."""
    if not rt_active(event) or not user or user.is_anonymous:
        return []
    blocks = list(InfoBlock.objects.filter(event=event))
    if not blocks:
        return []
    for submission in accepted_submissions_with_ticket(event, user):
        ticket = ticket_for_submission(submission)
        values = {
            "rt_ticket_id": ticket.rt_id,
            "rt_mailto": mailto_for_ticket(ticket, submission),
            "profile_page_url": event.urls.user.full(),
        }
        acknowledged = _acknowledged_blocks(event, user).get(user.pk, set())
        return [
            {
                "block": block,
                "title": block.title,
                "text": block.render_text(str(block.text), values),
                "acknowledged": block.pk in acknowledged,
            }
            for block in blocks
        ]
    return []


def all_acknowledged(boxes):
    return bool(boxes) and all(box["acknowledged"] for box in boxes)


def new_box(boxes):
    """The newest box the speaker has not confirmed yet, if the speaker has
    confirmed boxes before and that box is not the first one on the page."""
    if not any(box["acknowledged"] for box in boxes):
        return None
    unread = [box for box in boxes if not box["acknowledged"]]
    if not unread:
        return None
    newest = max(unread, key=lambda box: box["block"].pk)
    return None if newest is boxes[0] else newest


def speaker_progress(event):
    """The number of boxes of the event, and how many of them every speaker who
    has to read them has confirmed (a dict of speaker codes)."""
    block_ids = set(InfoBlock.objects.filter(event=event).values_list("pk", flat=True))
    if not block_ids:
        return 0, {}
    acknowledged = _acknowledged_blocks(event)
    progress = {}
    for submission in accepted_submissions_with_ticket(event):
        for speaker in submission.speakers.all():
            if speaker.user_id:
                confirmed = acknowledged.get(speaker.user_id, set()) & block_ids
                progress[speaker.code] = len(confirmed)
    return len(block_ids), progress


def acknowledgement_status(event):
    """Maps the code of every speaker who has to read the boxes to whether
    they have confirmed all of them."""
    total, progress = speaker_progress(event)
    return {code: confirmed == total for code, confirmed in progress.items()}


def speaker_groups(event):
    """The codes of the speakers who have confirmed none of the boxes
    ("unread") and of those who have confirmed some, but not all ("new")."""
    total, progress = speaker_progress(event)
    return {
        "unread": [code for code, confirmed in progress.items() if confirmed == 0],
        "new": [code for code, confirmed in progress.items() if 0 < confirmed < total],
    }
