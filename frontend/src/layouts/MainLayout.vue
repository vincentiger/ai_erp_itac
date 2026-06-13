<template>
  <el-container class="h-screen bg-slate-50">
    <!-- Sidebar (ChatGPT style) -->
    <el-aside
      width="280px"
      class="bg-slate-900 text-slate-100 border-r border-slate-800 flex flex-col"
    >
      <!-- Brand / New chat -->
      <div class="p-4 border-b border-slate-800">
        <div class="flex items-center justify-between gap-3">
          <div class="font-black tracking-tight text-lg select-none">
            AI ERP
          </div>

          <button
            class="h-9 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 active:scale-[0.99] transition text-sm font-semibold"
            @click="$router.push({ name: 'dashboard' })"
            title="回到首頁"
          >
            ＋ 新指令
          </button>
        </div>

        <!-- Quick search (optional) -->
        <div class="mt-3">
          <input
            v-model="sidebarSearch"
            type="text"
            placeholder="搜尋功能…"
            class="w-full h-10 rounded-lg bg-slate-800/60 border border-slate-700 px-3 text-sm
                   placeholder:text-slate-400 outline-none focus:border-slate-500"
          />
        </div>
      </div>

      <!-- Menu list -->
      <div class="flex-1 overflow-auto p-2">
        <!-- 你可以先用 Sidebar 元件，或改成內嵌菜單 -->
        <Sidebar :search="sidebarSearch" :items="menus" />
      </div>

      <!-- User footer -->
      <div class="p-3 border-t border-slate-800">
        <div class="flex items-center justify-between gap-3">
          <div class="min-w-0">
            <div class="text-sm font-semibold truncate">
              {{ currentUser?.name || '未登入' }}
            </div>
            <div class="text-xs text-slate-400 truncate">
              {{ currentContext }}
            </div>
          </div>

          <button
            class="h-9 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 active:scale-[0.99] transition text-sm"
            @click="handleLogout"
          >
            登出
          </button>
        </div>
      </div>
    </el-aside>

    <!-- Main -->
    <el-container class="min-w-0">
      <!-- Topbar -->
      <el-header class="h-14 !p-0 bg-white border-b border-slate-200 flex items-center">
        <div class="w-full px-4 flex items-center justify-between gap-3">
          <Topbar />
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="!p-0 min-w-0">
        <!-- subtle background like ChatGPT -->
        <div class="h-full min-h-0 bg-slate-50">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import Topbar from '@/components/Topbar.vue'
import { disconnectSocket } from '@/utils/socket.js'

const router = useRouter()

// ✅ 預設要有 menus，避免 Sidebar 沒資料
const currentUser = ref(JSON.parse(localStorage.getItem('user')) || { name: '未登入', menus: [] })
const currentContext = ref(localStorage.getItem('currentContext') || '通用模式')

// ✅ Sidebar 搜尋（可選）
const sidebarSearch = ref('')

// ✅ 把 menus 統一從 currentUser 取（讓 Sidebar 純展示）
const menus = computed(() => Array.isArray(currentUser.value?.menus) ? currentUser.value.menus : [])
// ✅ 可選保險：因為 login 後會 router.push 到 /dashboard，Layout 會重新 mount
// 但如果你有「同頁切換」情況，這段可確保會同步 localStorage
onMounted(() => {
  const u = JSON.parse(localStorage.getItem('user') || 'null')
  if (u) currentUser.value = u
})

const handleLogout = () => {
  localStorage.clear()
  disconnectSocket()
  router.push('/login')
}
</script>
