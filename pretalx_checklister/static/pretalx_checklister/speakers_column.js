// Adds the "Checkboxes confirmed" column to the speaker list in the organiser area.
// Wrapped so the scripts do not share global names.
(() => {
    const script = document.currentScript

    document.addEventListener("DOMContentLoaded", () => {
        const table = document.querySelector("table")
        if (!script || !table) return
        const status = JSON.parse(script.dataset.status)
        const head = document.createElement("th")
        head.textContent = script.dataset.label
        table.querySelector("thead tr").append(head)
        for (const row of table.querySelectorAll("tbody tr")) {
            const cell = document.createElement("td")
            const link = row.querySelector("a[href*='/speakers/']")
            const code = link && link.getAttribute("href").match(/\/speakers\/([^/]+)\/?$/)
            if (code && status[code[1]]) {
                cell.innerHTML = '<i class="fa fa-check text-success"></i>'
            }
            row.append(cell)
        }
    })
})()
