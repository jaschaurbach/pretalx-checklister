// Adds the link to the user menu and, on the event start page, the notice.
// Wrapped so the scripts do not share global names.
(() => {
    const script = document.currentScript

    document.addEventListener("DOMContentLoaded", () => {
        if (!script) return
        const profile = document.querySelector(
            `#user-dropdown a[href='${script.dataset.profileUrl}']`,
        )
        if (profile) {
            const link = profile.cloneNode(true)
            link.href = script.dataset.url
            link.querySelector("i").className = "fa fa-exclamation-circle mr-2"
            link.lastChild.textContent = ` ${script.dataset.label}`
            profile.after(link)
        }
        const main = document.querySelector("main")
        if (script.dataset.html && main) {
            const notice = document.createElement("div")
            notice.innerHTML = script.dataset.html
            main.prepend(notice)
        }
    })
})()
