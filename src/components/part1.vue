<template>
    <div>
  <el-row>
   <el-col style="width: 50%; padding-bottom: 10px; padding-right: 10px;">
    <el-card style="padding:0px;" >
      <img src="../assets/insar2.png" class="image">
      <div style="padding: 14px;">
        <span>InSar形变一张图</span>
        <div class="bottom clearfix">
          <time class="time">InSar形变一张图</time>
          <el-button type="text" class="button" @click="$router.push({path:'/part1_1'})">操作按钮</el-button>
        </div>
      </div>
    </el-card>
  </el-col>
  <el-col style="width: 50%; padding-bottom: 10px; padding-right: 10px;">
    <el-card style="padding:0px;" >
      <img src="../assets/insar2.png" class="image">
      <div style="padding: 14px;">
        <span>InSar形变一张图</span>
        <div class="bottom clearfix">
          <time class="time">InSar形变一张图</time>
          <el-button type="text" class="button" @click="$router.push({path:'/part1_1'})">操作按钮</el-button>
        </div>
      </div>
    </el-card>
  </el-col>
  <el-col style="width: 50%; padding-bottom: 10px; padding-right: 10px;">
    <el-card style="padding:0px;" >
      <img src="../assets/insar2.png" class="image">
      <div style="padding: 14px;">
        <span>InSar形变一张图</span>
        <div class="bottom clearfix">
          <time class="time">InSar形变一张图</time>
          <el-button type="text" class="button" @click="$router.push({path:'/part1_1'})">操作按钮</el-button>
        </div>
      </div>
    </el-card>
  </el-col>
  <el-col style="width: 50%; padding-bottom: 10px; padding-right: 10px;">
    <el-card style="padding:0px;" >
      <img src="../assets/insar2.png" class="image">
      <div style="padding: 14px;">
        <span>InSar形变一张图</span>
        <div class="bottom clearfix">
          <time class="time">InSar形变一张图</time>
          <el-button type="text" class="button" @click="$router.push({path:'/part1_1'})">操作按钮</el-button>
        </div>
      </div>
    </el-card>
  </el-col>
</el-row>
    </div>
</template>

<style>
  .time {
    font-size: 13px;
    color: #999;
  }

  .bottom {
    margin-top: 13px;
    line-height: 12px;
  }

  .button {
    padding: 0;
    float: right;
  }

  .image {
    width: 100%;
    display: block;
  }

  .clearfix:before,
  .clearfix:after {
      display: table;
      content: "";
  }

  .clearfix:after {
      clear: both
  }
</style>

<script>
export default {
  data() {
    return {
      currentDate: new Date(),
    };
  },
};
</script>
