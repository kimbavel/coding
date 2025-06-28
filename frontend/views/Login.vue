<template>
  <div class="login-container">
    <div class="login-desc">
      <p>멘토-멘티 서비스에 로그인하여 다양한 멘토와 멘티를 만나보세요.<br />
      이메일과 비밀번호로 로그인할 수 있습니다.</p>
    </div>
    <h2>로그인</h2>
    <form @submit.prevent="onLogin">
      <input id="email" v-model="email" type="email" placeholder="이메일" required />
      <input id="password" v-model="password" type="password" placeholder="비밀번호" required />
      <button id="login" type="submit">로그인</button>
    </form>
    <p>
      계정이 없으신가요?
      <router-link to="/signup">회원가입</router-link>
    </p>
    <div v-if="error" style="color:red">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';

const email = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

const onLogin = async () => {
  error.value = '';
  try {
    const res = await api.post('/login', { email: email.value, password: password.value });
    localStorage.setItem('token', res.data.token);
    // 토큰에서 role 추출
    const payload = JSON.parse(atob(res.data.token.split('.')[1]));
    localStorage.setItem('role', payload.role);
    router.push('/profile');
  } catch (e) {
    error.value = e.response?.data?.detail || '로그인 실패';
  }
};
</script>

<style scoped>
.login-container { max-width: 400px; margin: 40px auto; padding: 2em; background: #fff; border-radius: 8px; }
.login-desc { margin-bottom: 1.5em; color: #b51727; font-size: 1.05em; text-align: center; }
input { display: block; width: 100%; margin-bottom: 1em; padding: 0.5em; }
button { width: 100%; padding: 0.7em; }
</style>
