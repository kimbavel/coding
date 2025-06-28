<template>
  <div class="profile-container" v-if="user">
    <h2>내 프로필</h2>
    <form @submit.prevent="onSave">
      <input id="name" v-model="user.profile.name" type="text" placeholder="이름" required />
      <textarea id="bio" v-model="user.profile.bio" placeholder="소개" required></textarea>
      <div v-if="user.role === 'mentor'">
        <input id="skillsets" v-model="skills" type="text" placeholder="기술 스택 (쉼표로 구분)" />
      </div>
      <div>
        <img :src="profileImageUrl" id="profile-photo" width="120" height="120" style="object-fit:cover;border-radius:50%" />
        <input id="profile" type="file" accept=".jpg,.png" @change="onFileChange" />
      </div>
      <button id="save" type="submit">저장</button>
    </form>
    <div v-if="msg" style="color:green">{{ msg }}</div>
    <div v-if="error" style="color:red">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../api';
import { useRouter } from 'vue-router';

const user = ref(null);
const error = ref('');
const msg = ref('');
const skills = ref('');
const imageFile = ref(null);
const router = useRouter();

const getProfile = async () => {
  try {
    const res = await api.get('/me', { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
    user.value = res.data;
    if (user.value.role === 'mentor') skills.value = user.value.profile.skills.join(',');
  } catch (e) {
    router.push('/login');
  }
};

onMounted(getProfile);

const onFileChange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    error.value = 'jpg 또는 png 파일만 업로드 가능합니다.';
    return;
  }
  if (file.size > 1024 * 1024) {
    error.value = '1MB 이하 이미지만 업로드 가능합니다.';
    return;
  }
  imageFile.value = file;
};

const onSave = async () => {
  error.value = '';
  msg.value = '';
  let imageBase64 = '';
  if (imageFile.value) {
    imageBase64 = await toBase64(imageFile.value);
  }
  try {
    if (user.value.role === 'mentor') {
      await api.put('/profile', {
        id: user.value.id,
        name: user.value.profile.name,
        role: 'mentor',
        bio: user.value.profile.bio,
        image: imageBase64,
        skills: skills.value.split(',').map(s => s.trim()).filter(Boolean),
      }, { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
    } else {
      await api.put('/profile', {
        id: user.value.id,
        name: user.value.profile.name,
        role: 'mentee',
        bio: user.value.profile.bio,
        image: imageBase64,
      }, { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
    }
    msg.value = '저장되었습니다.';
  } catch (e) {
    error.value = e.response?.data?.detail || '저장 실패';
  }
};

const toBase64 = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = () => resolve(reader.result.split(',')[1]);
  reader.onerror = reject;
});

const profileImageUrl = computed(() => {
  if (!user.value) return '';
  if (user.value.profile.imageUrl) {
    return `http://localhost:8080/api/images/${user.value.role}/${user.value.id}`;
  }
  return user.value.role === 'mentor'
    ? 'https://placehold.co/500x500.jpg?text=MENTOR'
    : 'https://placehold.co/500x500.jpg?text=MENTEE';
});
</script>

<style scoped>
.profile-container { max-width: 500px; margin: 40px auto; padding: 2em; background: #fff; border-radius: 8px; }
input, textarea { display: block; width: 100%; margin-bottom: 1em; padding: 0.5em; }
button { width: 100%; padding: 0.7em; }
</style>
