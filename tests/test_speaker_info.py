import pytest
from django.urls import reverse
from django_scopes import scopes_disabled

from pretalx.event.domain.plugins import disable_plugin
from pretalx.person.models import User

from pretalx_checklister.models import Acknowledgement, InfoBlock
from pretalx_checklister.speaker import speaker_groups


def get_page(client, event):
    return client.get(f"/{event.slug}/me/submissions/notes", follow=True)


@pytest.mark.django_db
@pytest.mark.parametrize("state", ("accepted", "confirmed"))
def test_box_shown_for_accepted_talks(speaker_client, event, block, make_talk, state):
    make_talk(state, rt_id=4711)
    content = get_page(speaker_client, event).content.decode()
    assert "Ticket-Box" in content
    assert (
        "mailto:Talks@cccv.de?subject=%5Brt.example.invalid%20%234711%5D%20-%20A%20talk"
        in content
    )
    assert "ticket 4711" in content
    assert "{rt_ticket_id}" not in content


@pytest.mark.django_db
@pytest.mark.parametrize("state", ("submitted", "rejected", "withdrawn", "canceled"))
def test_box_hidden_for_other_states(speaker_client, event, block, make_talk, state):
    make_talk(state, rt_id=4711)
    content = get_page(speaker_client, event).content.decode()
    assert "4711" not in content
    assert "Ticket-Box" not in content


@pytest.mark.django_db
def test_box_hidden_without_ticket(speaker_client, event, block, make_talk):
    make_talk("accepted", with_ticket=False)
    assert "Ticket-Box" not in get_page(speaker_client, event).content.decode()


@pytest.mark.django_db
def test_box_once_per_speaker(speaker_client, event, block, make_talk):
    make_talk("rejected", rt_id=3333, title="Third talk")
    make_talk("accepted", rt_id=1111, title="First talk")
    make_talk("confirmed", rt_id=2222, title="Second talk")
    content = get_page(speaker_client, event).content.decode()
    assert content.count("Ticket-Box") == 1
    assert "%231111%5D%20-%20First%20talk" in content
    assert "2222" not in content
    assert "3333" not in content


@pytest.mark.django_db
def test_box_not_shown_to_other_speakers(client, event, block, make_talk):
    make_talk("accepted", rt_id=4711)
    with scopes_disabled():
        other = User.objects.create_user(
            password="x-passw0rd", email="other@example.org", name="Other"
        )
    client.force_login(other)
    content = get_page(client, event).content.decode()
    assert "4711" not in content


@pytest.mark.django_db
def test_stray_braces_do_not_break_rendering(speaker_client, event, make_talk):
    with scopes_disabled():
        InfoBlock.objects.create(
            event=event, title="Odd", text="{ nope } {rt_ticket_id"
        )
    make_talk("accepted")
    assert get_page(speaker_client, event).status_code == 200


@pytest.mark.django_db
def test_orga_can_manage_blocks(orga_client, event):
    url = reverse("plugins:pretalx_checklister:block.new", kwargs={"event": event.slug})
    response = orga_client.post(
        url, {"title_0": "Hello", "text_0": "ID {rt_ticket_id}"}, follow=True
    )
    assert response.status_code == 200
    with scopes_disabled():
        block = InfoBlock.objects.get(event=event)
    assert str(block.title) == "Hello"
    listing = orga_client.get(
        reverse("plugins:pretalx_checklister:settings", kwargs={"event": event.slug})
    )
    assert "Hello" in listing.content.decode()
    orga_client.post(
        reverse(
            "plugins:pretalx_checklister:block.delete",
            kwargs={"event": event.slug, "pk": block.pk},
        )
    )
    with scopes_disabled():
        assert not InfoBlock.objects.filter(event=event).exists()


