import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

/**
 * Tracking of the current theme (dark or light).
 */
export const useThemeStore = defineStore('theme', () => {
  const STORAGE_KEY = 'theme'
  const theme = ref(initialTheme())

  /**
   * Determine the initial theme mode based on local storage or system preference.
   */
  function initialTheme() {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'dark' || saved === 'light') return saved
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  /**
   * Sets the current theme.
   */
  function setTheme(newTheme) {
    theme.value = newTheme === 'dark' ? 'dark' : 'light'
    localStorage.setItem(STORAGE_KEY, theme.value)
  }

  return {
    theme: computed(() => theme.value),
    isDark: computed(() => theme.value === 'dark'),
    setTheme,
  }
})
