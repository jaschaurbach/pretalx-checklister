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
        return super().save(commit=commit)

    class Meta:
        model = InfoBlock
        fields = ("title", "text")
