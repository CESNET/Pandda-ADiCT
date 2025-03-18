// Common charts options and functions

/**
 * Chart.js options for the X axis
 */
export const CHART_SCALE_X_OPTIONS = {
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

/**
 * Common Chart.js chart options
 */
export const CHART_COMMON_OPTIONS = {
  animation: {
    duration: 0,
  },
  maintainAspectRatio: false,
}

/**
 * Sets chart datetime range if both `dt_from` and `dt_to` are provided
 * @param {Object} chartScaleXOptions Options for the X axis
 * @param {String} dt_from Start date and time formatted like "1970-01-01T01:23"
 * @param {String} dt_to End date and time formatted like "1970-01-01T01:23"
 */
export function setChartDatetimeRange(chartScaleXOptions, dt_from, dt_to) {
  if (dt_from && dt_to) {
    // + 'Z' to treat as UTC
    chartScaleXOptions.min = new Date(dt_from + 'Z')
    chartScaleXOptions.max = new Date(dt_to + 'Z')
  }
}
