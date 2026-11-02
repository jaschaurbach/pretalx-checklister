from django.apps import AppConfig
from django.utils.translation import gettext_lazy

from . import __version__


class PluginApp(AppConfig):
    name = "pretalx_checklister"
    verbose_name = "pretalx Checklister"

    class PretalxPluginMeta:
        name = gettext_lazy("pretalx Checklister")
        author = "tomate"
        description = gettext_lazy(
            "Crucial information for accepted speakers that they have to read and "
            "confirm, with RT ticket links, an overview for organisers and mail templates."
        )
        visible = True
        version = __version__
        category = "OTHER"

    def installed(self, event):
        from .mail import ensure_mail_templates  # noqa: PLC0415 -- needs loaded apps

        ensure_mail_templates(event)

    def ready(self):
        from . import signals  # noqa: PLC0415, F401
