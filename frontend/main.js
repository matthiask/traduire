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

import { onReady } from "./js/utils.js"

onReady(() => {
  document.body.addEventListener("change", (e) => {
    if (e.target.matches(".form--filter input[type=checkbox]")) {
      e.target.form.requestSubmit()
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
          "x-csrftoken": document.querySelector(
            "input[name=csrfmiddlewaretoken]",
          ).value,
        },
        body,
      })
      if (r.ok) {
        const data = await r.json()
        if (data.msgstr) {
          t.closest(".field").querySelector("textarea").value = data.msgstr
        } else if (data.error) {
          alert(data.error)
        }
      }
    }
  })
})
