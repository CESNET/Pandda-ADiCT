<script setup>
import { inject, provide, watchEffect } from 'vue'
import { RouterView } from 'vue-router'

import { useRequestsStateStore } from '@/stores/requestsState'
import { useThemeStore } from '@/stores/theme'
import NavigationBar from '@/components/NavigationBar.vue'
import RequestsState from '@/components/RequestsState.vue'

const axios = inject('axios')
const requestsState = useRequestsStateStore()
const theme = useThemeStore()

/**
 * Universal data getter
 *
 * Provides loading and error tracking.
 */
async function getData(urlPath, ...params) {
  try {
    requestsState.started(urlPath)
    const res = await axios.get(urlPath, ...params)
    requestsState.finishedSuccess(urlPath)
    return res.data
  } catch (err) {
    requestsState.finishedError(urlPath, err.message || err)
  }
}

// Provide data getter to whole app
provide('getData', getData)

watchEffect(() => {
  document.documentElement.setAttribute('data-bs-theme', theme.theme)
})
</script>

<template>
  <NavigationBar />
  <RouterView />
  <RequestsState />
</template>
