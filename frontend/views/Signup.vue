<template>
  <div class="signup-container">
    <h2>회원가입</h2>
    <form @submit.prevent="onSignup">
      <input id="email" v-model="email" type="email" placeholder="이메일" required />
      <input id="password" v-model="password" type="password" placeholder="비밀번호" required />
      <select id="role" v-model="role" required>
        <option value="mentor">멘토</option>
        <option value="mentee">멘티</option>
      </select>
      <input id="name" v-model="name" type="text" placeholder="이름" required />
      <button id="signup" type="submit">회원가입</button>
    </form>
    <p>
      이미 계정이 있으신가요?
      <router-link to="/login">로그인</router-link>
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
const name = ref('');
const role = ref('mentee');
const error = ref('');
const router = useRouter();

const onSignup = async () => {
  error.value = '';
  try {
    await api.post('/signup', { email: email.value, password: password.value, name: name.value, role: role.value });
    router.push('/login');
  } catch (e) {
    error.value = e.response?.data?.detail || '회원가입 실패';
  }
};
</script>

<style scoped>
.signup-container { max-width: 400px; margin: 40px auto; padding: 2em; background: #fff; border-radius: 8px; }
input, select { display: block; width: 100%; margin-bottom: 1em; padding: 0.5em; }
button { width: 100%; padding: 0.7em; }
</style>
