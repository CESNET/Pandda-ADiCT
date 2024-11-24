<script setup>
import PaginatedListing from '@/components/PaginatedListing.vue'

function parseBoolFilter(str) {
  if (str == 'true') {
    return { $eq: true }
  } else if (str == 'false') {
    return { $eq: false }
  } else {
    return undefined
  }
}
</script>

<template>
  <main class="py-4">
    <div class="container">
      <h1 class="h2">IP addresses</h1>
      <PaginatedListing url="/entity/ip">
        <template #filters="{ fulltextFilters, genericFilter }">
          <div class="row">
            <div class="col-md-6">
              <div class="input-group my-2">
                <VTooltip class="input-group-text">
                  <div>IP&nbsp;<span class="fa fa-info text-secondary ms-1"></span></div>
                  <template #popper>
                    Substring search. Regular expressions are supported.
                  </template>
                </VTooltip>
                <input
                  :value="fulltextFilters.eid?.replaceAll('\\.', '.')"
                  @input="fulltextFilters.eid = $event.target.value.replaceAll('.', '\\.')"
                  type="text"
                  class="form-control"
                />
              </div>
            </div>
            <div class="col-md-6">
              <div class="input-group my-2">
                <VTooltip class="input-group-text">
                  <div>Hostname&nbsp;<span class="fa fa-info text-secondary ms-1"></span></div>
                  <template #popper>
                    Substring search. Regular expressions are supported.
                  </template>
                </VTooltip>
                <input v-model="fulltextFilters.hostname" type="text" class="form-control" />
              </div>
            </div>
            <div class="col-md-4">
              <div class="input-group my-2">
                <div class="input-group-text">Open port</div>
                <input
                  :value="genericFilter['last.open_ports']"
                  @input="
                    genericFilter['last.open_ports'] = parseInt($event.target.value) || undefined
                  "
                  type="text"
                  class="form-control"
                />
              </div>
            </div>
            <div class="col-md-4">
              <div class="input-group my-2">
                <div class="input-group-text">Activity class</div>
                <select class="form-select" v-model="fulltextFilters.activity_class">
                  <option selected></option>
                  <option value="off">Off</option>
                  <option value="idle">Idle</option>
                  <option value="light">Light</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="input-group my-2">
                <div class="input-group-text">Open resolver</div>
                <select
                  class="form-select"
                  :value="genericFilter['last.open_resolver']?.['$eq']"
                  @change="
                    genericFilter['last.open_resolver'] = parseBoolFilter($event.target.value)
                  "
                >
                  <option selected></option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
            </div>
          </div>
        </template>

        <template #tableHeader>
          <th scope="col">IP address</th>
          <th scope="col" class="text-end">Hostname</th>
          <th scope="col">Open ports</th>
          <th scope="col">Activity class</th>
          <th scope="col">Resolver</th>
        </template>

        <template #tableRow="{ row }">
          <th scope="row">
            <RouterLink :to="{ name: 'ip', params: { eid: row.eid } }" class="text-decoration-none">
              {{ row.eid }}
            </RouterLink>
          </th>
          <td class="text-end">
            <code>{{ row.hostname }}</code>
          </td>
          <td>
            <VTooltip
              v-for="(port, i) in (row.open_ports || []).sort((a, b) => a - b)"
              :key="i"
              class="badge bg-secondary me-1"
              :class="{
                'opacity-50': row['open_ports#c'][i] < 0.5 && row['open_ports#c'][i] >= 0.25,
                'opacity-25': row['open_ports#c'][i] < 0.25,
              }"
            >
              <span>{{ port }}</span>
              <template #popper>
                <strong>{{ Math.round(row['open_ports#c'][i] * 100) }} %</strong> confidence
              </template>
            </VTooltip>
          </td>
          <td>
            <span v-if="row.activity_class == 'off'" class="badge bg-dark-subtle">
              <i class="fa fa-power-off me-2" aria-hidden="true"></i>Off
            </span>
            <span v-else-if="row.activity_class == 'idle'" class="badge bg-dark-subtle">Idle</span>
            <span v-else-if="row.activity_class == 'light'" class="badge bg-info text-dark"
              >Light</span
            >
            <span v-else-if="row.activity_class == 'medium'" class="badge bg-warning text-dark"
              >Medium</span
            >
            <span v-else-if="row.activity_class == 'high'" class="badge bg-danger">High</span>
          </td>
          <td>
            <span v-if="row.open_resolver === true" class="badge bg-danger">
              <i class="fa fa-exclamation-triangle me-2" aria-hidden="true"></i>Open
            </span>
            <span v-else-if="row.open_resolver === false" class="badge bg-secondary">
              <i class="fa fa-check me-2" aria-hidden="true"></i>Closed
            </span>
          </td>
        </template>
      </PaginatedListing>
    </div>
  </main>
</template>
