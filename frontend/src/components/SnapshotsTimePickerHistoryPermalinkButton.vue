<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import dayjs from 'dayjs'

import CopyPermalinkButton from '@/components/CopyPermalinkButton.vue'

const route = useRoute()

const props = defineProps(['timePickerState'])

// Permalink to displayed history
const permalink = computed(() => {
  const range = props.timePickerState.range
  const ts = dayjs(props.timePickerState.picked)
    .subtract(range / 2, 'minute')
    .format('YYYY-MM-DDTHH:mm')
  return window.location.origin + route.path + `?ts=${ts}&range=${range}`
})
</script>

<template>
  <CopyPermalinkButton :permalink="permalink" default-color-class="btn-secondary" />
</template>
