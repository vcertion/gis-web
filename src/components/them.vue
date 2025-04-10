<template>
  <div class="main-container">
    <!-- <el-container> -->
      <el-header class="custom-header">
        <h1>管理系统</h1>
      </el-header>
      <el-container direction="horizontal" >
        <el-aside class="custom-aside">
          <el-menu
            class="custom-menu"
            :default-active="activeIndex"
            @select="handleMenuSelect"
          >
            <el-menu-item
              v-for="item in menuItems"
              :key="item.index"
              :index="item.index"
            >
              <i :class="item.icon"></i>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main class="custom-main">
          <component :is="currentComponent" />
        </el-main>
      </el-container>
    <!-- </el-container> -->
  </div>
</template>

<script>
const UserManagement = () => import('../components/part1.vue');

export default {
  data() {
    return {
      activeIndex: '1',
      currentComponent: 'UserManagement',
      menuItems: [
        { index: '1', icon: 'el-icon-user-solid', title: '用户管理', component: 'UserManagement' },
        { index: '2', icon: 'el-icon-s-goods', title: '商品管理', component: 'ProductManagement' },
        { index: '3', icon: 'el-icon-s-order', title: '订单管理', component: 'OrderManagement' },
      ],
    };
  },
  components: {
    UserManagement,
    ProductManagement: { template: '<div>商品管理内容...</div>' },
    OrderManagement: { template: '<div>订单列表内容...</div>' },
  },
  methods: {
    handleMenuSelect(index) {
      this.activeIndex = index;
      this.currentComponent = this.menuItems.find(item => item.index === index).component;
    },
  },
};
</script>

<style scoped>
@import url('../styles/colors.less');
.main-container {
  background: white;
  padding: 50px 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin: 0 auto;

}

.custom-header {
  background: white !important;
  padding: 0 !important;
  height: 80px !important;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #e4e7ed;
}

.custom-header h1 {
  font-size: 2rem;
  color: #303133;
}

.custom-menu {
  border-right: none !important;
  padding: 20px 0;
}

.custom-menu .el-menu-item {
  height: 60px;
  line-height: 60px;
  margin: 8px 12px;
  border-radius: 8px;
  color: #606266 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
}

.custom-menu .el-menu-item i {
  color: #909399;
  font-size: 18px;
  margin-right: 8px;
}

.custom-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #409EFF 0%, #79BBFF 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
}

.custom-menu .el-menu-item.is-active i {
  color: #fff !important;
}

.custom-menu .el-menu-item:not(.is-active):hover {
  background: rgba(64, 158, 255, 0.08) !important;
  color: #409EFF !important;
}

.custom-menu .el-menu-item:not(.is-active):hover i {
  color: #409EFF !important;
}

.el-container {
  flex: 1;
  display: flex;
  flex-direction: row !important;
  width: 50%;
  margin: 0 auto 0 19%;
  background-color: #ededed;
  /* background-color: #606266; */
}
.cunstom-header{
    flex: 0 0 auto;
    min-height: 80px;
}
.el-container > .el-container{
    flex: 1;
    min-height: 0;
}
.custom-aside{
    flex: 0 0 auto;
    display: flex;
    flex-direction: column;
    flex: 0 0 auto;
    width: 220px !important;
    /* background: #f5f7fa; */
    box-shadow: 2px 0 8px rgba(0,0,0,0.05);
}
.custom-menu{
    flex: 1;
    overflow-y:auto
}
.cunstom-main{
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    /* background: #f5f7fa; */
    padding: 30px;
    width: 70%;
    /* max-width: max-content; */
}
</style>
