<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-date-fns'

import {
  CHART_COMMON_OPTIONS,
  CHART_SCALE_X_OPTIONS,
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
})

const CHART_UNITS = ['pkt', 'flw', 'B']
const CHART_COLORS = ['#0DCAF0', '#198754', '#FFC107']

const chartOptions = computed(() => {
  let scaleXOptions = { ...CHART_SCALE_X_OPTIONS }

  // Set the time range of the chart
  setChartDatetimeRange(scaleXOptions, props.timePickerState.from, props.timePickerState.to)

  return {
    ...CHART_COMMON_OPTIONS,
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
  const data = props.activity.map((dp) => {
    return {
      t: new Date(dp.t2 + 'Z'),
      packets: dp.v.packets,
      flows: dp.v.flows,
      bytes: dp.v.bytes,
    }
  })

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
        pointRadius: 4,
        pointHitRadius: 5,
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
        pointRadius: 4,
        pointHitRadius: 5,
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
        pointRadius: 4,
        pointHitRadius: 5,
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
