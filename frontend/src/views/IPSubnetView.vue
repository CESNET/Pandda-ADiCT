<script setup>
import { computed, inject, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Netmask } from 'netmask'

import ActivityTimeline from '@/components/ActivityTimeline.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import SnapshotsTimePickerUrlSync from '@/components/SnapshotsTimePickerUrlSync.vue'

// Number of IP addresses loaded in parallel
const BATCH_SIZE = 32

const getData = inject('getData')
const route = useRoute()

// Parse subnet
const subnetInvalid = ref(false)
let _subnet = null
try {
  _subnet = new Netmask(`${route.params.ip}/${route.params.prefix}`)
} catch {
  subnetInvalid.value = true
}
const subnet = ref(_subnet)

// Primitive mutex
const loading = ref(false)

const timePickerState = ref({
  from: null,
  to: null,
  picked: null,
  latest: null,
  range: null,
  resampleUnitCount: null,
  resampleUnit: null,
})
const activity = ref([])
const addressesLoaded = ref(0)

/**
 * Number of addresses in subnet
 */
const addressCount = computed(() => {
  if (subnetInvalid.value) {
    return 0
  }
  if (subnet.value.bitmask >= 31) {
    // Special case for /31 and /32 due to RFC 3021
    return subnet.value.size
  }
  return subnet.value.size - 2
})

/**
 * Load progress percentage
 */
const loadProgress = computed(() => {
  if (subnetInvalid.value) {
    return 0
  }
  return (addressesLoaded.value / addressCount.value) * 100
})

/**
 * Loads data for single IP adress
 * @param address IP address
 */
async function loadAddress(address) {
  const data = await getData(`/entity/ip/${address}/master`, {
    params: {
      date_from: timePickerState.value.from,
      date_to: timePickerState.value.to,
    },
  })

  if (data?.activity) {
    activity.value = activity.value.concat(data.activity)
  }
}

/**
 * Loads data for batch of IP addresses
 *
 * All data is loaded in parallel.
 *
 * @param addresses Array of addresses to load
 */
async function loadBatch(addresses) {
  const dataPromises = []

  // Iterate over all IPs in subnet
  addresses.forEach((ip) => {
    // Push promise
    dataPromises.push(loadAddress(ip))
  })

  // Await all promises
  await Promise.all(dataPromises)
}

/**
 * Loads all data
 *
 * Subnet is divided into batches of `BATCH_SIZE` addresses. Batches are loaded
 * sequentially, but all addresses in a batch are loaded in parallel.
 */
async function load() {
  if (subnetInvalid.value) {
    return
  }

  // Prevent multiple loadings at the same time
  while (loading.value) {
    await new Promise((resolve) => setTimeout(resolve, 100))
  }
  loading.value = true

  // Store current route
  const loadingRoute = route.fullPath

  // Reset activity
  activity.value = []
  addressesLoaded.value = 0

  // Generate list of all addresses in subnet
  let addresses = []
  subnet.value.forEach((ip) => {
    addresses.push(ip)
  })

  // Load data in batches
  for (let i = 0; i < addresses.length; i += BATCH_SIZE) {
    if (route.fullPath !== loadingRoute) {
      // Route has changed, stop loading new batches
      break
    }

    const batch = addresses.slice(i, i + BATCH_SIZE)

    // Load batch
    await loadBatch(batch)

    // Update addresses loaded
    addressesLoaded.value += batch.length
  }

  loading.value = false
}

/**
 * Hook to update `timePickerState` value and reload data
 */
async function updateTimePickerState(newTimePickerState) {
  timePickerState.value = newTimePickerState
  await load()
}
</script>

<template>
  <main class="py-4">
    <div class="container">
      <div v-if="subnetInvalid" class="alert alert-danger">
        Invalid subnet <code>{{ $route.params.ip }}/{{ $route.params.prefix }}</code>
      </div>
      <div v-else>
        <div class="row mb-5">
          <div class="col col-lg-7 title">
            <h4>IP subnet</h4>
            <h1 class="h2 fw-bold">{{ subnet.base }}/{{ subnet.bitmask }}</h1>
            <div class="h5 text-muted">
              <span
                >{{ subnet.first }} &ndash; {{ subnet.last }} ({{ addressCount }}
                {{ addressCount == 1 ? 'address' : 'addresses' }})</span
              >
            </div>
          </div>
          <div class="col col-lg-5">
            <SnapshotsTimePickerUrlSync @update:timePickerState="updateTimePickerState" />
          </div>
        </div>

        <div>
          <h4 class="my-3">
            <div class="d-flex align-items-center">
              <span>Activity</span>
              <ProgressBar v-if="loadProgress < 100" :progress="loadProgress" class="w-100 ms-3" />
            </div>
          </h4>
          <ActivityTimeline
            v-if="activity.length > 0 || loading"
            :activity="activity"
            :time-picker-state="timePickerState"
            :picked-snapshot-ts="new Date(0)"
            :resample-unit-count="timePickerState.resampleUnitCount"
            :resample-unit="timePickerState.resampleUnit"
          />
          <div v-else class="alert alert-info">No data</div>
        </div>
      </div>
    </div>
  </main>
</template>
