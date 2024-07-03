/* Inspired by: https://michalzalecki.com/why-using-localStorage-directly-is-a-bad-idea/ */

export const safeStorage = (storage) => {
  let fallback = {}
  return {
    get(key) {
      try {
        return storage.getItem(key)
      } catch (_e) {
        return fallback[key] || null
      }
    },
    set(key, value) {
      try {
        storage.setItem(key, value)
      } catch (_e) {
        fallback[key] = value
      }
    },
    remove(key) {
      try {
        storage.removeItem(key)
      } catch (_e) {
        delete fallback[key]
      }
    },
    clear() {
      try {
        storage.clear()
      } catch (_e) {
        fallback = {}
      }
    },
  }
}
