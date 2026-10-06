import { Redirect, router } from 'expo-router'
import { useEffect, useState } from 'react'
import {
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import * as authApi from '@/api/auth'
import { Btn, DANGER, Input, useColors } from '@/components/ui'
import { ThemedText } from '@/components/themed-text'
import { ThemedView } from '@/components/themed-view'
import { Spacing } from '@/constants/theme'
import { DEFAULT_PROD_URL, DEFAULT_STAGING_URL, normalizeApiUrl } from '@/lib/config'
import { ApiError } from '@/lib/api-client'
import { setSession, useSession } from '@/lib/session'
import { clearSession, getServerUrl, setAdminId, setServerUrl, setToken } from '@/lib/storage'

export default function LoginScreen() {
  const theme = useColors()
  const session = useSession()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [countdown, setCountdown] = useState(0)

  // 服务器配置状态
  const [currentServer, setCurrentServer] = useState(DEFAULT_PROD_URL)
  const [showServerModal, setShowServerModal] = useState(false)
  const [customServerInput, setCustomServerInput] = useState('')

  useEffect(() => {
    getServerUrl().then((saved) => {
      if (saved) {
        setCurrentServer(saved)
        setCustomServerInput(saved)
      } else {
        setCustomServerInput(DEFAULT_PROD_URL)
      }
    })
  }, [])

  useEffect(() => {
    if (countdown <= 0) return
    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown])

  if (session === 'ok') {
    return <Redirect href="/" />
  }

  const handleSelectServer = async (url: string) => {
    const normalized = normalizeApiUrl(url)
    await setServerUrl(normalized)
    setCurrentServer(normalized)
    setCustomServerInput(normalized)
    setShowServerModal(false)
    Alert.alert('切换成功', `当前服务器已切换为：\n${normalized}`)
  }

  const onSendCode = async () => {
    if (!username.trim()) {
      Alert.alert('提示', '请先输入用户名')
      return
    }
    setSending(true)
    try {
      await authApi.sendCode(username.trim())
      Alert.alert('已发送', '验证码已发送至管理员邮箱（测试环境可直接使用 888888）')
      setCountdown(60)
    } catch (e) {
      Alert.alert(
        '发送失败',
        e instanceof ApiError ? e.message : '网络错误，请检查服务器连接',
      )
    } finally {
      setSending(false)
    }
  }

  const onLogin = async () => {
    if (!username.trim() || !password || !code.trim()) {
      Alert.alert('提示', '请填写用户名、密码和验证码')
      return
    }
    setLoading(true)
    try {
      const { id, token } = await authApi.login(
        username.trim(),
        password,
        code.trim(),
      )
      await setToken(token)
      const profile = await authApi.getProfile()
      if (profile.role === 0) {
        await clearSession()
        throw new ApiError('游客账号不可登录 App，请使用管理员账号')
      }
      await setAdminId(id)
      setSession('ok')
      router.replace('/')
    } catch (e) {
      Alert.alert(
        '登录失败',
        e instanceof ApiError ? e.message : '网络错误，请检查服务器地址与网络连接',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <ThemedView style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.safeArea}
        >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            {/* 品牌 Logo 与标题 */}
            <View style={styles.brandArea}>
              <ThemedText type="title" style={styles.brand}>
                Kang's Blog
              </ThemedText>
              <ThemedText type="smallBold" themeColor="textSecondary">
                个人博客移动管理后台
              </ThemedText>
              <ThemedText
                type="small"
                themeColor="textSecondary"
                style={styles.slogan}
              >
                内容审核 · 文章管理 · 城市足迹 · 数据看板
              </ThemedText>
            </View>

            <View style={styles.formArea}>
              {/* 当前连接的服务器指示条 */}
              <Pressable
                style={[
                  styles.serverBadge,
                  { backgroundColor: theme.backgroundElement },
                ]}
                onPress={() => setShowServerModal(true)}
              >
                <ThemedText type="small" themeColor="textSecondary" numberOfLines={1}>
                  🌐 当前服务器: {currentServer}
                </ThemedText>
                <ThemedText type="smallBold" style={{ color: theme.text }}>
                  [切换]
                </ThemedText>
              </Pressable>

              <ThemedView type="backgroundElement" style={styles.form}>
                <Input
                  label="用户名"
                  placeholder="管理员用户名"
                  autoCapitalize="none"
                  value={username}
                  onChangeText={setUsername}
                />
                <Input
                  label="密码"
                  placeholder="登录密码"
                  secureTextEntry
                  value={password}
                  onChangeText={setPassword}
                />
                <Input
                  label="验证码"
                  placeholder="邮箱验证码（测试可用 888888）"
                  keyboardType="number-pad"
                  value={code}
                  onChangeText={setCode}
                  style={{ paddingRight: 96 }}
                />
                <Pressable
                  onPress={onSendCode}
                  disabled={sending || countdown > 0}
                  style={[
                    styles.codeBtn,
                    { opacity: sending || countdown > 0 ? 0.5 : 1 },
                  ]}
                >
                  <Text style={[styles.codeBtnText, { color: theme.text }]}>
                    {countdown > 0 ? `${countdown}s 后重试` : '获取验证码'}
                  </Text>
                </Pressable>
                <Btn label="登录管理后台" onPress={onLogin} loading={loading} />
              </ThemedView>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>

        {/* 切换服务器模态弹窗 */}
        <Modal visible={showServerModal} transparent animationType="fade">
          <Pressable
            style={styles.modalMask}
            onPress={() => setShowServerModal(false)}
          >
            <Pressable
              style={[
                styles.modalCard,
                { backgroundColor: theme.background },
              ]}
              onPress={(e) => e.stopPropagation()}
            >
              <ThemedText type="subtitle" style={{ marginBottom: Spacing.two }}>
                选择连接服务器
              </ThemedText>
              
              <Btn
                label="🚀 阿里云正式生产 (admin.imcjk.top)"
                variant="ghost"
                onPress={() => handleSelectServer(DEFAULT_PROD_URL)}
                style={styles.modalBtn}
              />
              
              <Btn
                label="🧪 腾讯云测试环境 (:8081)"
                variant="ghost"
                onPress={() => handleSelectServer(DEFAULT_STAGING_URL)}
                style={styles.modalBtn}
              />

              <Input
                label="自定义服务器地址"
                placeholder="http://192.168.x.x:8081"
                value={customServerInput}
                onChangeText={setCustomServerInput}
                style={{ marginTop: Spacing.two }}
              />

              <View style={styles.modalRow}>
                <Btn
                  label="取消"
                  variant="ghost"
                  onPress={() => setShowServerModal(false)}
                  style={{ flex: 1 }}
                />
                <Btn
                  label="保存并连接"
                  onPress={() => handleSelectServer(customServerInput)}
                  style={{ flex: 1 }}
                />
              </View>
            </Pressable>
          </Pressable>
        </Modal>
      </SafeAreaView>
    </ThemedView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: Spacing.four,
  },
  brandArea: {
    flex: 1,
    maxHeight: '32%',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.two,
    paddingHorizontal: Spacing.four,
  },
  brand: {
    fontSize: 40,
    lineHeight: 48,
    fontWeight: '800',
  },
  slogan: {
    marginTop: Spacing.one,
  },
  formArea: {
    paddingHorizontal: Spacing.three,
  },
  serverBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: Spacing.two,
    paddingHorizontal: Spacing.three,
    borderRadius: Spacing.two,
    marginBottom: Spacing.two,
    gap: Spacing.two,
  },
  form: {
    borderRadius: Spacing.three,
    padding: Spacing.four,
    gap: Spacing.three,
  },
  codeBtn: {
    position: 'absolute',
    right: Spacing.four,
    top: 114,
  },
  codeBtnText: {
    fontSize: 14,
    fontWeight: '600',
  },
  modalMask: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.four,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    borderRadius: Spacing.three,
    padding: Spacing.four,
    gap: Spacing.two,
  },
  modalBtn: {
    marginVertical: 4,
  },
  modalRow: {
    flexDirection: 'row',
    gap: Spacing.two,
    marginTop: Spacing.three,
  },
})
