<template>
<div>
  <Slider/>
  <Them/>
  <About/>
  <!-- <T/> -->
  <Department/>
  <Contact/>
</div>
</template>
<script>
import Slider from '@/components/Slider';
import About from '@/components/About';
// import T from '@/components/T';
import Contact from '@/components/Contact';
import Department from '@/components/Department';
import Them from '@/components/them';

export default {
  components: { Slider, Contact, Department, About, Them },
};
</script>


<style lang="less">
</style>
