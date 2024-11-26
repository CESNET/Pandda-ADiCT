<script setup>
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import { onMounted, ref, watch } from 'vue'

dayjs.extend(utc)

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const localTime = ref(localTimeFromUTC(props.modelValue))
const points = ref([])

/**
 * Converts day.js instance to short ISO string
 * @param {Object} dayjsInst Day.js instance
 */
function dayjsToShortISO(dayjsInst) {
  return dayjsInst.format('YYYY-MM-DDTHH:mm')
}

/**
 * Parses local time from UTC timestamp
 * @param ts Any timestamp accepted by Day.js constructor
 */
function localTimeFromUTC(ts) {
  if (!ts) {
    return ''
  }
  return dayjsToShortISO(dayjs.utc(ts).local())
}

onMounted(async () => {
  const now = dayjs()

  if (!localTime.value) {
    localTime.value = dayjsToShortISO(now)
  }

  points.value = [
    { title: '-14d', dt: now.subtract(14, 'day') },
    { title: '-7d', dt: now.subtract(7, 'day') },
    { title: '-5d', dt: now.subtract(5, 'day') },
    { title: '-4d', dt: now.subtract(4, 'day') },
    { title: '-3d', dt: now.subtract(3, 'day') },
    { title: '-2d', dt: now.subtract(2, 'day') },
    { title: '-24h', dt: now.subtract(24, 'hour') },
    { title: 'Now', dt: now },
  ]
})

watch(localTime, (v) => {
  // Convert local time to UTC and emit
  emit('update:modelValue', dayjsToShortISO(dayjs(v).utc()))
})
</script>

<template>
  <div class="row">
    <div class="col-md-8 mb-3">
      <div class="timeline">
        <div
          v-for="p in points"
          :key="p.title"
          class="point-container"
          :class="{ active: p.dt.isSame(localTime, 'minute') }"
          @click="localTime = dayjsToShortISO(p.dt)"
        >
          <div class="line"></div>
          <div class="point"></div>
          <div class="text">{{ p.title }}</div>
        </div>
      </div>
    </div>
    <div class="col-md-4 mb-3">
      <div class="input-group">
        <span class="input-group-text">
          <i class="fa fa-calendar"></i>
        </span>
        <input type="datetime-local" class="form-control" v-model="localTime" />
      </div>
    </div>
  </div>
</template>

<style lang="css" scoped>
.timeline {
  display: flex;
  justify-content: center;
}

.timeline .point-container {
  width: calc(100% / 7);
  text-align: center;
  color: var(--bs-secondary);
  cursor: pointer;
}

.timeline .point-container .point {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  background: var(--bs-secondary);
  border-radius: 50%;
  position: relative;
  z-index: 2;
}

.timeline .point-container .line {
  width: 100%;
  height: 4px;
  background: var(--bs-secondary);
  position: relative;
  top: calc(1rem - 3px);
  z-index: 1;
}

.timeline .point-container:first-child .line {
  width: 50%;
  margin-left: 50%;
}

.timeline .point-container:last-child .line {
  width: 50%;
  margin-right: 50%;
}

.timeline .point-container.active {
  color: var(--bs-body-color);
}

.timeline .point-container.active .point {
  background: var(--bs-body-color);
}
</style>
