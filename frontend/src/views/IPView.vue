<script setup>
import ActivityClassBadge from '@/components/ActivityClassBadge.vue'
import ActivityTimeline from '@/components/ActivityTimeline.vue'
import EntityDetailTemplate from '@/templates/EntityDetailTemplate.vue'
import ObservationsTimeline from '@/components/ObservationsTimeline.vue'
import OpenResolverBadge from '@/components/OpenResolverBadge.vue'
import SnapshotsTimePickerHistoryPermalinkButton from '@/components/SnapshotsTimePickerHistoryPermalinkButton.vue'
import SnapshotsTimePickerLatestDataPermalinkButton from '@/components/SnapshotsTimePickerLatestDataPermalinkButton.vue'

/**
 * Stringifies recog-attribute value
 *
 * Returns human-readable value for recog attribute value.
 */
function stringifyRecogValue(v) {
  let service = 'unknown'
  let os = 'unknown'

  if (v.service) {
    if (v.service.product && v.service.version) {
      service = `${v.service.product} ${v.service.version}`
    } else if (v.service.product) {
      service = v.service.product
    } else if (v.service.family) {
      service = v.service.family
    } else if (v.service.cpe23) {
      service = v.service.cpe23
    }
  }

  if (v.os) {
    if (v.os.vendor) {
      os = v.os.vendor
    } else if (v.os.product) {
      os = v.os.product
    } else if (v.os.family) {
      os = v.os.family
    } else if (v.os.cpe23) {
      os = v.os.cpe23
    }
  }

  return `${service} @ ${os}`
}
</script>

