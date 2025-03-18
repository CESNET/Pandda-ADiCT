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
  id: {
    type: String,
    required: true,
  },
  snapshots: {
    type: Array,
    default() {
      return []
    },
  },
  timePickerState: {
    type: Object,
    required: true,
  },
  pickedSnapshotTs: {
    type: Date,
    required: true,
  },
  isArrayType: {
    type: Boolean,
    default: false,
  },
  valueMapper: {
    type: Function,
    default: (v) => `${v}`,
  },
})

const chartOptions = computed(() => {
  let scaleXOptions = { ...CHART_SCALE_X_OPTIONS }

  // Set the time range of the chart
  setChartDatetimeRange(scaleXOptions, props.timePickerState.from, props.timePickerState.to)

  return {
    ...CHART_COMMON_OPTIONS,
    scales: {
      x: scaleXOptions,
      y: {
        type: 'category',
        labels: [],
        offset: true,
        ticks: {
          display: true,
        },
        grid: {
          display: false,
        },
      },
    },
    plugins: {
      legend: false,
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const data = ctx.dataset.data[ctx.dataIndex]
            return `${ctx.formattedValue} (${Math.round(100 * data.c)} %)`
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
  let dataset = []

  const dataConv = (ts, value, confidence) => {
    return {
      x: ts,
      y: props.valueMapper(value),
      c: confidence,
    }
  }

  for (const s of props.snapshots) {
    // + 'Z' to treat as UTC
    const ts = new Date(s._time_created + 'Z')

    if (props.isArrayType) {
      if (!s[props.id]) {
        // Skip undefined values
        continue
      }
      dataset.push(...s[props.id].map((v, i) => dataConv(ts, v, s[props.id + '#c'][i])))
    } else {
      dataset.push(dataConv(ts, s[props.id], s[props.id + '#c']))
    }
  }

  return {
    datasets: [
      {
        data: dataset,
        pointBorderWidth: 0,
        pointBorderColor: '#ffffff',
        pointRadius: 4,
        pointHitRadius: 5,
        pointBackgroundColor(ctx) {
          // Edge case of empty dataset
          if (ctx.dataIndex === undefined) {
            return 'transparent'
          }

          const data = ctx.dataset.data[ctx.dataIndex]
          const cInt = Math.round(100 * data.c)
          return `hsl(${cInt}, 100%, 40%)`
        },
        showLine: false,
      },
    ],
  }
})
</script>

<template>
  <div v-if="snapshots.length > 0 && snapshots.some((s) => s[id])" class="chart">
    <Line :data="chartData" :options="chartOptions" />
  </div>
  <div v-else class="alert alert-info">No data</div>
</template>

<style lang="css" scoped>
.chart {
  height: 12rem;
}
</style>
