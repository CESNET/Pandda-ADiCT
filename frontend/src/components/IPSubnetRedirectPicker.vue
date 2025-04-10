<!--
IP subnet picker with redirect

This component is used to pick an IP subnet and redirect to the appropriate route.
It uses the ipaddr.js library to validate the IP address and prefix length.
-->

<script setup>
import { computed, ref } from 'vue'
import ipaddr from 'ipaddr.js'

const props = defineProps({
  /**
   * Whether to use IPv4 or IPv6
   * @type {boolean}
   * @default true
   */
  isIPv4: {
    type: Boolean,
    default: true,
  },

  /**
   * The route name to use for the redirect
   * @type {string}
   */
  routeName: {
    type: String,
    required: true,
  },

  /**
   * The text to display on the button
   * @type {string}
   * @default 'View'
   */
  buttonText: {
    type: String,
    default: 'View',
  },

  /**
   * The icon to display on the button
   * @type {string}
   * @default 'fa fa-chevron-right'
   */
  buttonIcon: {
    type: String,
    default: 'fa fa-chevron-right',
  },

  /**
   * The minimum prefix length for the subnet
   * @type {number}
   * @default 16
   */
  minPrefix: {
    type: Number,
    default: 16,
  },

  /**
   * The maximum prefix length for the subnet
   * @type {number}
   * @default 32
   */
  maxPrefix: {
    type: Number,
    default: 32,
  },

  /**
   * The default prefix length for the subnet
   * @type {number}
   * @default 24
   */
  defaultPrefix: {
    type: Number,
    default: 24,
  },
})

const ip = ref(null)
const prefix = ref(props.defaultPrefix)

/**
 * IP address validator
 */
const ipValid = computed(() => {
  if (props.isIPv4) {
    // `ipaddr.IPv4.isValid()` allows even '1.2' as valid
    return ipaddr.IPv4.isValidFourPartDecimal(ip.value)
  } else {
    return ipaddr.IPv6.isValid(ip.value)
  }
})

/**
 * Possible prefixes
 */
const prefixes = computed(() => {
  return Array(props.maxPrefix - props.minPrefix + 1)
    .fill()
    .map((_, i) => props.minPrefix + i)
})
</script>

<template>
  <div class="row">
    <div class="col-md-8">
      <div class="input-group my-2">
        <div class="input-group-text">IP</div>
        <input
          v-model="ip"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': ip && !ipValid }"
          :placeholder="props.isIPv4 ? '1.2.3.4' : 'fe80::1'"
        />
        <div class="input-group-text">/</div>
        <select v-model="prefix" class="form-select">
          <option v-for="p in prefixes" v-bind:key="p">{{ p }}</option>
        </select>
      </div>
    </div>
    <div class="col-md-4">
      <component
        :is="!ip || !ipValid ? 'div' : 'router-link'"
        :to="{
          name: routeName,
          params: {
            ip: ip,
            prefix: prefix,
          },
        }"
        class="btn btn-primary my-2 w-100"
        :class="{ disabled: !ip || !ipValid }"
      >
        {{ buttonText }}
        <i :class="buttonIcon"></i>
      </component>
    </div>
  </div>
</template>
