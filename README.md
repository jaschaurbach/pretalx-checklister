# pretalx Checklister

A plugin for [pretalx](https://github.com/pretalx/pretalx) that gives accepted speakers
a page with crucial information, which they have to read and confirm box by box.
Organisers see who has confirmed what and can mail everyone who still has to.

Tested with pretalx **2026.2.1**. It needs the
[pretalx-rt](https://pypi.org/project/pretalx-rt/) plugin (every proposal has a Request
Tracker ticket), installed (it comes along with this plugin) and enabled for the event.
Otherwise the Checklister does nothing and organisers see a message on every page of the
organiser area. Speakers whose proposals have no RT ticket see nothing.

## What it does

**Organisers**

- Define information boxes (title and Markdown text, translatable) under
  *Speakers → Speaker Checklist*.
- The texts can contain placeholders, for example a link that mails the RT queue with the
  ticket number of the speaker's talk in the subject.
- The speaker list shows a green tick in the column *Checkboxes confirmed* for speakers
  who have confirmed all boxes.
- Two mail templates are created automatically ("please read the information" and "there
  is new information"). On the mail composer page (*Sessions, proposals, speakers*),
  buttons preselect all speakers who have confirmed nothing yet, or who have new information.

**Speakers** (with an accepted or confirmed talk that has an RT ticket)

- See a notice with a link on the event start page and on *My proposals*, plus an entry in
  the user menu.
- The notes page (`/<event>/me/submissions/notes`) shows all boxes, each with a tick box
  "I have read and understood this", and one Save button.
- When an organiser adds a new box later, the tick in the speaker list disappears, the
  notice asks again, and the notes page offers a "New information" link to jump to it.

## Placeholders

In the box texts:

| Placeholder | Becomes |
|---|---|
| `{rt_ticket_id}` | the RT ticket number of the speaker's talk |
| `{rt_mailto}` | a `mailto:` link to the RT queue, subject `[rt-host #ticket] - talk title` |
| `{profile_page_url}` | the speaker's page of the conference (`…/CONFERENCE/me/`) |

In mail templates there is the additional placeholder `{notes_url}` (link to the notes page).

The mail address is built from the queue name of pretalx-rt plus `@cccv.de`
(`MAIL_DOMAIN` in `pretalx_checklister/rt.py`).

## Installation

Run these commands as the user that runs pretalx, in the environment of your pretalx
installation (see [performing updates](https://docs.pretalx.org/administrator/maintenance/#performing-updates)
in the pretalx documentation).

1. Install the plugin. This also installs `pretalx-rt`, which the plugin needs:

   ```
   python -m pip install git+https://github.com/jaschaurbach/pretalx-checklister.git
   ```

2. Apply the database changes:

   ```
   python -m pretalx migrate
   ```

3. Rebuild the static files:

   ```
   python -m pretalx rebuild
   ```

## Good to know

- If a speaker has several accepted talks, the box texts use the oldest one.
- pretalx has no plugin hooks for the speaker menu, the start page, the speaker table and
  the recipient selection of the mail composer. These parts are added with small script
  files and could break with a pretalx update.

## To do

- Make it work without the RT plugin available.

## Development

```
just test      # run the tests (needs pretalx and pretalx-rt in the environment)
just fmt       # format and lint
```

### Translations

The plugin is available in English and German. After changing texts in the code or
templates:

```
just localegen       # update pretalx_checklister/locale/<language>/LC_MESSAGES/django.po
# translate the new entries in the .po files
just localecompile   # create the django.mo files, which pretalx loads
```

Commit the `.po` and the `.mo` files. A new language is added to `languages` in the
`justfile`.

## License

Copyright 2026 tomate. Released under the Apache License 2.0.
