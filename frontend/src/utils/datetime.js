// Date and time manipulation utilities

import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'

dayjs.extend(duration)

/**
 * Day.js macro to floor a date to a specified unit
 *
 * @param {Date} date Date to floor
 * @param {Number} unitCount Number of `unit` to floor to
 * @param {String} unit Unit to floor to (e.g. 'minute', 'hour')
 * @returns {Date} Floored date
 */
export function dateFloor(date, unitCount, unit) {
  const inst = dayjs(date)
  return inst
    .subtract(inst.get(unit) % unitCount, unit)
    .startOf(unit)
    .toDate()
}

/**
 * Macro to get the duration in milliseconds of a specified unit
 *
 * @param {Number} unitCount Number of `unit` to floor to
 * @param {String} unit Unit to floor to (e.g. 'minute', 'hour')
 * @returns {Number} Duration in milliseconds
 */
export function durationMs(unitCount, unit) {
  return dayjs.duration(unitCount, unit).asMilliseconds()
}
