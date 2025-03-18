// Date and time manipulation utilities

import dayjs from 'dayjs'

/**
 * Day.js macro to ceil a date to a specified unit
 *
 * @param {Date} date Date to ceil
 * @param {Number} unitCount Number of `unit` to ceil to
 * @param {String} unit Unit to ceil to (e.g. 'minute', 'hour')
 * @returns {Date} Ceiled date
 */
export function dateCeil(date, unitCount, unit) {
  const inst = dayjs(date)
  return inst
    .add(unitCount - (inst.get(unit) % unitCount), unit)
    .startOf(unit)
    .toDate()
}
