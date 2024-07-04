window.htmx = require("htmx.org")
import("htmx.org/dist/ext/response-targets.js")

import "./styles/reset.css"
import "./styles/functional.css"

import "./styles/vars.css"
import "./styles/icons.css"
import "./styles/buttons.css"
import "./styles/body.css"
import "./styles/header.css"
import "./styles/forms.css"
import "./styles/table.css"

import "./dashboard/base.css"
import "./dashboard/login.css"
import "./dashboard/objects.css"

import { onReady, qsa, qs, getCSSVariableValue } from "./js/utils.js"

onReady(() => {
  document.body.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      window["menu-toggle"].checked = false
    }
  })
})

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
