import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'floating-vue/dist/style.css'
import 'font-awesome/css/font-awesome.min.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import FloatingVue from 'floating-vue'
import VueAxios from 'vue-axios'

import App from './App.vue'
import router from './router'

// Set API URL as the base
axios.defaults.baseURL = import.meta.env.VITE_API_URL || ''

const app = createApp(App)

app.use(createPinia())
app.use(FloatingVue)
app.use(router)
app.use(VueAxios, axios)
app.provide('axios', app.config.globalProperties.axios)

app.mount('#app')
