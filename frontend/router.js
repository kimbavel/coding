import { createRouter, createWebHistory } from 'vue-router';
import Login from './views/Login.vue';
import Signup from './views/Signup.vue';
import Profile from './views/Profile.vue';
import Mentors from './views/Mentors.vue';
import Requests from './views/Requests.vue';

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/signup', component: Signup },
  { path: '/profile', component: Profile },
  { path: '/mentors', component: Mentors },
  { path: '/requests', component: Requests },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
