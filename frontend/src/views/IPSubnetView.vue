<script setup>
import { computed, inject, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Netmask } from 'netmask'

import ActivityTimeline from '@/components/ActivityTimeline.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import SnapshotsTimePickerUrlSync from '@/components/SnapshotsTimePickerUrlSync.vue'
import { formatSI } from '@/utils/commonCharts.js'

// Number of IP addresses loaded in parallel
const BATCH_SIZE = 32

const N_TOP_ACTIVE_IPS = 10

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
const activeIps = ref([])
const addressesLoaded = ref(0)
const topIncomingSort = ref({ key: 'flows' })
const topOutgoingSort = ref({ key: 'flows' })

/**
 * Aggregates flow and byte totals for one IP address from its activity
 */
function summarizeActivity(address, addressActivity) {
  const summary = {
    eid: address,
    in_flows: 0,
    out_flows: 0,
    in_bytes: 0,
    out_bytes: 0,
  }

  for (const dp of addressActivity || []) {
    summary.in_flows += dp?.v?.in_flows || 0
    summary.out_flows += dp?.v?.out_flows || 0
    summary.in_bytes += dp?.v?.in_bytes || 0
    summary.out_bytes += dp?.v?.out_bytes || 0
  }

  return summary
}

/**
 * Formats value with two decimals and SI unit
 */
function formatTwoDecimals(value, unit) {
  return formatSI(Number(value || 0).toFixed(2), unit)
}

/**
 * Gets sort state object for given direction
 * @returns 'flows' or 'bytes'
 */
function getSortState(direction) {
  return direction === 'in' ? topIncomingSort.value : topOutgoingSort.value
}

/**
 * Sets sort key for top active IPs of given direction
 *
 * Used to change the sorting.
 *
 * @param direction 'in' or 'out'
 * @param key 'flows' or 'bytes'
 */
function setTopActiveIpsSort(direction, key) {
  const sortState = getSortState(direction)

  sortState.key = key
}

/**
 * Gets sort and other keys for given direction and metric key
 *
 * @param direction 'in' or 'out'
 * @param metricKey 'flows' or 'bytes'
 */
function getActivitySortKeys(direction, metricKey) {
  const flowsKey = `${direction}_flows`
  const bytesKey = `${direction}_bytes`

  return metricKey === 'bytes'
    ? { sortKey: bytesKey, otherKey: flowsKey }
    : { sortKey: flowsKey, otherKey: bytesKey }
}

/**
 * Returns top N active IPs sorted by selected metric and direction
 */
function getTopNActiveIps(direction, n = N_TOP_ACTIVE_IPS) {
  const sortState = getSortState(direction)
  const { sortKey, otherKey } = getActivitySortKeys(direction, sortState.key)

  return [...activeIps.value]
    .sort((a, b) => {
      if (b[sortKey] !== a[sortKey]) {
        return b[sortKey] - a[sortKey]
      }

      if (b[otherKey] !== a[otherKey]) {
        return b[otherKey] - a[otherKey]
      }

      return a.eid.localeCompare(b.eid)
    })
    .slice(0, n)
}

