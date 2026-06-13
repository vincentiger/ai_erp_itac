<template>
  <div class="login-page min-h-screen flex items-center justify-center font-sans px-4">
    
    <div class="login-card bg-white px-6 sm:px-8 py-10 w-full max-w-md text-center shadow-sm border border-slate-100">
      
      <div class="flex flex-col items-center justify-center mb-10">
        <img
          src="@/assets/img/logo.png"
          alt="logo"
          class="login-logo"
          draggable="false"
        />
        <div class="login-subtitle">( 實驗室篇 )</div>
      </div>

      <form @submit.prevent="handleLogin" class="text-left space-y-6">
        <div>
          <label class="block text-sm font-bold text-slate-700 mb-2">
            帳號<span class="text-red-500 ml-1">*</span>
          </label>
          <input
            ref="accountInput"
            v-model="account"
            type="text"
            placeholder="請輸入帳號"
            :class="[
              'w-full input-neon transition-all',
              errorField === 'account' ? 'border-red-400 animate-shake' : ''
            ]"
          >
        </div>

        <div>
          <el-alert
            v-if="loginErrorMsg"
            :title="loginErrorMsg"
            type="error"
            show-icon
            closable
            @close="loginErrorMsg = ''"
            class="mb-4"
          />
          <label class="block text-sm font-bold text-slate-700 mb-2">
            密碼<span class="text-red-500 ml-1">*</span>
          </label>
          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            placeholder="請輸入密碼"
            :class="[
              'w-full input-neon transition-all',
              errorField === 'password' ? 'border-red-400 animate-shake' : ''
            ]"
          >
        </div>

        <label class="flex items-center gap-2 text-sm text-slate-600 select-none">
          <input
            v-model="rememberMe"
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300 text-lime-600 focus:ring-lime-500"
          >
          <span>記住帳密</span>
        </label>

        <button
          type="submit"
          class="w-full btn-login mt-6"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? '登入中...' : '登入系統' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
//frontend/src/views/loginView.vue
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { rtLogin, startUserListWatch } from '@/utils/rt'
const loginErrorMsg = ref('')
const account = ref('')
const password = ref('')
const rememberMe = ref(false)
const errorField = ref('')
const isSubmitting = ref(false)

const accountInput = ref(null)
const passwordInput = ref(null)
const router = useRouter()
const route = useRoute()

const LOGIN_COOKIE_ACCOUNT = 'ai_erp_login_account'
const LOGIN_COOKIE_PASSWORD = 'ai_erp_login_password'
const LOGIN_COOKIE_REMEMBER = 'ai_erp_login_remember'

function setCookie(name, value, days = 30) {
  const expires = new Date(Date.now() + days * 86400000).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
}

function getCookie(name) {
  const prefix = `${name}=`
  const parts = document.cookie.split(';').map(v => v.trim())
  const found = parts.find(v => v.startsWith(prefix))
  return found ? decodeURIComponent(found.slice(prefix.length)) : ''
}

function deleteCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`
}

function getStartupLoginParams() {
  const routeQuery = route.query || {}
  const href = String(window.location.href || '')
  const queryText = String(window.location.search || '').replace(/^\?/, '')
  const hashQueryText = href.includes('?') ? href.slice(href.indexOf('?') + 1) : ''
  const merged = new URLSearchParams(queryText)
  const hashParams = new URLSearchParams(hashQueryText)

  for (const [key, value] of hashParams.entries()) {
    if (!merged.has(key)) merged.set(key, value)
  }

  const clean = value => String(value || '').trim().replace(/\^+$/g, '')
  const startup = String(routeQuery.startup || merged.get('startup') || '') === '1'

  return {
    account: startup ? 'winnie' : clean(routeQuery.account || merged.get('account')),
    password: startup ? 'w19800828' : clean(routeQuery.password || merged.get('password')),
    autologin: startup || String(routeQuery.autologin || merged.get('autologin') || '') === '1',
  }
}

async function handleLogin() {
  loginErrorMsg.value = ''
  errorField.value = ''

  const acc = account.value.trim()
  const pwd = password.value.trim()

  if (!acc) {
    errorField.value = 'account'
    accountInput.value?.focus()
    return
  }
  if (!pwd) {
    errorField.value = 'password'
    passwordInput.value?.focus()
    return
  }
  if (isSubmitting.value) return
  isSubmitting.value = true

  try {
    // ✅ 正確：傳兩個參數
    const res = await rtLogin(acc, pwd) // res = {ok,sid,user,users,online_count}

    if (rememberMe.value) {
      setCookie(LOGIN_COOKIE_ACCOUNT, acc)
      setCookie(LOGIN_COOKIE_PASSWORD, pwd)
      setCookie(LOGIN_COOKIE_REMEMBER, '1')
    } else {
      deleteCookie(LOGIN_COOKIE_ACCOUNT)
      deleteCookie(LOGIN_COOKIE_PASSWORD)
      deleteCookie(LOGIN_COOKIE_REMEMBER)
    }

    const rawUser = res.user || {}
    const loginUser = {
      ...rawUser,
      id: rawUser.id ?? rawUser.user_id ?? rawUser.eid ?? rawUser.staff_id ?? '',
      account: rawUser.account || acc,
      name: rawUser.name || rawUser.display_name || rawUser.account || acc,
      _loginAt: Date.now(),
    }

    // 後續表單會取登入者 id/name，localStorage 與 sessionStorage 都保留一份。
    localStorage.setItem('user', JSON.stringify(loginUser))
    sessionStorage.setItem('user', JSON.stringify(loginUser))

    // ✅ 正確：傳入 getUserFn，讓 heartbeat 能拿到 user.account
    startUserListWatch(() => JSON.parse(localStorage.getItem('user') || '{}'))

    ElMessage.success(`歡迎回來，${loginUser.name || ''}`)
    router.push('/dashboard')
  } catch (e) {
    const msg = e?.message || '登入失敗'
    loginErrorMsg.value = msg
    ElMessage.error(msg)
  } finally {
    isSubmitting.value = false
  }
}
onMounted(async () => {
  const startupParams = getStartupLoginParams()
  const startupAccount = startupParams.account
  const startupPassword = startupParams.password
  const startupAutologin = startupParams.autologin

  if (startupAccount || startupPassword) {
    account.value = startupAccount
    password.value = startupPassword
    rememberMe.value = false
    await nextTick()
    if (startupAutologin && startupAccount && startupPassword) {
      await handleLogin()
      return
    }
    if (startupAccount) passwordInput.value?.focus()
    else accountInput.value?.focus()
    return
  }

  rememberMe.value = getCookie(LOGIN_COOKIE_REMEMBER) === '1'
  if (rememberMe.value) {
    account.value = getCookie(LOGIN_COOKIE_ACCOUNT)
    password.value = getCookie(LOGIN_COOKIE_PASSWORD)
  }
  if (account.value) passwordInput.value?.focus()
  else accountInput.value?.focus()
})
</script>
<style>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(5px); }
  75% { transform: translateX(-5px); }
}
.animate-shake { animation: shake 0.2s ease-in-out; }

/* ✅ 整頁白底鎖住 */
html, body, #app {
  background: #fff !important;
}

.login-page {
  background: #fff !important;
  /* 確保滿版 */
  width: 100%;
}

.login-card {
  /* 移除硬塞的高度，改用內距 py-10 撐開 */
  border-radius: 4px;
}

.login-logo {
  /* ✅ 修正寬度設定，確保不會因為寬度過大推擠 */
  width: 78%;
  max-width: 270px;
  height: auto;
  display: block;
}

.login-subtitle {
  width: 100%;
  margin-top: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #334155;
  letter-spacing: 0;
  text-align: center;
}

/* ===============================
   Input（無圓角 + 霓虹 hover/focus）
   =============================== */
.input-neon {
  font-size: 12pt;
  padding: 12px 14px;
  border-radius: 0;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.input-neon:hover,
.input-neon:focus {
  border-color: #91C51B;
  box-shadow:
    inset 0 0 0 1px #91C51B,
    0 0 6px rgba(145, 197, 27, 0.6);
  outline: none;
}

/* ===============================
   Button（黑底 + 霓虹 hover，效果不外溢）
   =============================== */
.btn-login {
  font-size: 12pt;
  padding: 12px;
  border-radius: 0;
  background-color: #020617;
  color: #ffffff;
  font-weight: 600;
  border: 1.5px solid #020617;
  cursor: pointer;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}

.btn-login:hover {
  border-color: #91C51B;
  box-shadow:
    inset 0 0 0 1px #91C51B,
    0 0 10px rgba(145, 197, 27, 0.65);
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
