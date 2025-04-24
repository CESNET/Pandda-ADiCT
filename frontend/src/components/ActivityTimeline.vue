<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-date-fns'

import {
  CHART_COMMON_OPTIONS,
  CHART_SCALE_X_OPTIONS,
  resampleTimedData,
  setChartDatetimeRange,
} from '@/utils/commonCharts.js'

ChartJS.register(...registerables, annotationPlugin)
ChartJS.defaults.color = '#dee2e6'
ChartJS.defaults.borderColor = '#495057'

const props = defineProps({
  activity: {
    type: Array,
    required: true,
  },
  timePickerState: {
    type: Object,
    required: true,
  },
  pickedSnapshotTs: {
    type: Date,
    required: true,
  },
  resampleUnitCount: {
    type: Number,
    required: true,
  },
  resampleUnit: {
    type: String,
    required: true,
  },
  incomingDirection: {
    type: Boolean,
    default: false,
  },
})

const CHART_UNITS = ['pkt', 'flw', 'B']
const CHART_COLORS = ['#0DCAF0', '#198754', '#FFC107']

const DIRECTION_PREFIX = props.incomingDirection ? 'in_' : 'out_'

const chartOptions = computed(() => {
  let scaleXOptions = { ...CHART_SCALE_X_OPTIONS }

  // Set the time range of the chart
  setChartDatetimeRange(scaleXOptions, props.timePickerState.from, props.timePickerState.to)

  return {
    ...CHART_COMMON_OPTIONS,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    scales: {
      x: scaleXOptions,
      packets: {
        ticks: {
          callback: (v) => `${v} ${CHART_UNITS[0]}`,
          color: CHART_COLORS[0],
        },
        grid: { tickColor: CHART_COLORS[0], drawOnChartArea: false },
        border: { color: CHART_COLORS[0] },
        min: 0,
      },
      flows: {
        ticks: {
          callback: (v) => `${v} ${CHART_UNITS[1]}`,
          color: CHART_COLORS[1],
        },
        grid: { tickColor: CHART_COLORS[1], drawOnChartArea: false },
        border: { color: CHART_COLORS[1] },
        min: 0,
      },
      bytes: {
        ticks: {
          callback: (v) => `${v} ${CHART_UNITS[2]}`,
          color: CHART_COLORS[2],
        },
        grid: { tickColor: CHART_COLORS[2] },
        border: { color: CHART_COLORS[2] },
        min: 0,
      },
    },
    plugins: {
      legend: false,
      tooltip: {
        callbacks: {
          label: (item) => {
            let unit = CHART_UNITS[item.datasetIndex]
            return `${item.formattedValue} ${unit}`
          },
        },
        usePointStyle: true,
      },
      annotation: {
        annotations: {
          line1: {
            type: 'line',
            xMin: props.pickedSnapshotTs,
            xMax: props.pickedSnapshotTs,
            borderColor: '#d980fa',
            borderWidth: 2,
          },
        },
      },
    },
  }
})
const chartData = computed(() => {
  let data = props.activity.map((dp) => {
    return {
      t: new Date(dp.t2 + 'Z'),
      packets: dp.v[DIRECTION_PREFIX + 'packets'],
      flows: dp.v[DIRECTION_PREFIX + 'flows'],
      bytes: dp.v[DIRECTION_PREFIX + 'bytes'],
    }
  })

  // Resample data to avoid too many points
  data = resampleTimedData(
    data,
    't',
    props.resampleUnitCount,
    props.resampleUnit,
    (bucketData, bucketDt) => {
      return [
        {
          t: bucketDt,
          packets: bucketData.reduce((acc, dp) => acc + dp.packets, 0),
          flows: bucketData.reduce((acc, dp) => acc + dp.flows, 0),
          bytes: bucketData.reduce((acc, dp) => acc + dp.bytes, 0),
        },
      ]
    },
  )

  // Round number of packets, flows, and bytes
  // Only applied to values >= 10. This is to avoid confusion, because user
  // doesn't expect to see 102.34 bytes transferred. For smaller values, it
  // might be better to show the exact value.
  // (This is due to redistribution of long flows into smaller time windows.)
  for (const dp of data) {
    if (dp.packets >= 10) {
      dp.packets = Math.round(dp.packets)
    }
    if (dp.flows >= 10) {
      dp.flows = Math.round(dp.flows)
    }
    if (dp.bytes >= 10) {
      dp.bytes = Math.round(dp.bytes)
    }
  }

  return {
    datasets: [
      {
        label: 'Packets',
        yAxisID: 'packets',
        data,
        parsing: {
          xAxisKey: 't',
          yAxisKey: 'packets',
        },
        borderColor: CHART_COLORS[0],
        pointRadius: 6,
        pointHoverRadius: 6,
        pointHitRadius: 7,
        pointStyle: 'rect',
      },
      {
        label: 'Flows',
        yAxisID: 'flows',
        data,
        parsing: {
          xAxisKey: 't',
          yAxisKey: 'flows',
        },
        borderColor: CHART_COLORS[1],
        pointRadius: 6,
        pointHoverRadius: 6,
        pointHitRadius: 7,
        pointStyle: 'circle',
      },
      {
        label: 'Bytes',
        yAxisID: 'bytes',
        data,
        parsing: {
          xAxisKey: 't',
          yAxisKey: 'bytes',
        },
        borderColor: CHART_COLORS[2],
        pointRadius: 6,
        pointHoverRadius: 6,
        pointHitRadius: 7,
        pointStyle: 'star',
      },
    ],
  }
})
</script>

<template>
  <div v-if="activity && activity.length > 0" class="chart">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<style lang="css" scoped>
.chart {
  height: 20rem;
}
</style>
