// src/utils/speech/handlers/index.js
import customerSearch from './customerSearch'
import customerCreatePrefill from './customerCreatePrefill'
import navigationFallback from './navigationFallback'
export default [
  customerSearch,
  customerCreatePrefill,
  navigationFallback, // 永遠放最後
]
