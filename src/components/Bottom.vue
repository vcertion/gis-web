<template>
    <div id="bottom">
        <div class="container">
            <el-row>
            <el-col :md="6" id="responsive-offset">-</el-col>
              <el-col :md="4">
                <div id="logo-wrapper">
                    <img src="../assets/logo_circle.png" alt="科协logo">
                </div>
              </el-col>
            <el-col :md="12" id="content">
                <p>© 2025 SASC</p>
                <p>测试版 v0.0</p>
                 <p class="site-info">技术支持：<a href="https://github.com/vcertion" style="font-weight: bold" target="_blank">ShanQing</a></p>
                <p>Hosted by <a style="font-weight: bold">Github Pages</a></p>        
            </el-col>
            </el-row>
        </div>
    </div>
</template>


<script>
export default {};
</script>

<style lang="less" scoped>
#bottom {
  #responsive-offset {
    color: black;
  }
  width: 100%;
  background-color: black;
  .container {
    height: 100%;
    text-align: center;
    @media (min-width: 992px) {
        #logo-wrapper{
          text-align: right;
          padding-right: 20px;
        }
        #content{
          text-align: left;
          padding-left: 0px;
        }
      }
    p{
      margin: 2px;
    }
    img {
      filter: invert(1);
      height: 100px;
      width: 100px;
    }
  }
  #content {
    color: white;
    a {
      color: white;
      text-decoration: none;
    }
  }
}
</style>