// Computed properties for top active IPs and their metric labels
const topIncomingActiveIps = computed(() => getTopNActiveIps('in'))
const topOutgoingActiveIps = computed(() => getTopNActiveIps('out'))
const topIncomingMetricLabel = computed(() =>
  topIncomingSort.value.key === 'bytes' ? 'bytes' : 'flows',
)
const topOutgoingMetricLabel = computed(() =>
  topOutgoingSort.value.key === 'bytes' ? 'bytes' : 'flows',
)

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

  activeIps.value.push(summarizeActivity(address, data?.activity))
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
  activeIps.value = []
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
          <div v-if="activity.length > 0 || loading">
            <h6>Outgoing</h6>
            <ActivityTimeline
              :activity="activity"
              :time-picker-state="timePickerState"
              :picked-snapshot-ts="new Date(0)"
              :resample-unit-count="timePickerState.resampleUnitCount"
              :resample-unit="timePickerState.resampleUnit"
              :incoming-direction="false"
            />
            <h6>Incoming</h6>
            <ActivityTimeline
              :activity="activity"
              :time-picker-state="timePickerState"
              :picked-snapshot-ts="new Date(0)"
              :resample-unit-count="timePickerState.resampleUnitCount"
              :resample-unit="timePickerState.resampleUnit"
              :incoming-direction="true"
            />
          </div>
          <div v-else class="alert alert-info">No data</div>
        </div>

        <div class="mt-5">
          <h4 class="my-3">Top active IP addresses</h4>
          <div class="row g-4 align-items-start">
            <div class="col-12 col-xl-6 top-active-table-col">
              <h6>Incoming activity (sorted by {{ topIncomingMetricLabel }})</h6>
              <div v-if="topIncomingActiveIps.length > 0" class="table-responsive">
                <table class="table table-hover align-middle">
                  <thead>
                    <tr>
                      <th scope="col">#</th>
                      <th scope="col">IP address</th>
                      <th
                        scope="col"
                        class="text-end"
                        :aria-sort="topIncomingSort.key === 'flows' ? 'descending' : 'none'"
                      >
                        <button
                          type="button"
                          class="btn btn-link p-0 text-decoration-none text-reset border-0 sort-toggle"
                          :class="{ active: topIncomingSort.key === 'flows' }"
                          :aria-pressed="topIncomingSort.key === 'flows'"
                          @click="setTopActiveIpsSort('in', 'flows')"
                        >
                          Flows
                        </button>
                      </th>
                      <th
                        scope="col"
                        class="text-end"
                        :aria-sort="topIncomingSort.key === 'bytes' ? 'descending' : 'none'"
                      >
                        <button
                          type="button"
                          class="btn btn-link p-0 text-decoration-none text-reset border-0 sort-toggle"
                          :class="{ active: topIncomingSort.key === 'bytes' }"
                          :aria-pressed="topIncomingSort.key === 'bytes'"
                          @click="setTopActiveIpsSort('in', 'bytes')"
                        >
                          Bytes
                        </button>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in topIncomingActiveIps" :key="`in-${item.eid}`">
                      <th scope="row">{{ index + 1 }}</th>
                      <td>
                        <RouterLink
                          :to="{ name: 'ip', params: { eid: item.eid } }"
                          class="text-decoration-none"
                        >
                          {{ item.eid }}
                        </RouterLink>
                      </td>
                      <td class="text-end">{{ formatTwoDecimals(item.in_flows, 'flw') }}</td>
                      <td class="text-end">{{ formatTwoDecimals(item.in_bytes, 'B') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="alert alert-info">No data</div>
            </div>

            <div class="col-12 col-xl-6 top-active-table-col">
              <h6>Outgoing activity (sorted by {{ topOutgoingMetricLabel }})</h6>
              <div v-if="topOutgoingActiveIps.length > 0" class="table-responsive">
                <table class="table table-hover align-middle">
                  <thead>
                    <tr>
                      <th scope="col">#</th>
                      <th scope="col">IP address</th>
                      <th
                        scope="col"
                        class="text-end"
                        :aria-sort="topOutgoingSort.key === 'flows' ? 'descending' : 'none'"
                      >
                        <button
                          type="button"
                          class="btn btn-link p-0 text-decoration-none text-reset border-0 sort-toggle"
                          :class="{ active: topOutgoingSort.key === 'flows' }"
                          :aria-pressed="topOutgoingSort.key === 'flows'"
                          @click="setTopActiveIpsSort('out', 'flows')"
                        >
                          Flows
                        </button>
                      </th>
                      <th
                        scope="col"
                        class="text-end"
                        :aria-sort="topOutgoingSort.key === 'bytes' ? 'descending' : 'none'"
                      >
                        <button
                          type="button"
                          class="btn btn-link p-0 text-decoration-none text-reset border-0 sort-toggle"
                          :class="{ active: topOutgoingSort.key === 'bytes' }"
                          :aria-pressed="topOutgoingSort.key === 'bytes'"
                          @click="setTopActiveIpsSort('out', 'bytes')"
                        >
                          Bytes
                        </button>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in topOutgoingActiveIps" :key="`out-${item.eid}`">
                      <th scope="row">{{ index + 1 }}</th>
                      <td>
                        <RouterLink
                          :to="{ name: 'ip', params: { eid: item.eid } }"
                          class="text-decoration-none"
                        >
                          {{ item.eid }}
                        </RouterLink>
                      </td>
                      <td class="text-end">{{ formatTwoDecimals(item.out_flows, 'flw') }}</td>
                      <td class="text-end">{{ formatTwoDecimals(item.out_bytes, 'B') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="alert alert-info">No data</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.sort-toggle {
  transition: color 0.15s ease;
}

.sort-toggle.active {
  font-weight: 700;
  text-shadow: 0 0 0.5rem color-mix(in srgb, var(--bs-primary) 55%, transparent);
}

@media (min-width: 1200px) {
  .top-active-table-col + .top-active-table-col {
    border-left: 1px solid var(--bs-border-color);
    padding-left: 1.5rem;
  }
}
</style>
