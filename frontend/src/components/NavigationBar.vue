<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <nav class="navbar bg-body-tertiary">
    <div class="container">
      <RouterLink :to="{ name: 'home' }" class="navbar-brand">
        <img src="@/assets/logo.svg" alt="PANDDA" class="logo" />
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.logo {
  height: 3.5rem;
}
</style>
