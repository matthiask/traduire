// export const { gettext, pgettext, ngettext } = window
// Make interpolate() always use named placeholders
// const i = window.interpolate
// export const interpolate = (s, p) => i(s, p, true)

export function onReady(fn) {
  if (
    document.readyState === "complete" ||
    document.readyState === "interactive"
  ) {
    // call on next available tick
    setTimeout(fn, 1)
  } else {
    document.addEventListener("DOMContentLoaded", fn)
  }
}

export const qs = (sel, base = document) => base.querySelector(sel)
export const qsa = (sel, base = document) => base.querySelectorAll(sel)
