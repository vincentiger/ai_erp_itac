// src/utils/speech/index.js
import { createSpeechRouter } from './router'
import handlers from './handlers'

export function createDefaultSpeechRouter() {
  return createSpeechRouter(handlers)
}
