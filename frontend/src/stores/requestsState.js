import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

/**
 * Tracking of ongoing asynchronous HTTP requests
 *
 * There can be multiple concurent requests and in all cases,
 * loading and errors correspond to current state.
 */
export const useRequestsStateStore = defineStore('reqState', () => {
  const loadings = ref(new Set())
  const errors = ref({})

  // At least one request is in loading state
  const loading = computed(() => loadings.value.size > 0)

  /**
   * Signals start of transmission
   * @param {String} id Identifier (URL)
   */
  function started(id) {
    loadings.value.add(id)
  }

  /**
   * Signals finish of transmission
   * @param {String} id Identifier (URL)
   */
  function finishedSuccess(id) {
    loadings.value.delete(id)
  }

  /**
   * Signals finish of transmission with error message
   * @param {String} id Identifier (URL)
   * @param {String} msg Message
   */
  function finishedError(id, msg) {
    loadings.value.delete(id)
    errors.value[id] = msg
  }

  /**
   * Clears the error message
   * @param {String} id Identifier (URL)
   */
  function clearError(id) {
    delete errors.value[id]
  }

  return {
    loading,
    errors,
    started,
    finishedSuccess,
    finishedError,
    clearError,
  }
})
