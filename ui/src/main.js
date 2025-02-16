import { createApp } from 'vue'
import App from './App.vue' // Create App.vue (see next step)
import '../public/base.js' // If you have this file, move it to src/assets
import '../public/telemetry.js' // Move to src/assets
import lucide from 'lucide' // Import lucide if you are using it
const app = createApp(App)
app.mount('#vue-app') // Change #vue-app to #app

app.config.globalProperties.$lucide = lucide

//lucide.createIcons(); // Create icons