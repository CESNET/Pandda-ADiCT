<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SnapshotsTimePicker from '@/components/SnapshotsTimePicker.vue'

const route = useRoute()
const router = useRouter()

const latest = ref(route.query.latest || false)
const ts = ref(route.query.ts)
const range = ref(parseInt(route.query.range) || 24 * 60)

// Pass through from child component
defineEmits(['update:timePickerState'])

// If no history timestamp is supplied, display latest snapshots
if (!ts.value) {
  latest.value = true
}

/**
 * Replaces the route with current parameters
 */
function replaceRoute() {
  let query = latest.value
    ? { latest: true, range: range.value }
    : { ts: ts.value, range: range.value }

  router.replace({ query })
}

// Sync URL with picker parameters
watch([latest, ts, range], replaceRoute)
</script>

<template>
  <SnapshotsTimePicker
    v-model:latest="latest"
    v-model:ts="ts"
    v-model:range="range"
    @update:timePickerState="$emit('update:timePickerState', $event)"
  />
</template>
