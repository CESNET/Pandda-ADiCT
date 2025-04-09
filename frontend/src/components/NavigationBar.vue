<script setup>
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <nav class="navbar bg-body-tertiary navbar-expand-lg">
    <div class="container">
      <div class="navbar-brand">
        <RouterLink :to="{ name: 'home' }" class="navbar-brand">
          <img src="@/assets/logo.svg" alt="PANDDA" class="logo" />
        </RouterLink>
      </div>
      <button
        class="navbar-toggler"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse row" id="navbarSupportedContent">
        <ul class="navbar-nav px-2">
          <li class="nav-item">
            <RouterLink
              :to="{ name: 'home' }"
              class="nav-link"
              :class="{ active: route.name === 'home' }"
            >
              <i class="fa fa-files-o me-1" aria-hidden="true"></i>
              IP addresses
            </RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink
              :to="{ name: 'ip_subnet_landing' }"
              class="nav-link"
              :class="{ active: route.name === 'ip_subnet_landing' }"
            >
              <i class="fa fa-bar-chart me-1" aria-hidden="true"></i>
              IP subnets
            </RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.logo {
  height: 3.5rem;
}
</style>