@pytest.mark.django_db
def test_reviewer_cannot_access_settings(review_client, event):
    response = review_client.get(
        reverse("plugins:pretalx_checklister:settings", kwargs={"event": event.slug})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_menu_entry_for_orga_only(orga_client, event):
    url = f"/orga/event/{event.slug}/"
    assert "pretalx_checklister/nav.js" in orga_client.get(url).content.decode()


@pytest.mark.django_db
def test_no_menu_entry_for_reviewer(review_client, event):
    url = f"/orga/event/{event.slug}/"
    assert "pretalx_checklister/nav.js" not in review_client.get(url).content.decode()


@pytest.mark.django_db
def test_no_entry_in_plugin_settings_nav(orga_client, event):
    response = orga_client.get(f"/orga/event/{event.slug}/settings/")
    assert "plugins/pretalx_checklister" not in response.content.decode()


@pytest.mark.django_db
def test_notice_on_submission_list_and_start_page(
    speaker_client, event, block, make_talk
):
    make_talk("accepted")
    listing = speaker_client.get(f"/{event.slug}/me/submissions/").content.decode()
    assert f"/{event.slug}/me/submissions/notes" in listing
    assert "Ticket-Box" not in listing
    start = speaker_client.get(f"/{event.slug}/").content.decode()
    assert "pretalx_checklister/speaker_pages.js" in start
    assert f"/{event.slug}/me/submissions/notes" in start


@pytest.mark.django_db
def test_no_notice_without_accepted_talk(speaker_client, event, block, make_talk):
    make_talk("submitted")
    listing = speaker_client.get(f"/{event.slug}/me/submissions/").content.decode()
    assert "/me/submissions/notes" not in listing
    start = speaker_client.get(f"/{event.slug}/").content.decode()
    assert "speaker_pages.js" not in start


@pytest.mark.django_db
def test_notes_page_needs_login(client, event, block):
    response = client.get(f"/{event.slug}/me/submissions/notes")
    assert response.status_code == 302


@pytest.mark.django_db
def test_acknowledge_blocks(speaker_client, speaker_user, event, block, make_talk):
    make_talk("accepted")
    with scopes_disabled():
        second = InfoBlock.objects.create(event=event, title="Second", text="x")
    url = f"/{event.slug}/me/submissions/notes"
    speaker_client.post(url, {f"read_{block.pk}": "on"})
    with scopes_disabled():
        assert Acknowledgement.objects.filter(user=speaker_user).count() == 1
        assert Acknowledgement.objects.filter(user=speaker_user, block=block).exists()
    content = speaker_client.get(url).content.decode()
    assert content.count("checked") == 1
    speaker_client.post(url, {f"read_{second.pk}": "on"})
    with scopes_disabled():
        assert list(
            Acknowledgement.objects.filter(user=speaker_user).values_list(
                "block", flat=True
            )
        ) == [second.pk]


@pytest.mark.django_db
def test_acknowledge_ignores_unrelated_blocks(
    speaker_client, speaker_user, event, block
):
    # no accepted talk: nothing to acknowledge
    speaker_client.post(
        f"/{event.slug}/me/submissions/notes", {f"read_{block.pk}": "on"}
    )
    with scopes_disabled():
        assert not Acknowledgement.objects.exists()


@pytest.mark.django_db
def test_start_page_notice_is_valid_attribute(speaker_client, event, block, make_talk):
    make_talk("accepted")
    start = speaker_client.get(f"/{event.slug}/").content.decode()
    assert 'data-html="' in start
    attribute = start.split('data-html="', 1)[1].split('"', 1)[0]
    assert "&lt;div class=&quot;alert alert-warning&quot;" in attribute


@pytest.mark.django_db
def test_notice_becomes_short_link_when_all_confirmed(
    speaker_client, speaker_user, event, block, make_talk
):
    make_talk("accepted")
    url = f"/{event.slug}/me/submissions/"
    assert "Please read it" in speaker_client.get(url).content.decode()
    with scopes_disabled():
        Acknowledgement.objects.create(block=block, user=speaker_user)
    content = speaker_client.get(url).content.decode()
    assert "alert-warning" in content
    assert "Please read it" not in content
    assert "Crucial information" in content
    assert f"/{event.slug}/me/submissions/notes" in content
    # a new box brings the original notice back
    with scopes_disabled():
        InfoBlock.objects.create(event=event, title="Newer", text="y")
    assert "Please read it" in speaker_client.get(url).content.decode()


@pytest.mark.django_db
def test_menu_script_for_speakers_with_boxes(speaker_client, event, block, make_talk):
    make_talk("accepted")
    content = speaker_client.get(f"/{event.slug}/me/").content.decode()
    assert "pretalx_checklister/speaker_pages.js" in content
    assert f'data-url="/{event.slug}/me/submissions/notes"' in content


@pytest.mark.django_db
def test_new_information_link(speaker_client, speaker_user, event, block, make_talk):
    make_talk("accepted")
    url = f"/{event.slug}/me/submissions/notes"
    with scopes_disabled():
        Acknowledgement.objects.create(block=block, user=speaker_user)
        newer = InfoBlock.objects.create(event=event, title="Newer", text="y")
    content = speaker_client.get(url).content.decode()
    assert f'href="#box-{newer.pk}"' in content
    assert f'id="box-{newer.pk}"' in content


@pytest.mark.django_db
def test_no_new_information_link_for_first_visit(
    speaker_client, event, block, make_talk
):
    make_talk("accepted")
    with scopes_disabled():
        InfoBlock.objects.create(event=event, title="Newer", text="y")
    content = speaker_client.get(f"/{event.slug}/me/submissions/notes").content.decode()
    assert "New information" not in content


@pytest.mark.django_db
def test_speaker_list_status(orga_client, speaker_user, event, block, make_talk):
    make_talk("accepted")
    code = speaker_user.get_speaker(event).code
    url = f"/orga/event/{event.slug}/speakers/"
    content = orga_client.get(url).content.decode()
    assert "speakers_column.js" in content
    assert f"&quot;{code}&quot;: false" in content
    with scopes_disabled():
        Acknowledgement.objects.create(block=block, user=speaker_user)
    content = orga_client.get(url).content.decode()
    assert f"&quot;{code}&quot;: true" in content
    with scopes_disabled():
        InfoBlock.objects.create(event=event, title="Newer", text="y")
    content = orga_client.get(url).content.decode()
    assert f"&quot;{code}&quot;: false" in content


@pytest.mark.django_db
def test_profile_page_url_placeholder(speaker_client, event, make_talk):
    with scopes_disabled():
        InfoBlock.objects.create(
            event=event, title="Ticket-Box", text="[Your page]({profile_page_url})"
        )
    make_talk("accepted")
    content = get_page(speaker_client, event).content.decode()
    assert "{profile_page_url}" not in content
    assert f'/{event.slug}/me/"' in content


@pytest.mark.django_db
def test_bare_profile_page_url_is_a_link(speaker_client, event, make_talk):
    with scopes_disabled():
        InfoBlock.objects.create(
            event=event, title="Ticket-Box", text="Visit {profile_page_url} now"
        )
    make_talk("accepted")
    content = get_page(speaker_client, event).content.decode()
    assert f"/{event.slug}/me/</a> now" in content


@pytest.mark.django_db
def test_speaker_groups(event, speaker_user, block, make_talk):
    make_talk("accepted")
    code = speaker_user.get_speaker(event).code
    with scopes_disabled():
        assert speaker_groups(event) == {"unread": [code], "new": []}
        Acknowledgement.objects.create(block=block, user=speaker_user)
        assert speaker_groups(event) == {"unread": [], "new": []}
        InfoBlock.objects.create(event=event, title="Newer", text="y")
        assert speaker_groups(event) == {"unread": [], "new": [code]}


@pytest.mark.django_db
def test_compose_page_links_preselect_speakers(
    orga_client, speaker_user, event, block, make_talk
):
    make_talk("accepted")
    code = speaker_user.get_speaker(event).code
    url = f"/orga/event/{event.slug}/mails/compose/sessions/"
    content = orga_client.get(url).content.decode()
    assert "compose_links.js" in content
    assert f"?speakers={code}&amp;template=" in content
    # the link target preselects the speaker in the compose form
    with scopes_disabled():
        template = event.mail_templates.filter(role__isnull=True).first()
    response = orga_client.get(f"{url}?speakers={code}&template={template.pk}")
    with scopes_disabled():
        assert response.context["form"].initial["speakers"].filter(code=code).exists()
        assert str(response.context["form"].initial["subject"]) == str(template.subject)


@pytest.mark.django_db
def test_compose_page_without_open_speakers_has_no_links(orga_client, event, block):
    content = orga_client.get(
        f"/orga/event/{event.slug}/mails/compose/sessions/"
    ).content.decode()
    assert "compose_links.js" not in content


@pytest.mark.django_db
def test_without_rt_organisers_get_a_message(orga_client, event, no_rt):
    content = orga_client.get(f"/orga/event/{event.slug}/").content.decode()
    assert "pretalx-rt" in content
    assert "is not installed" in content
    assert "pretalx_checklister/nav.js" not in content


@pytest.mark.django_db
def test_with_rt_there_is_no_message(orga_client, event):
    content = orga_client.get(f"/orga/event/{event.slug}/").content.decode()
    assert "is not installed" not in content


@pytest.mark.django_db
def test_without_rt_the_plugin_has_no_pages(
    orga_client, speaker_client, event, block, make_talk, no_rt
):
    make_talk("accepted")
    base = f"/orga/event/{event.slug}/settings/p/pretalx_checklister/"
    assert orga_client.get(base).status_code == 404
    assert orga_client.get(f"{base}new/").status_code == 404
    assert speaker_client.get(f"/{event.slug}/me/submissions/notes").status_code == 404


@pytest.mark.django_db
def test_without_rt_nothing_is_added_to_the_pages(
    speaker_client, event, block, make_talk, no_rt
):
    make_talk("accepted")
    for url in (f"/{event.slug}/", f"/{event.slug}/me/submissions/"):
        content = speaker_client.get(url).content.decode()
        assert "notes" not in content.replace("notes_", "")
        assert "speaker_pages.js" not in content


@pytest.mark.django_db
def test_orga_message_when_rt_is_not_enabled(orga_client, event):
    with scopes_disabled():
        disable_plugin(event, "pretalx_rt")
    content = orga_client.get(f"/orga/event/{event.slug}/").content.decode()
    assert "is not enabled for this event" in content
    assert "pretalx_checklister/nav.js" not in content


@pytest.mark.django_db
def test_speaker_sees_nothing_when_rt_is_not_enabled(
    speaker_client, event, block, make_talk
):
    make_talk("accepted")
    with scopes_disabled():
        disable_plugin(event, "pretalx_rt")
    assert speaker_client.get(f"/{event.slug}/me/submissions/notes").status_code == 404
    listing = speaker_client.get(f"/{event.slug}/me/submissions/").content.decode()
    assert "/me/submissions/notes" not in listing


@pytest.mark.django_db
def test_not_installed_message_differs_from_not_enabled(orga_client, event, no_rt):
    content = orga_client.get(f"/orga/event/{event.slug}/").content.decode()
    assert "is not installed" in content
    assert "is not enabled" not in content
