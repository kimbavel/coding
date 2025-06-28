<template>
  <div class="requests-container">
    <h2>매칭 요청 목록</h2>
    <div v-if="role==='mentor'">
      <div v-for="req in incoming" :key="req.id" class="request-message" :mentee="req.menteeId">
        <b>멘티 ID: {{ req.menteeId }}</b>
        <div>{{ req.message }}</div>
        <div id="request-status">상태: {{ req.status }}</div>
        <button id="accept" @click="accept(req.id)" v-if="req.status==='pending'">수락</button>
        <button id="reject" @click="reject(req.id)" v-if="req.status==='pending'">거절</button>
      </div>
    </div>
    <div v-else>
      <div v-for="req in outgoing" :key="req.id">
        <b>멘토 ID: {{ req.mentorId }}</b>
        <div id="request-status">상태: {{ req.status }}</div>
        <button id="cancel" @click="cancel(req.id)" v-if="req.status==='pending'">취소</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';

const incoming = ref([]);
const outgoing = ref([]);
const role = localStorage.getItem('role');

const fetchRequests = async () => {
  if (role === 'mentor') {
    const res = await api.get('/match-requests/incoming', { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
    incoming.value = res.data;
  } else {
    const res = await api.get('/match-requests/outgoing', { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
    outgoing.value = res.data;
  }
};

onMounted(fetchRequests);

const accept = async (id) => {
  await api.put(`/match-requests/${id}/accept`, {}, { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
  fetchRequests();
};
const reject = async (id) => {
  await api.put(`/match-requests/${id}/reject`, {}, { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
  fetchRequests();
};
const cancel = async (id) => {
  await api.delete(`/match-requests/${id}`, { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
  fetchRequests();
};
</script>

<style scoped>
.requests-container { max-width: 600px; margin: 40px auto; padding: 2em; background: #fff; border-radius: 8px; }
.request-message { background: #f7f7f7; margin-bottom: 1em; padding: 1em; border-radius: 6px; }
</style>
