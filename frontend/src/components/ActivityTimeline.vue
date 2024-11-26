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
})

const chartOptions = computed(() => {
  const UNITS = {
    0: 'pkt',
    1: 'flw',
    2: 'B',
  }

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

  if (props.activity.length > 0) {
    // + 'Z' to treat as UTC
    scaleXOptions.min = new Date(props.activity[0].t2 + 'Z')
    scaleXOptions.max = new Date(props.activity[props.activity.length - 1].t2 + 'Z')
  }

  return {
    scales: {
      x: scaleXOptions,
      packets: {
        ticks: {
          callback: (v) => `${v} ${UNITS[0]}`,
        },
        min: 0,
      },
      flows: {
        ticks: {
          callback: (v) => `${v} ${UNITS[1]}`,
        },
        min: 0,
      },
      bytes: {
        ticks: {
          callback: (v) => `${v} ${UNITS[2]}`,
        },
        min: 0,
      },
    },
    plugins: {
      legend: false,
      tooltip: {
        callbacks: {
          label: (item) => {
            let unit = UNITS[item.datasetIndex]
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
        borderColor: '#DC3545',
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
        borderColor: '#FFC107',
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
        borderColor: '#0D6EFD',
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
