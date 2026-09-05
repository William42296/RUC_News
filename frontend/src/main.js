import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'

// Vant 4 函数式组件（showToast / showDialog 等）样式需手动引入
// 模板中的 <van-xxx> 组件样式由 unplugin-vue-components 按需自动注入
import 'vant/es/toast/style'
import 'vant/es/dialog/style'
import 'vant/es/notify/style'

// 全局样式 + 设计系统变量
import '@/styles/index.css'

const app = createApp(App)

app.use(pinia)
app.use(router)

app.mount('#app')
