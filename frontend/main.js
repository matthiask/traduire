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
    if (e.target.matches(".form--filter input")) {
      e.target.form.requestSubmit()
    }
  })
})
