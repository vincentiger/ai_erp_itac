//C:\ai_erp\frontend\src\router\index.js
import { createRouter, createWebHashHistory } from 'vue-router'
const LoginView = () => import('@/views/loginView.vue')
const MainDashboard = () => import('@/views/MainDashboard.vue')
const CustomerCreate = () => import('@/views/CustomerCreate.vue')
const LabMech = () => import('@/views/labMech.vue')

const routes = [
  // ✅ 進站先導到 login
  { path: '/', redirect: '/login' },

  { path: '/login', component: LoginView, meta: { title: '登入' } },
  { path: '/dashboard', component: MainDashboard, meta: { title: '主控台' } },

  {
    path: '/customer_create',
    name: 'customer_create',
    component: CustomerCreate,
    meta: { title: '客戶新增 / 編輯' },
  },
  {
    path: '/customer_edit/:custno',
    redirect: (to) => ({
      name: 'customer_create',
      query: { refno: to.params.custno },
    }),
  },
  {
    path: '/customer_view',
    name: 'customer_view',
    component: () => import('@/views/customer_view.vue'),
    meta: { title: '客戶查詢' },
  },
  {
    path: '/customer_edit',
    name: 'customer_edit',
    component: () => import('@/views/customer_edit.vue'),
    meta: { title: '客戶修改' },
  },
  {
    path: '/customer_del',
    name: 'customer_del',
    component: () => import('@/views/customer_del.vue'),
    meta: { title: '客戶刪除' },
  },

  {
    path: '/order_view',
    name: 'order_view',
    component: () => import('@/views/order_view.vue'),
    meta: { title: '訂單查詢' },
  },

  {
    path: '/ai_alerts',
    name: 'ai_alerts',
    component: () => import('@/views/AiAlertsTable.vue'),
    meta: { title: '出貨明細' },
  },

  // ✅ 應收帳款套用（只留一個）
  {
    path: '/ar_apply',
    name: 'ar_apply',
    redirect: '/ar_manage',
  },

  {
    path: '/ar_manage',
    name: 'ar_manage',
    component: () => import('@/views/ar_manage.vue'),
    meta: { title: '應收帳款維護' },
  },

  {
    path: '/rpt_sales_perf',
    name: 'rpt_sales_perf',
    component: () => import('@/views/rpt_sales_perf.vue'),
    meta: { title: '業務績效儀表板' },
  },
  {
    path: '/rpt_fulfill',
    name: 'rpt_fulfill',
    component: () => import('@/views/rpt_fulfill.vue'),
    meta: { title: '出貨達成率' },
  },
  {
    path: '/ai_todo',
    name: 'ai_todo',
    component: () => import('@/views/ai_todo.vue'),
    meta: { title: 'AI 今日優先處理訂單' },
  },
  {
    path: '/inv_grn_view',
    name: 'inv_grn_view',
    component: () => import('@/views/InvGrnView.vue'),
  },
  {
    path: '/lab',
    name: 'lab',
    component: () => import('@/views/lab.vue'),
  },
  {
    path: '/lab/view',
    name: 'lab_view',
    component: () => import('@/views/lab_view.vue'),
    meta: { title: '委託測試單查詢' },
  },
  {
    path: '/lab/quote/manage',
    name: 'lab_quote_manage',
    component: () => import('@/views/lab_quote_manage.vue'),
    meta: { title: '委託單報價維護' },
  },
  {
    path: '/lab/qet',
    name: 'lab_qet',
    component: () => import('@/views/inspectValues.vue')
  },
  {
    path: '/lab/qet/standard',
    name: 'lab_qet_standard',
    component: () => import('@/views/inspectStandard.vue'),
    meta: { title: '設定尺寸原始紀錄表' },
  },
  {
    path: '/lab/qet/judge',
    name: 'lab_qet_judge',
    component: () => import('@/views/lab_qet_judge.vue'),
    meta: { title: '尺寸原始紀錄表判定' },
  },
  {
    path: '/lab/qet/manage',
    name: 'lab_qet_manage',
    component: () => import('@/views/lab_qet_manage.vue'),
    meta: { title: '原始尺寸紀錄表查修' },
  },
  {
    path: '/lab/qet/results',
    name: 'lab_qet_results',
    component: () => import('@/views/lab_qet_results.vue'),
    meta: { title: '尺寸原始紀錄表判定結果' },
  },
  {
    path: '/lab/mech',
    name: 'lab_mech',
    component: LabMech,
    meta: { title: '機械性質試驗紀錄表' },
  },
  {
    path: '/lab/mech/standard',
    name: 'lab_mech_standard',
    component: () => import('@/views/labMechStandard.vue'),
    meta: { title: '設定機械性質檢驗記錄表' },
  },
  {
    path: '/lab/mech/judge',
    name: 'lab_mech_judge',
    component: () => import('@/views/lab_mech_judge.vue'),
    meta: { title: '機械性質試驗紀錄表判定' },
  },
  {
    path: '/lab/mech/results',
    name: 'lab_mech_results',
    component: () => import('@/views/lab_mech_results.vue'),
    meta: { title: '機械性質試驗紀錄表判定結果' },
  },
  {
    path: '/lab/mech/manage',
    name: 'lab_mech_manage',
    component: () => import('@/views/lab_mech_manage.vue'),
    meta: { title: '機械性質試驗紀錄表查修' },
  },
  // ✅ 一定要最後：未知路由導回 /login（避免子路徑下白頁/錯頁）
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]


const BASE = import.meta.env.BASE_URL || '/'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL || '/ai/'), // 2. 套用 Hash
  routes,
})

router.afterEach((to) => {
  const base = 'Synaptic ERP'
  const t = to.meta?.title
  document.title = t ? `${t} - ${base}` : base
})

export default router
