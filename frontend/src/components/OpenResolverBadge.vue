<script setup>
defineProps(['value'])
</script>

<template>
  <span v-if="value === true" class="badge bg-danger">
    <i class="fa fa-exclamation-triangle me-2" aria-hidden="true"></i>Open resolver
  </span>
  <span v-else-if="value === false" class="badge bg-secondary">
    <i class="fa fa-check me-2" aria-hidden="true"></i>No open resolver
  </span>
</template>
