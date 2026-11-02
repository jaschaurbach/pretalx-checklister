from django.urls import re_path

from pretalx.event.models.event import SLUG_REGEX

from .views import InfoBlockDelete, InfoBlockEdit, InfoBlockList, SpeakerNotes

BASE = rf"^orga/event/(?P<event>{SLUG_REGEX})/settings/p/pretalx_checklister/"

urlpatterns = [
    re_path(f"{BASE}$", InfoBlockList.as_view(), name="settings"),
    re_path(f"{BASE}new/$", InfoBlockEdit.as_view(), name="block.new"),
    re_path(f"{BASE}(?P<pk>[0-9]+)/$", InfoBlockEdit.as_view(), name="block.edit"),
    re_path(
        f"{BASE}(?P<pk>[0-9]+)/delete/$", InfoBlockDelete.as_view(), name="block.delete"
    ),
    re_path(
        rf"^(?P<event>{SLUG_REGEX})/me/submissions/notes$",
        SpeakerNotes.as_view(),
        name="notes",
    ),
]
