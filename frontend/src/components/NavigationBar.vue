<script setup>
import { RouterLink, useRoute } from 'vue-router'

import { useThemeStore } from '@/stores/theme'
import ThemeToggle from '@/components/ThemeToggle.vue'

const route = useRoute()
const theme = useThemeStore()
</script>

<template>
  <nav class="navbar bg-body-tertiary navbar-expand-lg">
    <div class="container">
      <div class="navbar-brand">
        <RouterLink :to="{ name: 'home' }" class="navbar-brand">
          <img
            v-if="theme.theme === 'dark'"
            src="@/assets/logo-white.svg"
            alt="PANDDA"
            class="logo"
          />
          <img v-else src="@/assets/logo-black.svg" alt="PANDDA" class="logo" />
        </RouterLink>
      </div>
      <button
        class="navbar-toggler"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav px-2 me-auto">
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
        <div class="m-2">
          <ThemeToggle />
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.logo {
  height: 3.5rem;
}
</style>
