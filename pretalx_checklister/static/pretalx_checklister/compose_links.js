// Adds links above the "Speakers" field that preselect the speakers
// who have not confirmed all information boxes.
// Wrapped so the scripts do not share global names.
(() => {
    const script = document.currentScript

    document.addEventListener("DOMContentLoaded", () => {
        const field = document.getElementById("id_speakers")
        if (!script || !field) return
        const group = field.closest(".form-group, .row") || field.parentElement
        const box = document.createElement("div")
        box.className = "offset-md-3 col-md-9 pt-0 mb-2"
        for (const key of ["unread", "new"]) {
            const count = Number(script.dataset[`${key}Count`])
            if (!count) continue
            const link = document.createElement("a")
            link.className = "btn btn-sm btn-outline-info mr-2"
            link.href = script.dataset[`${key}Url`]
            link.textContent = `${script.dataset[`${key}Label`]} (${count})`
            box.append(link)
        }
        group.before(box)
    })
})()
