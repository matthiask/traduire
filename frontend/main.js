// window.htmx = require("htmx.org")

import "./styles/reset.css"
import "./styles/functional.css"

import "./styles/vars.css"
import "./styles/buttons.css"
import "./styles/body.css"
import "./styles/header.css"
import "./styles/forms.css"
import "./styles/table.css"
import "./styles/entries.css"
import "./styles/login.css"

import { onReady, qs } from "./js/utils.js"

onReady(() => {
  document.body.addEventListener("change", (e) => {
    if (e.target.matches(".form--filter input[type=checkbox]")) {
      e.target.form.requestSubmit()
    }

    const entry = e.target.closest(".entry")
    if (e.target.closest(".entry__msgstr")) {
      qs(".entry__fuzzy input", e.target.closest(".entry")).checked = false
    }
  })
})

onReady(() => {
  document.body.addEventListener("click", async (e) => {
    const t = e.target.closest("[data-suggest]")
    if (t) {
      e.preventDefault()
      const body = new FormData()
      body.append("language_code", t.dataset.languageCode)
      body.append("msgid", t.dataset.suggest)
      const r = await fetch("/suggest/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "x-csrftoken": qs("input[name=csrfmiddlewaretoken]").value,
        },
        body,
      })
      if (r.ok) {
        const data = await r.json()
        if (data.msgstr) {
          qs("textarea", t.closest(".field")).value = data.msgstr
        } else if (data.error) {
          alert(data.error)
        }
      }
    }
  })
})
