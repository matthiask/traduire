export const { gettext, pgettext, ngettext } = window
// Make interpolate() always use named placeholders
const i = window.interpolate
export const interpolate = (s, p) => i(s, p, true)

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

export function csrfTokenHeader() {
  return {
    "X-CSRFToken": document.cookie.match(/\bcsrftoken=(.+?)\b/)[1],
  }
}

export const containsJSON = (response) => {
  const contentType = response.headers.get("content-type")
  return contentType ? contentType.includes("application/json") : false
}

export function getCookie(cookieName) {
  const cookies = document.cookie ? document.cookie.split("; ") : []
  const prefix = `${cookieName}=`
  for (const cookie of cookies) {
    if (cookie.startsWith(prefix))
      return decodeURIComponent(cookie.substring(prefix.length))
  }
}

export const fetchAPI = async (url, opts = {}) => {
  opts.credentials = "same-origin"
  opts.headers = opts.headers || {}
  opts.headers["X-CSRFToken"] = getCookie("csrftoken")
  const response = await fetch(url, opts)
  /*
  if (response.status == 401) {
    window.location.href = `/world/login/?next=${encodeURIComponent(
      window.location.pathname,
    )}`
  }
  */
  return response
}

export const fetchJSON = async (url, opts) => {
  const response = await fetchAPI(url, opts)
  if (!response.ok || !containsJSON(response)) throw Error(response.statusText)
  return response.json()
}

export const changeListPresence = (list, item, presence) => {
  // Add or remove items from list while ensuring that we return the object
  // unchanged if no change is necessary.
  return presence
    ? list.includes(item)
      ? list
      : [...list, item]
    : list.includes(item)
      ? list.filter((i) => i !== item)
      : list
}

/**
 * Retrieves the value of a CSS variable.
 *
 * @param {string} variable - The name of the CSS variable (e.g., '--header-height-full').
 * @returns {string|null} - The value of the CSS variable, or null if the variable does not exist or an error occurs.
 */
export const getCSSVariableValue = (variable) => {
  try {
    if (typeof variable !== "string") {
      return null
    }
    const value = getComputedStyle(document.documentElement).getPropertyValue(
      variable,
    )
    return value ? value.trim() : null
  } catch (error) {
    return null
  }
}
