from django.db import models
from django.utils.translation import gettext_lazy as _
from i18nfield.fields import I18nCharField, I18nTextField

LINK_PLACEHOLDERS = {"profile_page_url"}


class InfoBlock(models.Model):
    """Information box for speakers, shown once per accepted proposal.

    The text may contain placeholders like ``{rt_ticket_id}``, which are
    replaced with the values of the respective proposal."""

    event = models.ForeignKey(
        to="event.Event",
        on_delete=models.CASCADE,
        related_name="pretalx_checklister_blocks",
    )
    position = models.PositiveIntegerField(default=0)
    title = I18nCharField(max_length=200, verbose_name=_("Title"))
    text = I18nTextField(
        verbose_name=_("Text"),
        help_text=_(
            "Markdown is supported. Placeholders: {rt_ticket_id} is the RT "
            "ticket number of the proposal, {rt_mailto} is a mailto link "
            "address to the RT queue with the ticket in the subject, "
            "{profile_page_url} is the link to the speaker's page of the "
            "conference (…/CONFERENCE/me/). The box is "
            "shown once per speaker with an accepted or confirmed proposal that "
            "has an RT ticket."
        ),
    )

    class Meta:
        ordering = ("position", "pk")

    def __str__(self):
        return str(self.title)

    def render_text(self, locale_text, values):
        """Substitute known placeholders in ``locale_text``.

        Plain replacement instead of ``str.format``, so stray braces in
        the markdown never raise. A link placeholder that is not already the
        target of a markdown link is wrapped in ``<>``, so that it always
        renders as a link (pretalx does not link bare addresses with an IP
        or other unknown host)."""
        for name, value in values.items():
            placeholder = f"{{{name}}}"
            if name in LINK_PLACEHOLDERS:
                parts = locale_text.split(placeholder)
                locale_text = parts[0]
                for part in parts[1:]:
                    in_link = locale_text.endswith("](")
                    locale_text += (str(value) if in_link else f"<{value}>") + part
            else:
                locale_text = locale_text.replace(placeholder, str(value))
        return locale_text


class Acknowledgement(models.Model):
    """A speaker confirmed that they have read an information box."""

    block = models.ForeignKey(
        to=InfoBlock, on_delete=models.CASCADE, related_name="acknowledgements"
    )
    user = models.ForeignKey(
        to="person.User",
        on_delete=models.CASCADE,
        related_name="pretalx_checklister_acknowledgements",
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("block", "user"),)

    def __str__(self):
        return f"Acknowledgement(block={self.block_id}, user={self.user_id})"
