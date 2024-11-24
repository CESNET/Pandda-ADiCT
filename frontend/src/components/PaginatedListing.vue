<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Paginate from 'vuejs-paginate-next'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import utc from 'dayjs/plugin/utc'
dayjs.extend(relativeTime)
dayjs.extend(utc)

const props = defineProps({
  url: {
    type: String,
    required: true,
  },
})

const getData = inject('getData')
const route = useRoute()
const router = useRouter()

// Query
const page = ref(parseInt(route.query.page) || 1)
const fulltextFilters = ref(JSON.parse(route.query.fulltext_filters || '{}'))
const genericFilter = ref(JSON.parse(route.query.generic_filter || '{}'))

const loaded = ref(false)
const items = ref([])
const timeCreated = ref(null)
const pageCount = ref(0)
const itemsPerPage = 20

/**
 * Replaces the route with current parameters
 */
function replaceRoute() {
  router.replace({
    query: {
      page: page.value,
      fulltext_filters: JSON.stringify(fulltextFilters.value),
      generic_filter: JSON.stringify(genericFilter.value),
    },
  })
}

/**
 * Changes page
 * @param {Number} newPage Index of new page
 */
async function changePage(newPage) {
  page.value = newPage
  replaceRoute()
  await load()
}

/**
 * Loads data
 */
async function load() {
  // Use only non-empty filters
  const validFulltextFilters = {}
  for (const f in fulltextFilters.value) {
    const val = fulltextFilters.value[f]
    if (val != '') {
      validFulltextFilters[f] = val
    }
  }

  const validGenericFilters = {}
  for (const f in genericFilter.value) {
    const val = genericFilter.value[f]
    if (val != '') {
      validGenericFilters[f] = val
    }
  }

  // Fetch items
  let data = await getData(props.url, {
    params: {
      skip: (page.value - 1) * itemsPerPage,
      limit: itemsPerPage,
      fulltext_filters: JSON.stringify(validFulltextFilters),
      generic_filter: JSON.stringify(validGenericFilters),
    },
  })

  if (data === undefined) {
    return
  }

  // Populate variables
  items.value = data.data
  pageCount.value = Math.ceil(data.total_count / itemsPerPage)
  timeCreated.value = data.time_created ? dayjs.utc(data.time_created).local() : null
}

onMounted(async () => {
  await load()
  loaded.value = true
})

// Adjust route query and reload data after filter change
watch(
  [() => fulltextFilters, () => genericFilter],
  async () => {
    page.value = 1
    replaceRoute()
    await load()
  },
  { deep: true },
)
</script>

<template>
  <div class="card my-4">
    <div class="card-body">
      <h5 class="card-title">Filters</h5>
      <slot name="filters" :fulltextFilters="fulltextFilters" :genericFilter="genericFilter"></slot>
    </div>
  </div>

  <div v-if="loaded && items.length == 0" class="alert alert-warning">No items</div>

  <div v-else-if="loaded && items.length > 0">
    <div v-if="timeCreated" class="mb-1">
      <span class="badge rounded-pill border text-secondary snapshot-timestamp-badge">
        <i class="fa fa-clock-o me-2"></i>Data timestamp: {{ timeCreated.format('HH:mm') }}
      </span>
    </div>

    <div class="table-responsive">
      <table class="table table-hover paginated-listing">
        <thead>
          <tr>
            <slot name="tableHeader"></slot>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, i) in items" :key="i">
            <slot name="tableRow" :row="item"></slot>
          </tr>
        </tbody>
      </table>
    </div>

    <Paginate
      :page-count="pageCount"
      :force-page="page"
      :click-handler="changePage"
      prev-text="Prev"
      next-text="Next"
      container-class="pagination justify-content-center"
    >
    </Paginate>
  </div>
</template>

<style lang="css">
.paginated-listing .invalid th,
.paginated-listing .invalid td {
  background: var(--bs-danger-bg-subtle);
}

.page-link {
  cursor: pointer;
}

.snapshot-timestamp-badge {
  font-size: 0.85em;
}
</style>
