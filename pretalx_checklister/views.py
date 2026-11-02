from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView, View

from pretalx.cfp.views.event import LoggedInEventPageMixin
from pretalx.common.views.mixins import EventPermissionRequired
from pretalx.common.views.redirect import get_login_redirect

from .forms import InfoBlockForm
from .mail import ensure_mail_templates
from .models import Acknowledgement, InfoBlock
from .rt import rt_active
from .speaker import boxes_for_user, new_box


class RequiresRT:
    """Without pretalx-rt the plugin has no pages."""

    def dispatch(self, request, *args, **kwargs):
        if not rt_active(request.event):
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class InfoBlockList(RequiresRT, EventPermissionRequired, TemplateView):
    permission_required = "event.update_event"
    template_name = "pretalx_checklister/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ensure_mail_templates(self.request.event)
        context["blocks"] = InfoBlock.objects.filter(event=self.request.event)
        return context


class InfoBlockEdit(RequiresRT, EventPermissionRequired, FormView):
    permission_required = "event.update_event"
    template_name = "pretalx_checklister/edit.html"
    form_class = InfoBlockForm

    @property
    def block(self):
        if "pk" not in self.kwargs:
            return None
        return get_object_or_404(
            InfoBlock, event=self.request.event, pk=self.kwargs["pk"]
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.request.event
        kwargs["instance"] = self.block
        return kwargs

    def get_success_url(self):
        return self.request.event.orga_urls.settings + "p/pretalx_checklister/"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("The information box was saved."))
        return super().form_valid(form)


class InfoBlockDelete(RequiresRT, EventPermissionRequired, View):
    permission_required = "event.update_event"

    def post(self, request, *args, **kwargs):
        get_object_or_404(InfoBlock, event=request.event, pk=self.kwargs["pk"]).delete()
        messages.success(request, _("The information box was deleted."))
        return redirect(request.event.orga_urls.settings + "p/pretalx_checklister/")


class SpeakerNotes(RequiresRT, LoggedInEventPageMixin, TemplateView):
    template_name = "pretalx_checklister/notes.html"

    def handle_no_permission(self):
        # pretalx only redirects to the login for views in the "cfp" namespace
        if self.request.user.is_anonymous:
            return get_login_redirect(self.request)
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        boxes = boxes_for_user(self.request.event, self.request.user)
        context["boxes"] = boxes
        context["new_box"] = new_box(boxes)
        return context

    def post(self, request, *args, **kwargs):
        for box in boxes_for_user(request.event, request.user):
            if f"read_{box['block'].pk}" in request.POST:
                Acknowledgement.objects.get_or_create(
                    block=box["block"], user=request.user
                )
            else:
                Acknowledgement.objects.filter(
                    block=box["block"], user=request.user
                ).delete()
        messages.success(request, _("Your confirmation was saved."))
        return redirect(request.path)
