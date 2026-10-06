import { defineStore } from 'pinia'
import { ref } from 'vue'
import { recordVisitor } from '@/api/visitor'
import { collectFingerprint } from '@/utils/fingerprint'

/**
 * 访客状态
 *
 * 访客身份由服务端下发 HttpOnly Cookie 承载，前端不再保存任何身份令牌：
 * JS 能读到的令牌在 XSS 场景下等同于公开，因此只保留用于展示与归属判断的 visitorId。
 */
export const useVisitorStore = defineStore(
  'visitor',
  () => {
    const visitorId = ref(null)
    const sessionId = ref('')
    const fingerprint = ref('')
    const nickname = ref('')
    const email = ref('')

    const record = async () => {
      try {
        const fp = collectFingerprint()
        const res = await recordVisitor(fp)
        const d = res.data.data
        visitorId.value = d.visitorId
        sessionId.value = d.sessionId
        fingerprint.value = d.visitorFingerprint
      } catch (e) {
        console.error('访客记录失败', e)
      }
    }

    return {
      visitorId,
      sessionId,
      fingerprint,
      nickname,
      email,
      record
    }
  },
  {
    persist: {
      pick: ['visitorId', 'fingerprint', 'nickname', 'email']
    }
  }
)
