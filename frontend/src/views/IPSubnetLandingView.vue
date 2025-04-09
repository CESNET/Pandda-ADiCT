<!--
IP subnet landing page

This view serves as a landing page for IP subnets.
-->

<script setup>
import IPSubnetRedirectPicker from '@/components/IPSubnetRedirectPicker.vue'
</script>

<template>
  <main class="py-4">
    <div class="container">
      <h1 class="h2">IP subnets</h1>
      <div class="card my-4">
        <div class="card-body">
          <h5 class="card-title">IPv4</h5>
          <IPSubnetRedirectPicker
            :isIPv4="true"
            routeName="ip_subnet"
            :minPrefix="16"
            :maxPrefix="32"
            :defaultPrefix="24"
          />
        </div>
      </div>
    </div>
  </main>
</template>
