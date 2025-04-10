<template>
<header :class="['navbar',(scrolled || !isHome)?'navbar-solid':'navbar-transparent']">
    <div class="container">
        <div class="home">
            <a href="/">
                <img src="../assets/logo.png" alt="Logo" style="height: 40px">
            </a>
        </div>
        <div class="menus hidden-xs-only">
            <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal"  :router="true">
                <el-menu-item index="/">首页</el-menu-item>
                <el-menu-item index="/galley">菜单2</el-menu-item>
                <el-menu-item index="/news">菜单3</el-menu-item>
                <el-menu-item index="/timeline">菜单4</el-menu-item>
                <el-menu-item index="/files">菜单5</el-menu-item>
                <el-menu-item index="/competition">菜单6</el-menu-item>
                <el-menu-item index="/login">登录</el-menu-item>
            </el-menu>
        </div>
  
            <el-dropdown trigger="click"  @command="handleCommand">
        <span class="el-dropdown-link hidden-sm-and-up">
            <i class="el-icon-menu"></i>
        </span>
        <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="/">首页</el-dropdown-item>
            <el-dropdown-item command="/galley">菜单2</el-dropdown-item>
            <el-dropdown-item command="/news">菜单3</el-dropdown-item>
            <el-dropdown-item command="/timeline">菜单4</el-dropdown-item>
            <el-dropdown-item command="/file">菜单5</el-dropdown-item>
            <el-dropdown-item command="/competition">菜单6</el-dropdown-item>
            <el-dropdown-item command="/login">登录</el-dropdown-item>
        </el-dropdown-menu>
        </el-dropdown>

        
    </div>
</header>

  
</template>
<script>
  export default {
    props: ['isHome'], // 如果是主页的navbar，则添加透明滚动渐变效果
    data() {
      return {
        scrolled: false, // 是否有滚动
      };
    },
    computed: {
      activeIndex() {
        return `/${this.$route.path.split('/')[1]}`;
      },
    },
    methods: {
      handleScroll() {
        this.scrolled = window.scrollY > 0; // 滚动事件的回调
      },
      handleCommand(command) { // 小屏状态时的下来菜单点击回调
        this.$router.push(command);
      },
    },
    mounted() {
      window.addEventListener('scroll', this.handleScroll); // 监听滚动事件
    },
};
</script>




<style lang="less" scoped>
@import 'element-ui/lib/theme-chalk/display.css';
@import url('../styles/colors.less');

// 菜单栏
.navbar{
    .el-dropdown{
        float: right;
        color: white;
        font-size: 24px;
        font-weight: 700;
        padding-top: 10px;
        user-select: none;
        cursor:pointer;
    }

    .el-menu{
    background-color:rgba(0, 0, 0, 0);
    color:white;
    bottom: 0;
    border-bottom: none;
    .el-menu-item{
        height: 50px;
        line-height: 50px;
        transition: all 0.4s ease 0s;
        font-size: 14px;
        font-weight: 700;
        color:white;
        background-color: rgba(0, 0, 0, 0);
        &.is-active{
            font-size: 16px;
            color: @blue;
            border-bottom: 2px solid @blue !important;
        }
        &:hover{
            font-size: 16px;
            color: @blue;
            background: rgba(0, 0, 0, 0);
            transition: all 0.4s ease 0s;
            border-bottom: 2px solid @blue !important;
        }
    }
}

}

// 透明状态的菜单栏
.navbar-transparent{
    padding-top: 30px;
    transition: all 0.3s ease 0s;
}

// 非透明状态的菜单栏
.navbar-solid {
    // box-shadow: 0 0 100px 10px rgba(0,0,0,1);
    padding-top:5px;
    background-color: #000 !important;
    transition: all 0.3s ease 0s;
    // .el-menu-item:hover, .is-active{
    //     transition: all 0.4s ease 0s;
    //     box-shadow: 0 0 100px 10px rgba(0,0,0,1);
    // }
}


header{
    height: 50px;
    width: 100%;
    position: fixed;
    left: 0;
    top: 0;
    z-index:1000;
    .home{
        float: left;
    }
    .menus{
        float: right;
    }
}

</style>
