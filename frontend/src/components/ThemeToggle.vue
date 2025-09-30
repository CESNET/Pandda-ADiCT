<template>
  <button
    type="button"
    class="btn btn-dark"
    :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="theme.setTheme(isDark ? 'light' : 'dark')"
  >
    <span v-if="isDark" aria-hidden="true">☀️</span>
    <span v-else aria-hidden="true">🌙</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
const isDark = computed(() => theme.theme === 'dark')
</script>
