<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

import ActivityClassBadge from '@/components/ActivityClassBadge.vue'
import ActivityTimeline from '@/components/ActivityTimeline.vue'
import ObservationsTimeline from '@/components/ObservationsTimeline.vue'
import OpenResolverBadge from '@/components/OpenResolverBadge.vue'
import TimelineSelect from '@/components/TimelineSelect.vue'

const getData = inject('getData')
const route = useRoute()
const router = useRouter()

const empty = ref(false)
const loaded = ref(false)
const dt = ref(route.query.dt)
const dt_from = computed(() => {
  return dayjs(dt.value).subtract(24, 'hour').format('YYYY-MM-DDTHH:mm')
})

const masterRecord = ref({})
const snapshots = ref([])
const latestSnapshot = computed(() => {
  if (snapshots.value.length > 0) {
    return snapshots.value[snapshots.value.length - 1]
  } else {
    return {}
  }
})

/**
 * Stringifies recog-attribute value
 *
 * Returns human-readable value for recog attribute value.
 */
function stringifyRecogValue(v) {
  let service = 'unknown'
  let os = 'unknown'

  if (v.service) {
    if (v.service.product && v.service.version) {
      service = `${v.service.product} ${v.service.version}`
    } else if (v.service.product) {
      service = v.service.product
    } else if (v.service.family) {
      service = v.service.family
    } else if (v.service.cpe23) {
      service = v.service.cpe23
    }
  }

  if (v.os) {
    if (v.os.vendor) {
      os = v.os.vendor
    } else if (v.os.product) {
      os = v.os.product
    } else if (v.os.family) {
      os = v.os.family
    } else if (v.os.cpe23) {
      os = v.os.cpe23
    }
  }

  return `${service} @ ${os}`
}

/**
 * Replaces the route with current parameters
 */
function replaceRoute() {
  router.replace({
    query: {
      dt: dt.value,
    },
  })
}

/**
 * Loads data
 */
async function load() {
  // Load IP detail
  const data = await getData('/entity/ip/' + route.params.eid, {
    params: {
      date_from: dt_from.value,
      date_to: dt.value,
    },
  })

  masterRecord.value = data.master_record
  snapshots.value = data.snapshots
  empty.value = data.empty
}

onMounted(async () => {
  await load()
  loaded.value = true
})

watch(dt, async () => {
  replaceRoute()
  await load()
})
</script>

