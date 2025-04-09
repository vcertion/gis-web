import Vue from 'vue';
import Router from 'vue-router';
import Home from '@/pages/Home';
import Galley from '@/pages/Galley';
import Timeline from '@/pages/Timeline';
// eslint-disable-next-line camelcase, import/no-unresolved
import Part1_1 from '@/pages/Part1_1';

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/galley',
      name: 'galley',
      component: Galley,
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: Timeline,
    },
    {
      path: '/part1_1',
      name: 'part1_1',
      component: Part1_1,
    },
  ],
});
