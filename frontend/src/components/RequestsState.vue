<script setup>
import { useRequestsStateStore } from '@/stores/requestsState'

const requestsState = useRequestsStateStore()
</script>

<template>
  <div v-if="requestsState.loading" class="spinner-border position-fixed bottom-0 end-0 m-3"></div>
  <div class="toast-container position-fixed end-0 p-3">
    <div
      v-for="(err, errId) in requestsState.errors"
      :key="errId"
      class="toast align-items-center text-bg-danger border-0 show"
    >
      <div class="d-flex">
        <div class="toast-body">
          <code>{{ errId }}</code
          >: {{ err }}
        </div>
        <button
          type="button"
          class="btn-close btn-close-white me-2 m-auto"
          @click="requestsState.clearError(errId)"
        ></button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="css">
.toast-container {
  bottom: 3rem;
}
.text-bg-danger code {
  color: inherit;
}
</style>
