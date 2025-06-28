<template>
  <div class="mentors-container">
    <h2>멘토 목록</h2>
    <input id="search" v-model="search" placeholder="기술 스택 검색" @input="fetchMentors" />
    <select id="name" v-model="orderBy" @change="fetchMentors">
      <option value="">정렬 없음</option>
      <option value="name">이름순</option>
      <option id="skill" value="skill">스킬셋순</option>
    </select>
    <div v-if="mentors.length === 0">멘토가 없습니다.</div>
    <div v-for="mentor in mentors" :key="mentor.id" class="mentor">
      <img :src="`/api/images/mentor/${mentor.id}`" width="60" height="60" style="object-fit:cover;border-radius:50%" />
      <div>
        <b>{{ mentor.profile.name }}</b>
        <div>{{ mentor.profile.bio }}</div>
        <div>기술: {{ mentor.profile.skills.join(', ') }}</div>
      </div>
      <button id="request" @click="openRequest(mentor)">매칭 요청</button>
    </div>
    <div v-if="showRequest">
      <textarea id="message" v-model="message" :data-mentor-id="selectedMentor?.id" :data-testid="`message-${selectedMentor?.id}`" placeholder="요청 메시지"></textarea>
      <button id="request" @click="sendRequest">요청 보내기</button>
      <button @click="showRequest=false">취소</button>
      <div v-if="reqError" style="color:red">{{ reqError }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';

const mentors = ref([]);
const search = ref('');
const orderBy = ref('');
const showRequest = ref(false);
const selectedMentor = ref(null);
const message = ref('');
const reqError = ref('');

const fetchMentors = async () => {
  try {
    const params = {};
    if (search.value) params.skill = search.value;
    if (orderBy.value) params.orderBy = orderBy.value;
    const res = await api.get('/mentors', {
      params,
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    });
    mentors.value = res.data;
  } catch (e) {
    mentors.value = [];
  }
};

onMounted(fetchMentors);

const openRequest = (mentor) => {
  selectedMentor.value = mentor;
  showRequest.value = true;
  message.value = '';
  reqError.value = '';
};

const sendRequest = async () => {
  try {
    await api.post('/match-requests', {
      mentorId: selectedMentor.value.id,
      menteeId: JSON.parse(atob(localStorage.getItem('token').split('.')[1])).user_id,
      message: message.value
    }, { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
    showRequest.value = false;
    fetchMentors();
  } catch (e) {
    reqError.value = e.response?.data?.detail || '요청 실패';
  }
};
</script>

<style scoped>
.mentors-container { max-width: 600px; margin: 40px auto; padding: 2em; background: #fff; border-radius: 8px; }
.mentor { display: flex; align-items: center; gap: 1em; margin-bottom: 1em; background: #f7f7f7; padding: 1em; border-radius: 6px; }
button { margin-left: auto; }
</style>
