<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import CopyPermalinkButton from '@/components/CopyPermalinkButton.vue'

const route = useRoute()

const props = defineProps(['timePickerState'])

// Permalink to displayed latest data
const permalink = computed(() => {
  const range = props.timePickerState.range
  const ts = props.timePickerState.picked
  return window.location.origin + route.path + `?ts=${ts}&range=${range}`
})
</script>

<template>
  <CopyPermalinkButton :permalink="permalink" default-color-class="btn-secondary" />
</template>
