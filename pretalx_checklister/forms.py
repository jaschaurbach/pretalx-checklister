from django.db.models import Max
from i18nfield.forms import I18nModelForm

from .models import InfoBlock


class InfoBlockForm(I18nModelForm):
    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs, locales=event.locales)
        # pretalx sizes textareas to their content, so "rows" has no effect
        for widget in self.fields["text"].widget.widgets:
            widget.attrs["style"] = "min-height: 12rem"

    def save(self, commit=True):
        self.instance.event = self.event
        if self.instance.pk is None:
            last = InfoBlock.objects.filter(event=self.event).aggregate(
                last=Max("position")
            )["last"]
            self.instance.position = 0 if last is None else last + 1
        return super().save(commit=commit)

    class Meta:
        model = InfoBlock
        fields = ("title", "text")