<template>
  <main class="py-4">
    <div class="container">
      <TimelineSelect v-model="dt" class="mb-4" />

      <div class="title mb-5">
        <h4>IP detail</h4>
        <h1 class="h2 fw-bold">{{ $route.params.eid }}</h1>
        <div class="h3 row g-2">
          <div class="col col-auto" v-if="latestSnapshot?.hostname">
            <span class="badge text-bg-secondary me-2 mb-1">
              {{ latestSnapshot?.hostname }}
            </span>
            <ActivityClassBadge :value="latestSnapshot?.activity_class" class="me-2 mb-1" />
            <OpenResolverBadge :value="latestSnapshot?.open_resolver" class="me-2 mb-1" />
          </div>
        </div>
      </div>

      <div v-if="empty" class="alert alert-info">No data for selected datetime in DP³</div>
      <div v-else-if="loaded">
        <div v-if="snapshots.length > 0">
          <h4 class="my-3 d-flex align-items-center">
            <span>Latest data</span>
            <div class="d-inline-block ms-2 fs-5">
              <span class="badge rounded-pill border text-secondary">
                <i class="fa fa-clock-o me-2"></i
                >{{ dayjs.utc(latestSnapshot?._time_created).local().format('DD.MM. HH:mm') }}
              </span>
            </div>
          </h4>
          <div class="row">
            <div class="col col-md-4">
              <h6>
                Open ports
                <VTooltip class="d-inline-block ms-2">
                  <i class="fa fa-info text-secondary"></i>
                  <template #popper>
                    Open TCP ports, based on observation of sucessfully established connections.
                    <br />
                    Note that ports which no one connected to (or scanned) recently are not visible
                    this way.
                  </template>
                </VTooltip>
              </h6>
              <div v-if="(latestSnapshot?.open_ports || []).length > 0">
                <div
                  v-for="(port, i) in latestSnapshot?.open_ports.sort((a, b) => a - b)"
                  v-bind:key="i"
                  class="mb-2"
                >
                  <span class="badge bg-light text-dark fs-6">{{ port }}</span>
                  <span class="opacity-50 ms-1">
                    ({{ Math.round(100 * latestSnapshot['open_ports#c'][i]) }} % confidence)
                  </span>
                </div>
              </div>
              <div v-else class="alert alert-info">No data</div>
            </div>
            <div class="col col-md-4">
              <h6>
                SSH details
                <VTooltip class="d-inline-block ms-2">
                  <i class="fa fa-info text-secondary"></i>
                  <template #popper>
                    Information extracted from SSH banners sent by this IP (using Recog pattern
                    database).
                  </template>
                </VTooltip>
              </h6>
              <pre v-if="latestSnapshot?.recog_ssh">{{
                JSON.stringify(latestSnapshot?.recog_ssh, null, 2)
              }}</pre>
              <div v-else class="alert alert-info">No data</div>
            </div>
            <div class="col col-md-4">
              <h6>
                SMTP details
                <VTooltip class="d-inline-block ms-2">
                  <i class="fa fa-info text-secondary"></i>
                  <template #popper>
                    Information extracted from SMTP banners sent by this IP (using Recog pattern
                    database)
                  </template>
                </VTooltip>
              </h6>
              <pre v-if="latestSnapshot?.recog_smtp">{{
                JSON.stringify(latestSnapshot?.recog_smtp, null, 2)
              }}</pre>
              <div v-else class="alert alert-info">No data</div>
            </div>
          </div>
        </div>
        <div>
          <h4>
            History
            <VTooltip class="d-inline-block my-3">
              <i class="fa fa-info text-secondary fs-5"></i>
              <template #popper> 24-hour window until selected timestamp. </template>
            </VTooltip>
          </h4>
          <div class="mb-3">
            <h6>Open ports</h6>
            <ObservationsTimeline
              v-if="snapshots.length > 0"
              id="open_ports"
              :snapshots="snapshots"
              :latestSnapshot="latestSnapshot"
              :isArrayType="true"
            />
            <div v-else class="alert alert-info">No snapshots</div>
          </div>
          <div class="mb-3">
            <h6>
              SSH details
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Service and operating system identifiers parsed from recog SSH attribute values.
                </template>
              </VTooltip>
            </h6>
            <ObservationsTimeline
              v-if="snapshots.length > 0"
              id="recog_ssh"
              :snapshots="snapshots"
              :latestSnapshot="latestSnapshot"
              :isArrayType="true"
              :valueMapper="stringifyRecogValue"
            />
            <div v-else class="alert alert-info">No snapshots</div>
          </div>
          <div class="mb-3">
            <h6>
              SMTP details
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Service and operating system identifiers parsed from recog SMTP attribute values.
                </template>
              </VTooltip>
            </h6>
            <ObservationsTimeline
              v-if="snapshots.length > 0"
              id="recog_smtp"
              :snapshots="snapshots"
              :latestSnapshot="latestSnapshot"
              :isArrayType="true"
              :valueMapper="stringifyRecogValue"
            />
            <div v-else class="alert alert-info">No snapshots</div>
          </div>
          <div class="mb-3">
            <h6>Activity</h6>
            <ActivityTimeline
              v-if="masterRecord.activity && masterRecord.activity.length > 0"
              :activity="masterRecord.activity"
            />
            <div v-else class="alert alert-info">No data</div>
          </div>
        </div>
      </div>
      <div v-else class="spinner-border"></div>
    </div>
  </main>
</template>

<style lang="css" scoped>
pre {
  color: var(--bs-code-color);
}
</style>
