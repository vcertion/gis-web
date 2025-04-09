<template>
  <div style="background-color:white;padding-top:50px;padding-bottom:50px">
      <div>
              <el-row :sm="8" v-for="(department, index) in departments" :key="index">
                  <el-card :body-style="{ padding: '0px' }" shadow="hover" style="background-color:#ededed">
                      <div class="card-content" :class="{reverse: index % 2 !== 0}">
                          <div class="left">
                              <img :src="department.url" class="image">
                          </div>
                          <div class="right">
                              <p style="text-align:center;">{{department.name}}</p>
                              <div class="bottom clearfix">
                                  <p style="color:#909399; line-height: 20px; text-align:center;">{{department.desc}}</p>
                              </div>

                          </div>
                      </div>
                  </el-card>
              </el-row>

      </div>
  </div>
</template>

<style>
  .time{
      font-size: 13px;
      color: #999;
  }

  .bottom{
      margin-top: 13px;
      line-height: 12px;
  }

  .button{
      padding: 0;
      float: right;
  }

  .image{
      width: 100%;
      display: block;
  }

  .clearfix:before,
  .clearfix:after{
      content: "";
      display: table;
  }

  .clearfix:after{
      clear: both;
  }

  .card-content{
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
  }

  .left{
      flex: 1;
  }

  .right{
      flex: 1;
  }

  .reverse{
      flex-direction: row-reverse;
  }
</style>

<script>/* eslint-disable */ 
export default {
  data () {
  return {
    departments: [
      {
        name: '部分1',
        url: require('../assets//tu01.png'),
        desc: '部分1的描述'
      },
      {
        name: '部分2',
        url: require('../assets/tu02.png'),
        desc: '部分2的描述'
      },
      {
        name: '部分3',
        url: require('../assets/tu03.png'),
        desc: '部分3的描述'
      }
    ]
  }
},
};
</script>