<template>
  <EntityDetailTemplate etype="ip" :eid="$route.params.eid">
    <template #header="{ pickedSnapshot }">
      <h4>IP detail</h4>
      <h1 class="h2 fw-bold">{{ $route.params.eid }}</h1>
      <div class="h3 row g-2">
        <div class="col col-auto" v-if="pickedSnapshot?.hostname">
          <span class="badge text-bg-secondary me-2 mb-1">
            {{ pickedSnapshot?.hostname }}
          </span>
          <ActivityClassBadge :value="pickedSnapshot?.activity_class" class="me-2 mb-1" />
          <OpenResolverBadge :value="pickedSnapshot?.open_resolver" class="me-2 mb-1" />
        </div>
      </div>
    </template>

    <template
      #default="{ masterRecord, snapshots, pickedSnapshot, pickedSnapshotTs, timePickerState }"
    >
      <div>
        <h4 class="my-3">
          <span>Activity</span>
          <VTooltip class="d-inline-block ms-2 fs-5">
            <i class="fa fa-info text-secondary"></i>
            <template #popper>
              Permalink to this section is identical to the history permalink (below).
            </template>
          </VTooltip>
        </h4>
        <ActivityTimeline
          v-if="masterRecord.activity && masterRecord.activity.length > 0"
          :activity="masterRecord.activity"
          :time-picker-state="timePickerState"
          :picked-snapshot-ts="pickedSnapshotTs.toDate()"
          :resample-unit-count="timePickerState.resampleUnitCount"
          :resample-unit="timePickerState.resampleUnit"
        />
        <div v-else class="alert alert-info">No data</div>
      </div>

      <div>
        <h4 class="mt-4 mb-3 d-flex align-items-center flex-wrap">
          <span v-if="timePickerState.latest">Latest data</span>
          <span v-else>Snapshot</span>
          <div class="d-inline-block ms-2 fs-5">
            <span class="badge rounded-pill border snapshot-date-badge">
              <i class="fa fa-clock-o me-2"></i>{{ pickedSnapshotTs.format('DD.MM. HH:mm') }}
            </span>
          </div>
          <VTooltip>
            <SnapshotsTimePickerLatestDataPermalinkButton
              v-if="timePickerState.latest"
              class="btn-sm ms-2"
              :time-picker-state="timePickerState"
            />
            <template #popper>Permalink to displayed latest data</template>
          </VTooltip>
        </h4>
        <div v-if="pickedSnapshot" class="row">
          <div class="col col-md-4">
            <h6>
              Open ports
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Open TCP ports, based on observation of sucessfully established connections.
                  <br />
                  Note that ports which no one connected to (or scanned) recently are not visible
                  this way.
                </template>
              </VTooltip>
            </h6>
            <div v-if="(pickedSnapshot?.open_ports || []).length > 0">
              <div
                v-for="(port, i) in pickedSnapshot?.open_ports.sort((a, b) => a - b)"
                v-bind:key="i"
                class="mb-2"
              >
                <span class="badge bg-light text-dark fs-6">{{ port }}</span>
                <span class="opacity-50 ms-1">
                  ({{ Math.round(100 * pickedSnapshot['open_ports#c'][i]) }} % confidence)
                </span>
              </div>
            </div>
            <div v-else class="alert alert-info">No data</div>
          </div>
          <div class="col col-md-4">
            <h6>
              SSH details
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Information extracted from SSH banners sent by this IP (using Recog pattern
                  database).
                </template>
              </VTooltip>
            </h6>
            <pre v-if="pickedSnapshot?.recog_ssh">{{
              JSON.stringify(pickedSnapshot?.recog_ssh, null, 2)
            }}</pre>
            <div v-else class="alert alert-info">No data</div>
          </div>
          <div class="col col-md-4">
            <h6>
              SMTP details
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Information extracted from SMTP banners sent by this IP (using Recog pattern
                  database)
                </template>
              </VTooltip>
            </h6>
            <pre v-if="pickedSnapshot?.recog_smtp">{{
              JSON.stringify(pickedSnapshot?.recog_smtp, null, 2)
            }}</pre>
            <div v-else class="alert alert-info">No data</div>
          </div>
        </div>
        <div v-else class="alert alert-info">No data in picked snapshot</div>
      </div>

      <div>
        <h4 class="mt-4 mb-3">
          <span>History</span>
          <VTooltip class="d-inline-block">
            <SnapshotsTimePickerHistoryPermalinkButton
              v-if="timePickerState.latest"
              class="btn-sm ms-2"
              :time-picker-state="timePickerState"
            />
            <template #popper>Permalink to displayed history and activity charts</template>
          </VTooltip>
        </h4>
        <div v-if="snapshots.length > 0">
          <div class="mb-3">
            <h6>Open ports</h6>
            <ObservationsTimeline
              id="open_ports"
              :snapshots="snapshots"
              :time-picker-state="timePickerState"
              :picked-snapshot-ts="pickedSnapshotTs.toDate()"
              :resample-unit-count="timePickerState.resampleUnitCount"
              :resample-unit="timePickerState.resampleUnit"
              :isArrayType="true"
            />
          </div>
          <div class="mb-3">
            <h6>
              SSH details
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Service and operating system identifiers parsed from recog SSH attribute values.
                </template>
              </VTooltip>
            </h6>
            <ObservationsTimeline
              id="recog_ssh"
              :snapshots="snapshots"
              :time-picker-state="timePickerState"
              :picked-snapshot-ts="pickedSnapshotTs.toDate()"
              :resample-unit-count="timePickerState.resampleUnitCount"
              :resample-unit="timePickerState.resampleUnit"
              :isArrayType="true"
              :valueMapper="stringifyRecogValue"
            />
          </div>
          <div class="mb-3">
            <h6>
              SMTP details
              <VTooltip class="d-inline-block ms-2">
                <i class="fa fa-info text-secondary"></i>
                <template #popper>
                  Service and operating system identifiers parsed from recog SMTP attribute values.
                </template>
              </VTooltip>
            </h6>
            <ObservationsTimeline
              id="recog_smtp"
              :snapshots="snapshots"
              :time-picker-state="timePickerState"
              :picked-snapshot-ts="pickedSnapshotTs.toDate()"
              :resample-unit-count="timePickerState.resampleUnitCount"
              :resample-unit="timePickerState.resampleUnit"
              :isArrayType="true"
              :valueMapper="stringifyRecogValue"
            />
          </div>
        </div>
        <div v-else class="alert alert-info">No snapshots</div>
      </div>
    </template>
  </EntityDetailTemplate>
</template>

<style lang="css" scoped>
pre {
  color: var(--bs-code-color);
}

.snapshot-date-badge {
  color: #d980fa;
  border-color: #d980fa !important;
}
</style>
