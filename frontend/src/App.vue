<script setup>
import { inject, provide } from 'vue'
import { RouterView } from 'vue-router'

import { useRequestsStateStore } from '@/stores/requestsState'
import NavigationBar from '@/components/NavigationBar.vue'
import RequestsState from '@/components/RequestsState.vue'

const axios = inject('axios')
const requestsState = useRequestsStateStore()

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
</script>

<template>
  <NavigationBar />
  <RouterView />
  <RequestsState />
</template>
