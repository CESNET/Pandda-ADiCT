<script setup>
defineProps(['progress'])
</script>

<template>
  <div class="progress">
    <div
      class="progress-bar progress-bar-striped progress-bar-animated"
      role="progressbar"
      :style="{ width: `${progress}%` }"
    ></div>
  </div>
</template>
