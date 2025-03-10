<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'

ChartJS.register(...registerables)
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
})

const CHART_UNITS = ['pkt', 'flw', 'B']
const CHART_COLORS = ['#0DCAF0', '#198754', '#FFC107']

const chartOptions = computed(() => {
  let scaleXOptions = {
    type: 'time',
    time: {
      displayFormats: {
        millisecond: 'HH:mm:ss.SSS',
        second: 'HH:mm:ss',
        minute: 'HH:mm',
        hour: 'HH:mm',
      },
      tooltipFormat: 'dd.MM. HH:mm',
    },
    ticks: {
      autoSkip: false,
      maxRotation: 0,
      major: {
        enabled: true,
      },
    },
  }

  if (props.timePickerState.from && props.timePickerState.to) {
    // + 'Z' to treat as UTC
    scaleXOptions.min = new Date(props.timePickerState.from + 'Z')
    scaleXOptions.max = new Date(props.timePickerState.to + 'Z')
  }

  return {
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
    },
    animation: {
      duration: 0,
    },
    maintainAspectRatio: false,
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
