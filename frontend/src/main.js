import './style.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { installGlobalErrorReporter } from './utils/errorReporter'

// ✅ Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// ✅ Element Plus Icons
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

app.use(router)
app.use(ElementPlus)

// 🔑 全域註冊所有 Icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

installGlobalErrorReporter()

app.mount('#app')





