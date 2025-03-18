// Common charts options and functions

import { dateCeil } from './datetime'

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

/**
 * Resamples data (datapoints) to have `bucketCount` number of buckets
 *
 * `data` should consist of objects that include key specified by `dtKey`
 * representing datapoint timestamp
 *
 * @param {Array} data Timed data to resample
 * @param {String} dtKey Key of the timestamp in the `data` objects (should be
 *   of `Date` type)
 * @param {Number} unitCount Number of `unit` to group into a bucket
 * @param {String} unit Unit to group into a bucket (e.g. 'minute', 'hour')
 * @param {Function} reduceFn Function to reduce data of a single bucket.
 *   Should take arguments (bucketData, bucketDt) and return array of one
 *   or more objects.
 * @returns {Array} Array of objects with the same keys as the `data` objects,
 *   but reduced and rounded to the nearest bucket
 */
export function resampleTimedData(data, dtKey, unitCount, unit, reduceFn) {
  if (!data) {
    return []
  }

  // Map to guarantee insertion order
  let buckets = new Map()

  // Split data into buckets
  for (const item of data) {
    const bucketKey = dateCeil(item[dtKey], unitCount, unit).getTime()
    if (!buckets.has(bucketKey)) {
      buckets.set(bucketKey, [])
    }
    buckets.get(bucketKey).push(item)
  }

  // Reduce each bucket and convert to array
  let result = []
  for (const [key, bucket] of buckets) {
    let bucketDt = new Date(key)
    result.push(...reduceFn(bucket, bucketDt).map((item) => ({ [dtKey]: bucketDt, ...item })))
  }
  return result
}
