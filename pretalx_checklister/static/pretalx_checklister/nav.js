// Adds the Checklister entry to the sidebar, between "Speakers" and "Speaker Information".
// Wrapped so the scripts do not share global names.
(() => {
    const script = document.currentScript

    document.addEventListener("DOMContentLoaded", () => {
        const menu = document.getElementById("collapseSpeakers")
        const anchor = menu && menu.querySelector("a[href$='/info/']")
        if (!script || !anchor) return
        const active = script.dataset.active === "1"
        const link = anchor.cloneNode(true)
        link.href = script.dataset.url
        link.classList.toggle("active", active)
        link.querySelector("span").textContent = script.dataset.label
        menu.insertBefore(link, anchor)
        if (active) menu.classList.add("show")
    })
})()
