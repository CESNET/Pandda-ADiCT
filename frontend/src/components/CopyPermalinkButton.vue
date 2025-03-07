<script setup>
import { ref } from 'vue'

const props = defineProps({
  permalink: {
    type: String,
    required: true,
  },
  text: {
    type: String,
    default: 'Copy permalink',
  },
  defaultColorClass: {
    type: String,
    default: 'btn-primary',
  },
})

const copied = ref(false)

/**
 * Copies supplied permalink
 */
function copyPermalink() {
  navigator.clipboard.writeText(props.permalink)

  // Animate successful copy
  copied.value = true
  setTimeout(() => (copied.value = false), 1000)
}
</script>

<template>
  <div
    class="btn"
    :class="{ [defaultColorClass]: !copied, 'btn-success': copied }"
    @click="copyPermalink"
  >
    <i class="fa" :class="{ 'fa-clone': !copied, 'fa-check': copied }"></i>
    {{ text }}
  </div>
</template>
