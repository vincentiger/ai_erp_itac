<template>
  <nav class="space-y-2" aria-label="主選單">
    <section v-for="group in filteredGroups" :key="group.key">
      <button
        type="button"
        class="group-toggle"
        :aria-expanded="!collapsed[group.key]"
        @click="toggleGroup(group.key)"
      >
        <span class="min-w-0 truncate">{{ group.title }}</span>
        <el-icon
          class="shrink-0 transition-transform duration-150"
          :class="{ 'rotate-90': !collapsed[group.key] }"
        >
          <ArrowRight />
        </el-icon>
      </button>

      <div v-show="!collapsed[group.key] || search" class="mt-1 space-y-1">
        <button
          v-for="item in group.items"
          :key="item.key"
          type="button"
          class="menu-item"
          :class="{ 'is-active': isActive(item) }"
          @click="onItemClick(item)"
        >
          <span class="min-w-0 flex-1 text-left">
            <span class="block truncate">{{ item.label }}</span>
            <span v-if="item.desc" class="mt-0.5 block truncate text-xs text-slate-400">
              {{ item.desc }}
            </span>
          </span>
          <span v-if="item.badge" class="menu-badge">{{ item.badge }}</span>
        </button>

        <div v-if="group.items.length === 0" class="px-3 py-2 text-xs text-slate-500">
          無可用功能
        </div>
      </div>
    </section>

    <div v-if="filteredGroups.length === 0" class="px-3 py-6 text-center text-sm text-slate-400">
      找不到符合的功能
    </div>
  </nav>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  search: { type: String, default: '' },
  items: { type: Array, default: () => [] } // tree: [{title, refno, children:[{title,url}]}]
})

const router = useRouter()
const route = useRoute()

function resolveRoute(node) {
  // ✅ 你的 children.url = route name
  const routeName = node?.url ? String(node.url).trim() : null
  const path = node?.path ? String(node.path).trim() : null
  return { routeName, path }
}

const groups = computed(() => {
  const rawGroups = Array.isArray(props.items) ? props.items : []

  return rawGroups.map((g, gi) => {
    const title = String(g.title || `Group ${gi + 1}`)
    const key = String(g.refno || g.code || g.id || title)

    const children = Array.isArray(g.children) ? g.children : []
    const items = children.map((c, ci) => {
      const r = resolveRoute(c)
      return {
        key: String(c.refno || c.code || c.id || c.title || `${key}-${ci}`),
        label: String(c.title || '未命名'),
        desc: String(c.desc || c.description || ''),
        icon: c.icon || null,
        badge: c.badge || '',
        routeName: r.routeName, // ✅ 用 url 當 route name
        path: r.path,
        _raw: c
      }
    })

    return { key, title, items }
  })
})

const filteredGroups = computed(() => {
  const q = String(props.search || '').trim().toLowerCase()
  if (!q) return groups.value

  const keepItem = (it) => {
    const hay = [it.label, it.desc, it.routeName, it.path].filter(Boolean).join(' ').toLowerCase()
    return hay.includes(q)
  }

  return groups.value
    .map(g => ({ ...g, items: g.items.filter(keepItem) }))
    .filter(g => g.items.length > 0 || g.title.toLowerCase().includes(q))
})

const collapsed = reactive({})
function toggleGroup(key) {
  collapsed[key] = !collapsed[key]
}

function isActive(item) {
  if (item.routeName && route.name) return String(route.name) === String(item.routeName)
  if (item.path && route.path) return String(route.path) === String(item.path)
  return false
}

function onItemClick(item) {
  if (item.routeName) {
    router.push({ name: item.routeName })
    return
  }
  if (item.path) {
    router.push(item.path)
    return
  }
  console.warn('[Sidebar] menu item has no route:', item._raw)
}
</script>

<style scoped>
.group-toggle {
  display: flex;
  width: 100%;
  min-height: 40px;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  color: rgb(226 232 240);
  font-size: 14px;
  font-weight: 700;
  text-align: left;
}

.group-toggle:hover {
  background: rgb(30 41 59);
}

.menu-item {
  display: flex;
  width: 100%;
  min-height: 40px;
  align-items: center;
  gap: 8px;
  padding: 8px 10px 8px 22px;
  color: rgb(203 213 225);
  font-size: 14px;
}

.menu-item:hover {
  background: rgb(30 41 59);
  color: white;
}

.menu-item.is-active {
  background: rgb(51 65 85);
  color: white;
  font-weight: 700;
}

.menu-badge {
  flex: none;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgb(71 85 105);
  color: rgb(241 245 249);
  font-size: 11px;
}
</style>
