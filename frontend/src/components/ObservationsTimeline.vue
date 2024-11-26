<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'

ChartJS.register(...registerables)
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
  isArrayType: {
    type: Boolean,
    default: false,
  },
})

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

  if (props.snapshots.length > 0) {
    // + 'Z' to treat as UTC
    scaleXOptions.min = new Date(props.snapshots[0].ts + 'Z')
    scaleXOptions.max = new Date(props.snapshots[props.snapshots.length - 1].ts + 'Z')
  }

  return {
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
    },
    animation: {
      duration: 0,
    },
    maintainAspectRatio: false,
  }
})
const chartData = computed(() => {
  let dataset = []

  const dataConv = (ts, value, confidence) => {
    return {
      x: ts,
      y: `${value}`,
      c: confidence,
    }
  }

  // Extract `Data` objects from all snapshots
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
  <div v-if="snapshots.length > 0" class="chart">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<style lang="css" scoped>
.toggle-button {
  cursor: pointer;
}

.chart {
  height: 10rem;
}
</style>
