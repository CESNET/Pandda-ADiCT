<script setup>
import { computed, watch } from 'vue'

import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'

dayjs.extend(utc)

const RANGES = [
  { value: 24 * 60, title: '24h' },
  { value: 2 * 24 * 60, title: '2d' },
  { value: 4 * 24 * 60, title: '4d' },
  { value: 7 * 24 * 60, title: '1w' },
  { value: 14 * 24 * 60, title: '14d' },
  { value: 30 * 24 * 60, title: '30d' },
]

// Models
const latest = defineModel('latest')
const ts = defineModel('ts', {
  get(value) {
    if (!value) {
      return dayjs.utc().local()
    }
    return dayjs.utc(value).local()
  },
  set(value) {
    if (!value) {
      return null
    }
    return dayjsToShortISO(dayjs(value).utc())
  },
})
const range = defineModel('range')

/**
 * Returns nearest index of `RANGES` element corresponding to the `range` value
 */
const rangesIndex = computed(() => {
  let nearestIndex = 0
  let minimumDiff = Infinity

  for (let i = 0; i < RANGES.length; i++) {
    let diff = Math.abs(range.value - RANGES[i].value)
    if (diff < minimumDiff) {
      nearestIndex = i
      minimumDiff = diff
    }
  }

  return nearestIndex
})

const emit = defineEmits(['update:timePickerState'])

/**
 * Converts day.js instance to short ISO string
 * @param {Object} dayjsInst Day.js instance
 */
function dayjsToShortISO(dayjsInst) {
  return dayjsInst.format('YYYY-MM-DDTHH:mm')
}

/**
 * Switches to the "latest" tab
 */
function switchToLatest() {
  if (latest.value) {
    return
  }

  latest.value = true
  ts.value = null
}

/**
 * Switches to the "history" tab
 *
 * If switching from "latest" tab, the corresponding time interval should be
 * exactly the same.
 */
function switchToHistory() {
  if (!latest.value) {
    return
  }

  latest.value = false
  ts.value = ts.value.subtract(range.value / 2, 'minute')
}

/**
 * Calculates time picker state
 *
 * Includes timestamp for [from, to] range usable in API.
 */
function calculateTimePickerState() {
  let tsFrom, tsTo

  if (latest.value) {
    // [ts - range, ts] for latest
    tsFrom = ts.value.subtract(range.value, 'minute')
    tsTo = ts.value
  } else {
    // [ts - range/2, ts + range/2] for history
    tsFrom = ts.value.subtract(range.value / 2, 'minute')
    tsTo = ts.value.add(range.value / 2, 'minute')
  }

  // Add small time increment to include snapshots created with negligible
  // time offset (e.g. range 20:00 - 22:00 should include snapshots
  // created at 22:00:00.001)
  tsTo = tsTo.add(1, 'minute')

  return {
    from: dayjsToShortISO(tsFrom.utc()),
    to: dayjsToShortISO(tsTo.utc()),
    picked: dayjsToShortISO(ts.value.utc()),
    latest: latest.value,
    range: range.value,
  }
}

// Recalculate timestamp range initially and on every change
emit('update:timePickerState', calculateTimePickerState())
watch([latest, ts, range], () => {
  emit('update:timePickerState', calculateTimePickerState())
})
</script>

<template>
  <div class="card text-center">
    <div class="card-header">
      <ul class="nav nav-tabs card-header-tabs">
        <li class="nav-item">
          <a class="nav-link" :class="{ active: latest }" @click="switchToLatest">Latest data</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" :class="{ active: !latest }" @click="switchToHistory"
            >Historical view</a
          >
        </li>
      </ul>
    </div>
    <div class="card-body">
      <div v-if="latest">
        <div class="btn-group w-100" role="group">
          <div
            v-for="rangesElement in RANGES.slice().reverse()"
            :key="rangesElement.value"
            class="btn"
            :class="{
              'btn-secondary': range == rangesElement.value,
              'btn-outline-secondary': range != rangesElement.value,
            }"
            @click="range = rangesElement.value"
          >
            {{ rangesElement.title }}
          </div>
        </div>
        <div class="btn-group w-100 mt-1" role="group">
          <button
            class="btn btn-secondary"
            @click="range = RANGES[rangesIndex + 1].value"
            :disabled="rangesIndex == RANGES.length - 1"
          >
            <i class="fa fa-search-minus"></i>
          </button>
          <button
            class="btn btn-secondary"
            @click="range = RANGES[rangesIndex - 1].value"
            :disabled="rangesIndex == 0"
          >
            <i class="fa fa-search-plus"></i>
          </button>
        </div>
      </div>
      <div v-else>
        <div class="row">
          <div class="col col-md-8">
            <div class="input-group">
              <span class="input-group-text">
                <i class="fa fa-calendar"></i>
              </span>
              <input
                type="datetime-local"
                class="form-control"
                :value="dayjsToShortISO(ts)"
                @input="ts = dayjs($event.target.value)"
              />
            </div>
            <div class="btn-group w-100 mt-1" role="group">
              <div class="btn btn-secondary" @click="ts = ts.subtract(range, 'minute')">
                <i class="fa fa-arrow-left"></i>
              </div>
              <div class="btn btn-secondary" @click="ts = ts.add(range, 'minute')">
                <i class="fa fa-arrow-right"></i>
              </div>
            </div>
          </div>
          <div class="col col-md-4">
            <div class="input-group">
              <span class="input-group-text">
                <i class="fa fa-arrows-h"></i>
              </span>
              <select class="form-control" v-model="range">
                <option
                  v-for="rangesElement in RANGES"
                  :key="rangesElement.value"
                  :value="rangesElement.value"
                >
                  {{ rangesElement.title }}
                </option>
              </select>
            </div>
            <div class="btn-group w-100 mt-1" role="group">
              <button
                class="btn btn-secondary"
                @click="range = RANGES[rangesIndex - 1].value"
                :disabled="rangesIndex == 0"
              >
                <i class="fa fa-search-plus"></i>
              </button>
              <button
                class="btn btn-secondary"
                @click="range = RANGES[rangesIndex + 1].value"
                :disabled="rangesIndex == RANGES.length - 1"
              >
                <i class="fa fa-search-minus"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="css" scoped>
.nav-link {
  cursor: pointer;
}
</style>
