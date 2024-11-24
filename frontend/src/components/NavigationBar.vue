<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <nav class="navbar bg-body-tertiary">
    <div class="container">
      <RouterLink :to="{ name: 'home' }" class="navbar-brand">PANDDA</RouterLink>
    </div>
  </nav>
</template>

<style scoped lang="scss"></style>
