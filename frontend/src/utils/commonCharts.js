// Common charts options and functions

import { dateFloor, durationMs } from './datetime'

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
 * Gets text color based on current theme
 */
export function themeTextColor(isDark) {
  return isDark ? '#DEE2E6' : '#212529'
}

/**
 * Sets chart datetime range if both `dtFrom` and `dtTo` are provided
 * @param {Object} chartScaleXOptions Options for the X axis
 * @param {String} dtFrom Start date and time formatted like "1970-01-01T01:23"
 * @param {String} dtTo End date and time formatted like "1970-01-01T01:23"
 * @returns {undefined}
 */
export function setChartDatetimeRange(chartScaleXOptions, dtFrom, dtTo) {
  if (dtFrom && dtTo) {
    // + 'Z' to treat as UTC
    chartScaleXOptions.min = new Date(dtFrom + 'Z')
    chartScaleXOptions.max = new Date(dtTo + 'Z')
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
 * @param {Boolean} addEmptyBuckets If true, empty buckets will be added
 *   to the result. If false, only buckets with data will be returned.
 *   Default is true.
 * @returns {Array} Array of objects with the same keys as the `data` objects,
 *   but reduced and rounded to the nearest bucket
 */
export function resampleTimedData(data, dtKey, unitCount, unit, reduceFn, addEmptyBuckets = true) {
  if (!data) {
    return []
  }

  // Map instead of object to allow for `Date` keys
  let buckets = new Map()

  // Split data into buckets
  for (const item of data) {
    const bucketKey = dateFloor(item[dtKey], unitCount, unit).getTime()
    if (!buckets.has(bucketKey)) {
      buckets.set(bucketKey, [])
    }
    buckets.get(bucketKey).push(item)
  }

  // If empty buckets are requested, add them
  if (addEmptyBuckets && buckets.size > 0) {
    const bucketKeys = Array.from(buckets.keys())
    const minKey = Math.min(...bucketKeys)
    const maxKey = Math.max(...bucketKeys)
    const increment = durationMs(unitCount, unit)
    for (let key = minKey; key <= maxKey; key += increment) {
      if (!buckets.has(key)) {
        buckets.set(key, [])
      }
    }
  }

  // Reduce each bucket and convert to array
  let result = []
  for (const [key, bucket] of buckets) {
    let bucketDt = new Date(key)
    result.push(...reduceFn(bucket, bucketDt).map((item) => ({ [dtKey]: bucketDt, ...item })))
  }

  // Ensure correct order of buckets
  return result.sort((a, b) => a[dtKey] - b[dtKey])
}
