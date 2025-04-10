<script setup>
import { computed, inject, onMounted, ref } from 'vue'

import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

import SnapshotsTimePickerUrlSync from '@/components/SnapshotsTimePickerUrlSync.vue'

const getData = inject('getData')

const props = defineProps({
  etype: {
    type: String,
    required: true,
  },
  eid: {
    type: String,
    required: true,
  },
})

const empty = ref(false)
const loaded = ref(false)
const timePickerState = ref({
  from: null,
  to: null,
  picked: null,
  latest: null,
  range: null,
  resampleUnitCount: null,
  resampleUnit: null,
})

const masterRecord = ref({})
const snapshots = ref([])

// Picked snapshot is either:
// - latest one if `timePickerState.latest == true`
// - the last one before midpoint of the selected interval otherwise
//   (midpoint is `timePickerState.picked`)
const pickedSnapshot = computed(() => {
  if (snapshots.value.length > 0) {
    if (timePickerState.value.latest) {
      // Select last (latest) one
      return snapshots.value[snapshots.value.length - 1]
    } else {
      // Find "midpoint"
      let midpointSnapshot = null
      let minTsDiff = Infinity
      for (let i = 0; i < snapshots.value.length; i++) {
        let snapshotTs = dayjs(snapshots.value[i]._time_created).millisecond(0).second(0)
        let tsDiff = dayjs(timePickerState.value.picked).diff(snapshotTs)
        if (tsDiff >= 0 && tsDiff < minTsDiff) {
          minTsDiff = tsDiff
          midpointSnapshot = snapshots.value[i]
        }
      }
      return midpointSnapshot
    }
  } else {
    return null
  }
})

// Shortcut for picked snapshot timestamp
const pickedSnapshotTs = computed(() => {
  return dayjs.utc(pickedSnapshot.value?._time_created).local()
})

/**
 * Loads data
 */
async function load() {
  const data = await getData(`/entity/${props.etype}/${props.eid}`, {
    params: {
      date_from: timePickerState.value.from,
      date_to: timePickerState.value.to,
    },
  })

  masterRecord.value = data.master_record
  snapshots.value = data.snapshots
  empty.value = data.empty
}

/**
 * Hook to update `timePickerState` value and reload data
 */
async function updateTimePickerState(newTimePickerState) {
  timePickerState.value = newTimePickerState
  await load()
}

onMounted(async () => {
  await load()
  loaded.value = true
})
</script>

<template>
  <main class="py-4">
    <div class="container">
      <div class="row mb-5">
        <div class="col col-lg-7 title">
          <slot
            name="header"
            :master-record="masterRecord"
            :snapshots="snapshots"
            :picked-snapshot="pickedSnapshot"
            :picked-snapshot-ts="pickedSnapshotTs"
            :time-picker-state="timePickerState"
          ></slot>
        </div>
        <div class="col col-lg-5">
          <SnapshotsTimePickerUrlSync @update:timePickerState="updateTimePickerState" />
        </div>
      </div>

      <div v-if="empty" class="alert alert-info">No data for selected datetime in DP³</div>
      <div v-else-if="loaded">
        <slot
          :master-record="masterRecord"
          :snapshots="snapshots"
          :picked-snapshot="pickedSnapshot"
          :picked-snapshot-ts="pickedSnapshotTs"
          :time-picker-state="timePickerState"
        ></slot>
      </div>
      <div v-else class="spinner-border"></div>
    </div>
  </main>
</template>
