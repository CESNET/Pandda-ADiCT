<script setup>
defineProps(['value'])
</script>

<template>
  <span v-if="value == 'off'" class="badge bg-dark-subtle">
    <i class="fa fa-power-off me-2" aria-hidden="true"></i>Off
  </span>
  <span v-else-if="value == 'idle'" class="badge bg-dark-subtle border border-white">Idle</span>
  <span v-else-if="value == 'light'" class="badge bg-info text-dark">Light</span>
  <span v-else-if="value == 'medium'" class="badge bg-warning text-dark">Medium</span>
  <span v-else-if="value == 'high'" class="badge bg-danger">High</span>
</template>
