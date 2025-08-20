<template>
  <div class="map-container">
    <div id="cesiumContainer">
      <!-- 控制按钮和侧边栏容器 -->
      <div class="controls-sidebar-container">
        <!-- 按钮 -->
        <div class="map-controls">
        <el-button @click="toggleSidebar" type="info" circle size="small">
         <i class="el-icon-menu"></i>
        </el-button>
        
        <el-upload
          action="http://127.0.0.1:5000/process-zip"
          :on-success="handleSuccess"
          :show-file-list="false"
          :before-upload="beforeUpload"
          accept=".zip"
        >
          <el-button 
            type="primary" 
            circle
            size="small"
          >
            <i class="el-icon-upload"></i> <!-- 上传图标 -->
          </el-button>
        </el-upload>
        <el-button 
          type="danger"
          @click="clearData"
          style="small"
        >
        <i class="el-icon-delete"></i> <!--删除-->
        </el-button>
        </div>

        <!-- 侧边栏 -->
        <div class="sidebar" v-if="showSidebar">
        <el-tree
          :data="vectorTreeData"
          show-checkbox
          node-key="id"
          :default-checked-keys="defaultCheckedKeys"
          :props="treeProps"
          @check-change="handleCheckChange"
          @node-click="handleNodeClick">
          <template #default="{ node, data }">
            <span class="tree-node">
                <span>{{ node.label }}</span>

                <span 
                  v-if="data.type === 'color-preview'">
                  <span
                  class="color-preview-block"
                  :style="getPreviewStyle(data.colorScheme)"
                  ></span>
                  </span>
            </span>
          </template>
        </el-tree>

        <!-- 编辑对话框 -->
        <el-dialog
          title="编辑图层样式"
          :visible.sync="editDialogVisible"
          width="50%"
          :modal="false"
        >
        <el-form label-width="100px">
          <el-form-item label="选择属性">
            <el-select
              v-model="editingData.selectedAttribute"
              placeholder="请选择属性">
              <el-option
                v-for="attr in getAvailableAttributes(editingData.id)"
                :key="attr"
                :label="attr"
                :value="attr"/>
            </el-select>
          </el-form-item>

          <el-form-item label="选择色带">
            <el-select
              v-model="editingData.selectedColorScheme"
              placeholder="请选择色带">
              <el-option
                v-for="(colors,name) in colorScheme"
                :key="name"
                :label="name"
                :value="name"
                />
            </el-select>

            <!-- 色带预览 -->
             <div
              class="dialog-preview"
              :style="getPreviewStyle(editingData.selectedColorScheme)"
              ></div>
          </el-form-item>
        </el-form>

        <span slot="footer">
          <el-button @click="editDialogVisible=false">取消</el-button>
          <el-button type="primary" @click="confirmEdit">确定</el-button>
        </span>
      </el-dialog>
      </div>
      </div>
      <div style="display: flex; flex-direction:column;position: absolute;right:15px;top:50%;z-index: 10;">
      <div class="toolbar-buttons">
    <el-popover
      placement="left"
      width="300"
      height="250"
      trigger="manual"
      v-model="popoverVisible"
    >
    <div class='popover-content'>

      <el-tabs v-model="activeTab" type="card" size="mini">
        <el-tab-pane label="剖面分析" name="profile">
          <div class="popover-controls">
        <el-button
        size="mini"
        class="popover-edit"
        @click="drawLine"
        >
        <i class="el-icon-edit"></i>
        </el-button>
        <el-button
          size="mini"
          class="popover-refresh"
          @click="cleardraw">
            <i class="el-icon-refresh"></i>
        </el-button>

        <el-button
        size="mini"
        class="popover-close"
        @click="closePopover"
        >
          <i class="el-icon-close"></i>
        </el-button>
      </div>
              <!-- 小型折线图 -->
      <div ref="smallChart" class="small-chart"
       @click="showLargeChart"
      ></div>
      <div class="attribute-select-container">
        <div style="display: flex; align-items:center;">
        <span class="attribute-label">图层：</span>
        <el-select
          v-model="selectedLayer"
          @change="onLayerChange"
          style="width: 100%; margin-bottom: 8px;"
        >
        <el-option
          v-for="item in layerOption"
          :key="item.id"
          :label = "item.name"
          :value="item.id"/>
      </el-select>
      </div>
      <div style="display: flex; align-items: center;">
      <span class="attribute-label">属性：</span>
      <el-select
       v-model="selectedAttribute"
       @change="onAttributeChange"
       style="width: 100%;">
      <el-option
        v-for="attr in attributeOption"
        :key="attr"
        :label="attr"
        :value="attr"
      />
      </el-select>
    </div>  
    </div>
        </el-tab-pane>

        <el-tab-pane label="单点分析" name="singlePoint">
          <div class="popover-controls single-point-controls">
            <el-button
            size="mini"
            class="popover-close"
            @click="closePointAnalysisPopover"
            >
              <i class="el-icon-close"></i>
            </el-button>
          </div>
          <div class="single-point-analysis">
            <el-form label-width="80px" size="mini">
              <el-form-item label="选择图层">
                <el-select
                v-model="selectedPointLayer"
                @change="onPointLayerChange"
                placeholder="请选择图层"
                style="width: 100%;"
                >
                <el-option
                v-for="item in layerOption"
                :key="item.id"
                :label="item.name"
                :value="item.id"
                />
              </el-select>
              </el-form-item>
              <el-form-item label="选择属性">
                <el-select
                v-model="selectedPointAttributes"
                @change="onPointAttributesChange"
                multiple
                placeholde="请选择属性（多选）"
                style="width: 100%;"
                :disabled="!selectedPointLayer"
                >
                  <el-option
                  v-for="attr in availablePointAttributes"
                  :key="attr"
                  :label="attr"
                  :value="attr"
                  />
              </el-select>
              </el-form-item>
            </el-form>
            <div v-if="pointAttributeChartData.length > 0" class="point-attribute-chart">
              <h5 style="margin: 10px 0; text-align: center;">属性信息</h5>
              <div ref="pointAttributeChart" @click="showPointAttributeLargeChart" style="width: 100%;  height: 120px; cursor: pointer;"></div>
            </div>
            <div v-else class="no-data-tip">
              <i class="el-icon-location"></i>
              请选择地图上一个点进行分析
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

    </div>
    <el-tooltip slot="reference" content="剖面分析" placement="left">
      <el-button  size="small" @click="showProfileAnalysis">
        <i class="el-icon-s-data"></i>
      </el-button>
    </el-tooltip>

  </el-popover>
    </div>
    <div class="toolbar-buttons">
      <el-popover 
        placement="left"
        width="300"
        height="250"
        trigger="manual"
        v-model="measureDistancePopoverVisible"
        :visible.sync="measureDistancePopoverVisible"
      >
      <div class="measure-popover-content">
        <h4 style="margin-top: 0px;">距离测量</h4>
        <div class="measure-controls">
          <el-button
            size="mini"
            type="primary"
            @click="startMeasureDistance"
            :disabled="isMeasuringDistance"
          >
          <i class="el-icon-location"></i>
          </el-button>
          <el-button
          size="mini"
          class="popover-close"
          @click="closeMeasureDistancePopover">
          <i class="el-icon-close"></i>
          </el-button>
        </div>
        <div v-if="distanceResult" class="measure-result">
          <p><strong>总距离：</strong>{{ distanceResult.totalDistance }}米</p>
          <p><strong>分段距离：</strong></p>
          <ul>
            <li v-for="(segment, index) in distanceResult.segments" :key="index">
              第{{ index + 1 }}段：{{ segment.distance }}米
            </li>
          </ul>
        </div>
        <div v-else class="measure-instruction">
          <p>点击开始测距后，在地图上点击多个点进行测距</p>
        </div>
      </div>
      <el-tooltip slot="reference" content="测距工具" placement="left">
        <el-button size="small" @click="toggleMeasureDistance">
          <i class="el-icon-edit"></i>
        </el-button>
      </el-tooltip>
      </el-popover>
    </div>

    <div class="toolbar-buttons">
      <el-popover
      placement="left"
      width="300"
      height="250"
      trigger="manual"
      v-model="measureAreaPopoverVisible"
      :visible.sync="measureAreaPopoverVisible"
      >
      <div class="measure-area-popover-content">
        <h4 style="margin-top: 0px;">面积测量</h4>
        <div class="measure-controls">
          <el-button
          size="mini"
          type="primary"
          @click="startMeasureArea"
          :disabled="isMeasuringArea"
          >
          <i class="el-icon-crop"></i>
        </el-button>
        <el-button
        size="mini"
        @click="clearMeasureArea"
        :disabled="!isMeasuringArea"
        >
        <i class="el-icon-delete"></i>
      </el-button>
      <el-button
      size="mini"
      class="popover-close"
      @click="closeMeasureAreaPopover">
      <i class="el-icon-close"></i>
    </el-button>
        </div>
        <div v-if="areaResult" class="measure-result">
          <p><strong>总面积：</strong>{{ areaResult.totalArea }}平方米</p>
          <p><strong>周长：</strong>{{ areaResult.perimeter }}米</p>
        </div>
        <div v-else class="measure-instruction">
          <p>点击开测面积后，在地图上点击多个点进行测面积</p>
        </div>
      </div>
      <el-tooltip
        slot="reference"
        content="面积测量"
        placement="left"
      >
      <el-button size="small" @click="toggleMeasureArea">
        <i class="el-icon-picture-outline"></i>
      </el-button>
    </el-tooltip>
      </el-popover>
    </div>
    <div class="toolbar-buttons">
      <el-popover
        placement="left"
        width="350"
        height="400"
        trigger="click"
      >
      <div class="legend-popover-content">
        <div class="legend-selector">
          <h4 style="text-align: center;margin-top: 0px;">图层图例</h4>
          <el-form label-width="80px" size="small">
            <el-form-item label="选择图层">
              <el-select
                v-model="legendSelectedLayer"
                @change="onLegendLayerChange"
                placeholder="请选择图层"
                style="width: 100%;"
              >
                <el-option
                v-for="item in layerOption"
                :key="item.id"
                :label="item.name"
                :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="选择数据">
              <el-select
                v-model="legendSelectedAttribute"
                @change="onLegendAttributeChange"
                placeholder="请选择属性"
                style="width: 100%;"
                :disabled="!legendSelectedLayer"
              >
              <el-option
                v-for="attr in legendAttributeOptions"
                :key="attr"
                :label="attr"
                :value="attr"
              />
            </el-select>
            </el-form-item>
          </el-form>
        </div>
        <div v-if="legendSelectedLayer && legendSelectedAttribute" class="legend-display">
          <div class="legend-info">
            <p><strong>图层名称：</strong>{{ getLayerName(legendSelectedLayer) }}</p>
            <p><strong>属性字段：</strong>{{ legendSelectedAttribute }}</p>
            <p><strong>数据范围：</strong>{{ legendDataRange.min }}-{{ legendDataRange.max }}</p>
          
          </div>

          <div class="color-scheme-preview">
            <h5>色带预览</h5>
            <div
              class="color-gradient"
              :style="getLegendColorGradient()"></div>
            <dic class="color-labels">
              <span>{{ legendDataRange.min }}</span>
              <span>{{ legendDataRange.max }}</span>
            </dic>
          </div>
        </div>
      </div>
      <el-tooltip slot="reference" content="图层图例" placement="left">
        <el-button  size="small">
          <i class="el-icon-picture"></i>
        </el-button>
      </el-tooltip>
    </el-popover>
    </div>
    </div>
    </div>


  <el-dialog
      title="元素属性"
      :visible.sync="attributeDialogVisible"
      width="50%"
    >
    <el-table :data="[currentAttributes]" border>
      <el-table-column
      v-for="column in attributeColumns"
      :key="column.prop"
      :prop="column.prop"
      :label="column.label"
      />
    </el-table>
  </el-dialog>

<el-dialog
  :visible.sync="showDialog"
  width="60%"
  @open="handleLargeChartOpen"
>
  <div
    ref="largeChart"
    class="large-chart-container"
  >
  </div>
</el-dialog>

  </div>
</template>

<script>
/* eslint-disable */
import { GeoJsonDataSource, objectToQuery } from "cesium";
import Color from "cesium/Source/Core/Color";
import CheckerboardMaterialProperty from "cesium/Source/DataSources/CheckerboardMaterialProperty";
import Cesium3DTile from "cesium/Source/Scene/Cesium3DTile";
import { pitch } from "file-loader";
import { head } from "shelljs";
import { expand } from "shelljs/src/common";
import 'element-ui/lib/theme-chalk/icon.css'
import { LabelsLayer } from "@amap/amap-vue";
import { keys, values } from "shelljs/commands";
import kdbush from 'kdbush';
import geokdbush, { distance } from 'geokdbush';
import { minSatisfying } from "semver";
import dist from "vue-amap";
import * as echarts from 'echarts'
import { name } from "file-loader";
import ImageMaterialProperty from "cesium/Source/DataSources/ImageMaterialProperty";
import { polygon, polyline, tooltip } from "leaflet";
import Interval from "cesium/Source/Core/Interval";

export default {
  data() {
    return {

        largeChartInstance:null,
        dialogResizeObserver:null,

        activeTab:'profile',
        selectedPointLayer:'',
        selectedPointAttributes:'',
        pointClickHandler:null,
        clickedPoint:null,
        pointAttributeChartData:[],
        availablePointAttributes:[],



        popoverVisible:false,//控制popover
        showDialog:false,//绘图对话框
        intersectingPoints:[],//储存相交点数据
        selectedLayer:'',
        selectedAttribute:'',

        isDrawingLine:false,
        tempLine:null,
        drawHandler: null,
        drawLinePoints:[],
        drawlines:[],
        // isValidCartesian:this.isValidCartesian,

        //测距相关
        measureDistancePopoverVisible: false,
        isMeasuringDistance: false,
        distanceHandler:null,
        distancePoints:[],
        distanceEntities:[],
        distanceResult:null,

        //测面积相关
        measureAreaPopoverVisible:false,
        isMeasuringArea:false,
        areaHandler:null,
        areaPoints:[],
        areaEntities:[],
        areaResult:null,

        //图例相关
        legendSelectedLayer:'',
        legendSelectedAttribute:'',
        legendDataRange:{min:0,max:0},

    
        //对话框相关状态
        editDialogVisible:false,
        editingData:{
          id:null,
          selectedAttribute:'',
          selectedColorScheme:''
        },
        // selectedAttribute:'default',//当前选择中的属性字段
        // selectedColorScheme:'red-yellow-green',
        colorScheme:{
            // 基础色带
            '红黄绿': ['#ff0000', '#ffff00', '#00ff00'],
            '蓝紫红': ['#0000ff', '#800080', '#ff0000'],
            '紫罗兰': ['#440154', '#21908d', '#fde725'],

            // 渐变色带
          '蓝色渐变': ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#08306b'],
          '绿色渐变': ['#f7fcf5', '#c7e9c0', '#74c476', '#238b45', '#00441b'],
          '红色渐变': ['#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'],
          '蓝白红': ['#3182bd', '#deebf7', '#fee0d2', '#de2d26'],
          '绿黄': ['#31a354', '#addd8e'],
          '紫粉': ['#756bb1', '#fcc5c0'],
          '彩虹': ['#ff0000', '#ff9900', '#ffff00', '#00ff00', '#00ffff', '#0000ff', '#9900ff'],
          '自然': ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3'],
          '明亮': ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00'],
          '地形': ['#ffffcc', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494'],
          '高程': ['#006837', '#31a354', '#78c679', '#c2e699', '#ffffcc'],
          '海洋': ['#f7fcf0', '#e0f3db', '#ccebc5', '#a8ddb5', '#7bccc4'],
          '温度': ['#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b'],
          '火焰': ['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#f03b20', '#bd0026'],
          '冰蓝': ['#f7fbff', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c'],
          '十二色': ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928'],
          '配对': ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a'],
          '集合三': ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9'],
          '交通灯': ['#d7191c', '#fdae61', '#ffffbf', '#a6d96a', '#1a9641'],
          '警告': ['#ffeda0', '#feb24c', '#f03b20', '#bd0026'],
          '昼夜': ['#081d58', '#253494', '#225ea8', '#1d91c0', '#41b6c4', '#7fcdbb', '#c7e9b4', '#edf8b1', '#ffffd9'],
          '莫兰迪': ['#b8c2cc', '#a5b4c4', '#8796a8', '#6a7b8f', '#4f6272'],
          '马卡龙': ['#ff9ff3', '#feca57', '#ff6b6b', '#48dbfb', '#1dd1a1'],
          '复古': ['#e6c229', '#f17105', '#d11149', '#6610f2', '#1a8fe3'],
          '灰度': ['#ffffff', '#f0f0f0', '#d9d9d9', '#bdbdbd', '#969696', '#737373', '#525252', '#252525', '#000000'],
          '粉彩': ['#ffb3ba', '#ffdfba', '#ffffba', '#baffc9', '#bae1ff'],
          '金属': ['#e0e0e0', '#c0c0c0', '#a0a0a0', '#808080', '#606060'],
          '秋季': ['#f6d746', '#f5b349', '#f3904f', '#ed6a5a', '#e83f6f'],
          '春季': ['#d4f1f9', '#a2d9f7', '#75c8f0', '#4fb3e3', '#2f9ed8'],
          '冬季': ['#ffffff', '#e6f3ff', '#cce6ff', '#99ccff', '#66b3ff'],
  
  // 纯色选项
      '纯红色': ['#ff0000'],
      '纯绿色': ['#00ff00'],
      '纯蓝色': ['#0000ff'],
      '纯黄色': ['#ffff00'],
      '纯紫色': ['#800080'],
      '纯橙色': ['#ffa500'],
      '纯粉色': ['#ffc0cb'],
      '纯青色': ['#00ffff'],
      '纯棕色': ['#a52a2a'],
      '纯灰色': ['#808080'],
      '纯黑色': ['#000000'],
      '纯白色': ['#ffffff'],
      '深红色': ['#8b0000'],
      '深绿色': ['#006400'],
      '深蓝色': ['#00008b'],
      '浅红色': ['#ffcccb'],
      '浅绿色': ['#90ee90'],
      '浅蓝色': ['#add8e6'],
        },

        attributeDialogVisible: false,// 控制属性弹窗显示
        currentAttributes:{},// 存储当前点击元素的属性
        attributeColumns:[],  // 动态生成表格列

        showSidebar: false,
        vectorTreeData: [],
        treeProps:{
          label: 'label',
          children: 'children',
          // disabled:(data) => data.type === 'color-picker'
        },
        vectorItems:{},//索引储存
        defaultCheckedKeys:[],//储存默认勾选ID
        predefineColors: [
          '#ff4500',
          '#ff8c00',
          '#ffd700',
          '#90ee90',
          '#00ced1',
          '#1e90ff',
          '#c71585',
          'rgba(255, 69, 0, 0.68)',
          'rgb(255, 120, 0)',
          'hsv(51, 100, 98)',
          'hsva(120, 40, 94, 0.5)',
          'hsl(181, 100%, 37%)',
          'hsla(209, 100%, 56%, 0.73)',
          '#c7158577'
        ]
      };
  },

  name: "CesiumView",
  mounted() {
    this.initMap();
    setTimeout(() => {
      this.initSmallChart();
    }, 100);
  },
  watch:{
    intersectingPoints:{
      handler(newPoints){
        if(newPoints.length>0 && this.selectedLayer && this.selectedAttribute){
          setTimeout(() => {
          this.updateSmallChart();
        }, 0);
      }
      },
      deep:true
    },
  },
  computed:{
    layerOption(){
      const options = Object.values(this.vectorItems).map(item =>({
        id:item.id,
        name:item.name
      }));

      return options
    },

    attributeOption(){
      if(!this.selectedLayer) return[];

      const item = this.vectorItems[this.selectedLayer];
      if(!item)return[];


      if(item.pointFeatures && item.pointFeatures.length > 0){
          return Object.keys(item.pointFeatures[0].properties);
        }

        //如果没有点数据，则加载限免数据
        if(item.dataSource && item.dataSource.entities.values.length >0){
          const firstEntity = item.dataSource.entities.values[0];
          if (firstEntity.properties){
            return Object.keys(firstEntity.properties.getValue());
          }
        }
        return [];
    },
    legendAttributeOptions(){
      if(!this.legendSelectedLayer) return[];

      const item = this.vectorItems[this.legendSelectedLayer];
      if(!item)return [];

      if(item.pointFeatures && item.pointFeatures.length >0){
        return Object.keys(item.pointFeatures[0].properties);
      }

      if(item.dataSource && item.dataSource.entities.values.length>0){
        const firstEntity = item.dataSource.entities.values[0];
        if(firstEntity.properties){
          return Object.keys(firstEntity.properties.getValue());
        }
      }
      return [];
    }
  },
  methods: {
    initMap() {
      Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkOWNmNmU2Mi01N2YzLTRmMmItYTMyZS1lMGZhNDIxZWE3YjgiLCJpZCI6MjkzMTA2LCJpYXQiOjE3NDY1ODIyMzN9.kboCT_PRY0z00d0qdEcLYafyuNZtmFsJ92x7oeXjzPY'

      this.viewer = new Cesium.Viewer('cesiumContainer',{
          homeButton: true,
          sceneModePicker: true,
          baseLayerPicker: true, // 影像切换
          animation: false, // 是否显示动画控件
          infoBox: false, // 是否显示点击要素之后显示的信息
          selectionIndicator: false, // 要素选中框
          geocoder: false, // 是否显示地名查找控件
          timeline: false, // 是否显示时间线控件
          fullscreenButton: false,
          shouldAnimate: false,
          navigationHelpButton: false, // 是否显示帮助信息控
      });

      this.viewer._cesiumWidget._creditContainer.style.display = 'none';
      
    },
    // 当对话框大小变化时，图表会自动调整以适应新的容器尺寸
    handleLargeChartOpen(){
      this.$nextTick(()=>{
        if(this.dialogResizeObserver){
          this.dialogResizeObserver.disconnect();
        }
        this.dialogResizeObserver = new ResizeObserver(()=>{
          if(this.largeChartInstance){
            this.largeChartInstance.resize();
          }
        });

        //监听对话框内容
        const dialogContent = this.$el.querySelector('.el-dialog__body');
        if(dialogContent){
          this.dialogResizeObserver.observe(dialogContent);
        }
      });
    },
    //单点属性分析
    onPointLayerChange(layerId){
      this.selectedPointLayer=layerId;
      this.selectedPointAttributes='';
      this.clickedPoint = null;
      this.pointAttributeChartData=[];
      this.updateAvailablePointAttribute();
      console.log('可用属性:', this.availablePointAttributes); // 添加调试日志

      this.setupPointClickHandler();
    },
    onPointAttributesChange(attribute){
      this.selectedPointAttributes = attribute;
      if(!attribute || attribute.length ===0){
        this.pointAttributeChartData=[];
        this.clickedPoint = null;
        this.$nextTick(()=>{
          if(this.$refs.pointAttributeChart){
            const chart = echarts.init(this.$refs.pointAttributeChart);
            const option={
        tooltip:{
          trigger:'axis',
          formatter:function(params){
            return `${params[0].name}:${params[0].value}`;
          }
        },
        xAxis:{
          type:'category',
          data:this.pointAttributeChartData.map(item => item.attribute),
          axisLabel:{
            fontSize:10,
            rotate:45,
            interval:0,
          },
        },
        yAxis:{
          type:'value',
          axisLabel:{fontSize:10,interval:0},
        },
        series:[{
          type:'line',
          data:this.pointAttributeChartData.map(item =>item.value),
        }],
        grid:{
          left: 0,    // 增加左边距
          right: 0,   // 增加右边距
          top: 5,
          bottom: 0,
          containLabel: true
        }
        
      };
            chart.setOption(option);
          }
        });
        return;
      }
      if(this.clickedPoint && this.selectedAttribute.length >0){
        this.updatePointAttributeChart();
      }
    },
    updateAvailablePointAttribute(){

      if(!this.selectedPointLayer){
        this.availablePointAttributes=[];
        return;
      }

      const item = this.vectorItems[this.selectedPointLayer]

      if(!item){
        this.availablePointAttributes=[]
        return;
      }
      if(item.pointFeatures && item.pointFeatures.length > 0){
        this.availablePointAttributes = Object.keys(item.pointFeatures[0].properties);
      }else if(item.dataSource && item.dataSource.entities.length >0){
        const firstEntity = item.dataSource.entities.values[0];
        if(firstEntity.properties){
          this.availablePointAttributes = Object.keys(firstEntity.properties.getValue());
        }
      }else{
        this.availablePointAttributes = [];
      }
    },
    setupPointClickHandler(){
      if(this.pointClickHandler){
        this.pointClickHandler.destroy();
        this.pointClickHandler=null;
      }

      if(!this.selectedPointLayer){
        return;
      }
      //创建新的点击器
      this.pointClickHandler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
      this.pointClickHandler.setInputAction((event)=>{
        this.handlePointClick(event);
      },Cesium.ScreenSpaceEventType.LEFT_CLICK);
    },
    handlePointClick(event){

      if(!this.selectedPointLayer || this.selectedPointAttributes.length ===0){
        return;
      }
 
      const pickedObject = this.viewer.scene.pick(event.position);
      if(!pickedObject)return;


      const item = this.vectorItems[this.selectedPointLayer];
      if(!item) return;

      let clickedPoint = null;

      if(item.pointFeatures && item.pointFeatures.length>0){
        const entity = pickedObject.id || pickedObject.primitive;

        if(entity && entity.position){
          let position;
          if(typeof entity.position.getValue ==='function'){
            position = entity.position.getValue();
          }else{
            position = entity.position;
          }
          
          clickedPoint = item.pointFeatures.find(feature=>{
            const featurePosition = feature.geometry.coordinates;
            
            const cartesian = Cesium.Cartesian3.fromDegrees(featurePosition[0], featurePosition[1]);
            
            return Cesium.Cartesian3.equals(position,cartesian,0.1)
          });
        }
      }else if(item.dataSource && item.dataSource.entities.values.length >0){
          clickedPoint = pickedObject.id
        }
        if(clickedPoint){
          this.clickedPoint = clickedPoint;
          this.updatePointAttributeChart();
 
        }
      },
    updatePointAttributeChart(){
      if(!this.clickedPoint || this.selectedPointAttributes.length === 0)return;
      const item = this.vectorItems[this.selectedPointLayer];
      if(!item){return};
      const chartData=[]

      this.selectedPointAttributes.forEach(attr =>{
        let value = null;

        if(item.pointFeatures && item.pointFeatures.length >0){
          value = parseFloat(this.clickedPoint.properties[attr]);
        }else if(item.dataSource && item.dataSource.entities.values.length > 0){
          if(this.clickedPoint.properties){
            value = parseFloat(this.clickedPoint.properties[attr].getValue());
          }
        }
        if(!isNaN(value)){
          chartData.push({
            value:value,
            attribute:attr
          });
        }
      });
      this.pointAttributeChartData = chartData;
      this.$nextTick(()=>{
        this.renderPointAttributeChart();
      })
    },
    renderPointAttributeLargeChart(){
      if(!this.$refs.largeChart) return;

      const chart = echarts.init(this.$refs.largeChart);

      const option={
        title:{
          text:'单点属性分析',
          left:'center',
        },
        xAxis:{
          type:'category',
          data:this.pointAttributeChartData.map(item => item.attribute),
          axisLabel:{
            fontSize:12,
            rotate:45,
            interval:0,
          }
        },
        yAxis:{
          type:"value",
          axisLabel:{fontSize:12,interval:0},
          axisLine:{show:true},
          axisTick:{show:true}
        },
        series:{
          type:'line',
          data:this.pointAttributeChartData.map(item =>item.value)
        },
        grid:{
          left: 10,    // 增加左边距
          right: 10,   // 增加右边距
          top: 60,
          bottom: 0,
          containLabel: true
        }
        
      };
      chart.setOption(option)
    },
    renderPointAttributeChart(){
      
      if(!this.$refs.pointAttributeChart || this.pointAttributeChartData.length === 0) return;
  
      const chart = echarts.init(this.$refs.pointAttributeChart);
      const option={
        tooltip:{
          trigger:'axis',
          formatter:function(params){
            return `${params[0].name}:${params[0].value}`;
          }
        },
        xAxis:{
          type:'category',
          data:this.pointAttributeChartData.map(item => item.attribute),
          axisLabel:{
            fontSize:10,
            rotate:45,
            interval:0,
          },
        },
        yAxis:{
          type:'value',
          axisLabel:{fontSize:10,interval:0},
        },
        series:[{
          type:'line',
          data:this.pointAttributeChartData.map(item =>item.value),
        }],
        grid:{
          left: 0,    // 增加左边距
          right: 0,   // 增加右边距
          top: 5,
          bottom: 0,
          containLabel: true
        }
        
      };
      chart.setOption(option);
    },

    closePointAnalysisPopover(){
      this.popoverVisible = false;
      if(this.pointClickHandler){
        this.pointClickHandler.destroy();
        this.pointClickHandler = null;
      }
    },



    //测距相关
    toggleMeasureDistance(){
      console.log('toggleMeasureDistance 被调用');
      this.measureDistancePopoverVisible = !this.measureDistancePopoverVisible;
      if(this.measureDistancePopoverVisible){
        this.closeMeasureAreaPopover();
        this.closePopover();
      }
    },
    closeMeasureDistancePopover(){
      this.measureDistancePopoverVisible = false;
      this.stopMeasureDistance();
    },
    startMeasureDistance(){
      this.isMeasuringDistance = true;
      this.distancePoints = [];
      this.distanceResult = null;
      this.clearDistanceEntities();

      //创建测距处理器
      this.distanceHandler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);

      this.distanceHandler.setInputAction((event) =>{
        const pickedPosition = this.viewer.camera.pickEllipsoid(event.position, this.viewer.scene.globe.ellipsoid);
        if(pickedPosition){
          this.addDistancePoint(pickedPosition);
        }
      },Cesium.ScreenSpaceEventType.LEFT_CLICK);

      this.distanceHandler.setInputAction((event)=>{
        if(this.distancePoints.length >= 2){
          this.finishMeasureDistance();
        }
      },Cesium.ScreenSpaceEventType.RIGHT_CLICK);
      this.distanceHandler.setInputAction((event)=>{
        if(this.distancePoints.length > 0){
          this.updateDistancePreview(event.endPosition);
        }
      },Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    },

    addDistancePoint(position){
      this.distancePoints.push(position);

      const pointEntity = this.viewer.entities.add({
        position:position,
        point:{
          pixelSize:8,
          color:Cesium.Color.YELLOW,
          outlineColor:Cesium.Color.BLACK,
          outlineWidth:2
        }
      });
      this.distanceEntities.push(pointEntity);

      if(this.distancePoints.length >1){
        const lineEntity = this.viewer.entities.add({
          polyline:{
            positions:[this.distancePoints[this.distancePoints.length - 2],position],
            width:3,
            material:Cesium.Color.CYAN
          }
        });
        this.distanceEntities.push(lineEntity);
      
      };
    },

    updateDistancePreview(mousePosition){
      if(this.distancePoints.length > 0 ){
        const pickedPosition = this.viewer.camera.pickEllipsoid(mousePosition,this.viewer.scene.globe.ellipsoid);
        if(pickedPosition){
          this.viewer.entities.values.forEach(entity=>{
            if(entity.polyline && entity.polyline.material){
              const materialColor = entity.polyline.material.color ? entity.polyline.material.color.getValue():null;
              if(materialColor && materialColor.equals(Cesium.Color.ORANGE)){
                this.viewer.entities.remove(entity);
              }
            }
          });

          this.viewer.entities.add({
            polyline:{
              positions:[this.distancePoints[this.distancePoints.length-1],pickedPosition],
              width:2,
              material:Cesium.Color.ORANGE,
              dashLength:8
            }
          });
        }
      }
    },
    finishMeasureDistance(){
      this.viewer.entities.values.forEach(entity=>{
        
          if(entity.polyline && entity.polyline.material){
            const materialColor = entity.polyline.material.color ? entity.polyline.material.color.getValue() : null;
            if(materialColor && materialColor.equals(Cesium.Color.ORANGE)){
              this.viewer.entities.remove(entity);
            }
          }
        });

      this.isMeasuringDistance = false;
      if(this.distanceHandler){
        this.distanceHandler.destroy();
        this.distanceHandler = null;
      }

      this.calculateDistance();
    },
    calculateDistance(){
      let totalDistance = 0;
      const segments = [];

      for (let i =1;i<this.distancePoints.length; i++){
        const distance = Cesium.Cartesian3.distance(this.distancePoints[i-1],this.distancePoints[i]);
        totalDistance += distance;
        segments.push({
          distance:(distance / 1000).toFixed(2)+'公里'
        });
      }

      this.distanceResult ={
        totalDistance:(totalDistance / 1000).toFixed(2)+'公里',
        segments:segments
      };
    },
    clearMeasureDistance(){
      this.isMeasuringDistance = false;
      if(this.distanceHandler){
        this.distanceHandler.destroy();
        this.distanceHandler = null;
      }
      this.distancePoints = [];
      this.distanceResult = null;
      this.clearDistanceEntities();
    },
    clearDistanceEntities(){
      this.distanceEntities.forEach(entity=>{
        this.viewer.entities.remove(entity);
      });
      this.distanceEntities = [];

      this.viewer.entities.values.forEach(entity =>{
        if(entity.polyline && (entity.polyline.material === Cesium.Color.CYAN || entity.polyline.material === Cesium.Color.ORANGE)){
          this.viewer.entities.remove(entity);
        }
      });
    },
    stopMeasureDistance(){
      this.isMeasuringDistance = false;
      if(this.distanceHandler){
        this.distanceHandler.destroy();
        this.distanceHandler = null;
      }
    },

    //面积测量相关
    toggleMeasureArea(){
      this.measureAreaPopoverVisible = !this.measureAreaPopoverVisible;
      if(this.measureAreaPopoverVisible){
        this.closeMeasureDistancePopover();
        this.closePopover();
      }
    },

    closeMeasureAreaPopover(){
      this.measureAreaPopoverVisible = false;
      this.stopMeasureArea();
    },

    startMeasureArea(){
      this.isMeasuringArea = true;
      this.areaPoints = [];
      this.areaResult = null;
      this.clearAreaEntities();

      this.areaHandler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);

      this.areaHandler.setInputAction((event)=>{
        const pickedPosition = this.viewer.camera.pickEllipsoid(event.position,this.viewer.scene.globe.ellipsoid);
        if(pickedPosition){
          this.addAreaPoint(pickedPosition);
        }
      },Cesium.ScreenSpaceEventType.LEFT_CLICK);

      this.areaHandler.setInputAction((event)=>{
        if(this.areaPoints.length >= 3){
          this.finishMeasureArea();
        }
      },Cesium.ScreenSpaceEventType.RIGHT_CLICK);

      this.areaHandler.setInputAction((event)=>{
        if(this.areaPoints.length > 0){
          this.updateAreaPreview(event.endPosition);
        }
      },Cesium.ScreenSpaceEventType.MOUSE_MOVE);

    },
    addAreaPoint(position){
      this.areaPoints.push(position);

      const pointEntity = this.viewer.entities.add({
        position:position,
        point:{
          pixelSize:8,
          color:Cesium.Color.GREEN,
          outlineColor:Cesium.Color.BLACK,
          outlineWidth:2
        }
      });
      this.areaEntities.push(pointEntity);

      if(this.areaPoints.length > 1){
        const lineEntity = this.viewer.entities.add({
          polyline:{
            positions:[this.areaPoints[this.areaPoints.length -2],position],
            width:3,
            material:Cesium.Color.LIME
          }
        });
        this.areaEntities.push(lineEntity);
      }
    },
    updateAreaPreview(mousePosition){
      if(this.areaPoints.length >0){
        const pickedPosition = this.viewer.camera.pickEllipsoid(mousePosition,this.viewer.scene.globe.ellipsoid);
        if(pickedPosition){
          this.viewer.entities.values.forEach(entity =>{
            if(entity.polyline && entity.polyline.material){
              const materialColor = entity.polyline.material.color ? entity.polyline.material.color.getValue():null;
              if(materialColor && materialColor.equals(Cesium.Color.ORANGE)){
                this.viewer.entities.remove(entity);
              }

            }
            if(entity.polygon && entity.polygon.material){
              const materialColor = entity.polygon.material.color ? entity.polygon.material.color.getValue():null;
              if(materialColor && materialColor.equals(Cesium.Color.ORANGE.withAlpha(0.3))){
                this.viewer.entities.remove(entity);
              }
              
            }
          });
        
        if(this.areaPoints.length >1){
          this.viewer.entities.add({
            polyline:{
              positions:[this.areaPoints[this.areaPoints.length-1],pickedPosition],
              width:2,
              material:Cesium.Color.ORANGE,
              dashLength:8
            }
          });
        }

        if(this.areaPoints.length >2){
          const previewPositions=[...this.areaPoints,pickedPosition];
          this.viewer.entities.add({
            polygon:{
              hierarchy:previewPositions,
              material:Cesium.Color.ORANGE.withAlpha(0.3),
              outline:true,
              outlineColor:Cesium.Color.ORANGE,
            }
          });
        }
      }
    }
    },
    finishMeasureArea(){
      this.isMeasuringArea = false;
      if(this.areaHandler){
        this.areaHandler.destroy();
        this.areaHandler = null;
      }

      this.calculateArea();

      this.drawFinalAreaPolygon();
    },
    calculateSphericalPolygonArea(positions){
      let area = 0;
      const n = positions.length;

      for (let i=0; i<n ; i++){
        const j = (i+1) % n;
        const p1 = Cesium.Cartographic.fromCartesian(positions[i]);
        const p2 = Cesium.Cartographic.fromCartesian(positions[j]);

        area += (p2.longitude - p1.longitude) * (p2.latitude + p1.latitude);

      }
      area = Math.abs(area) *0.5
      
      const earthRadius = 6371000;
      return area * earthRadius * earthRadius;
    },
    calculateArea(){
      if(this.areaPoints.length < 3) return;

      let perimeter = 0;
      for (let i = 0;i <this.areaPoints.length;i++){
        const nextIndex = (i+1) % this.areaPoints.length;
        const distance = Cesium.Cartesian3.distance(this.areaPoints[i], this.areaPoints[nextIndex]);
        perimeter += distance;
      }

      const area = this.calculateSphericalPolygonArea(this.areaPoints);

      this.areaResult = {
        totalArea:(area/1000000).toFixed(2)+'平方公里',
        perimeter:(perimeter / 1000).toFixed(2)+'公里',
      };
    },

    drawFinalAreaPolygon(){

      const polygonEntity = this.viewer.entities.add({
        polygon:{
          hierarchy:this.areaPoints,
          material:Cesium.Color.GREEN.withAlpha(0.3),
          outline:true,
          outlineColor:Cesium.Color.GREEN,
          outlineWidth:2
        }
      });
      this.areaEntities.push(polygonEntity);
    },

    clearMeasureArea(){
      this.isMeasuringArea = false;
      if(this.areaHandler){
        this.areaHandler.destroy();
        this.areaHandler = null;
      }
      this.areaPoints = [];
      this.areaResult = null;
      this.clearAreaEntities();
    },

    clearAreaEntities(){
      this.areaEntities.forEach(entity=>{
        this.viewer.entities.remove(entity);
      });
      this.areaEntities = [];

      this.viewer.entities.values.forEach(entity=>{
        if(entity.polygon && entity.polygon.material === Cesium.Color.LIME || entity.polygon.material === Cesium.color.ORANGE){
          this.viewer.entities.remove(entity);
        }
        if(entity.polygon && entity.polygon.material === Cesium.Color.ORANGE.withAlpha(0.3)){
          this.viewer.entities.remove(entity);
        }
      })
    },
    stopMeasureArea(){
      this.isMeasureArea = false;
      if(this.areaHandler){
        this.areaHandler.destroy();
        this.areaHandler = null;
      } 

    },
    
  onLegendLayerChange(layerId){
    this.legendSelectedLayer = layerId;

    const item = this.vectorItems[layerId];
    if(item && item.selectedAttribute){
      this.legendSelectedAttribute = item.selectedAttribute;
    }else{
      this.legendSelectedAttribute=''
      if(item && item.pointFeatures && item.pointFeatures.length>0){
        const availableAttributes = Object.keys(item.pointFeatures[0].properties);
        if(availableAttributes.length>0){
          this.legendSelectedAttribute = availableAttributes[0];
        }
      }
    }
    this.updateLegendData();
  },
  onLegendAttributeChange(attribute){
    this.legendSelectedAttribute = attribute;
    this.updateLegendData();

    //同时更新侧边栏中该图层的属性选择
    const item = this.vectorItems[this.legendSelectedLayer];
    if(item){
      item.selectedAttribute = attribute;
    
    if(item.points){
      this.updatePointsColorsDirectly(item)
    }
    if(item.dataSource){
      this.uodateDataSourceColors(item);
    }
    this.updataTreeData();
    }
    this.updataLegendData();
  },
  // 添加一个方法来同步图例选择与侧边栏选择
  syncLegendWithSidebar(){
    if(!this.legendSelectedLayer){
      const item = this.vectorItems[this.legendSelectedLayer];
      if(item && item.selectedAttribute){
        this.legendSelectedAttribute = item.selectedAttribute;
        this.updateLegendData();
      }
    }
  },
  //修改侧边栏属性变化，同步到图例
  handleAttributeChange(id,val){
    const item = this.vectorItems[id];
    if(!item || item.selectedAttribute === val) return;

    item.selectedAttribute = val;
    this.updatePointsColorsDirectly(item);
    
    //如果当前图例显示的就是这个图层，则更新图例
    if(this.legendSelectedLayer === id){
      this.legendSelectedAttribute = val;
      this.updateLegendData();
    }

  },

  updatePointsColorsDirectly(item){
    if(!item.points || !item.selectedAttribute) return;

    const attribute = item.selectedAttribute;
    const colors = this.getColorScheme(item.selectedColorScheme);
    if(!colors || colors.length === 0) return;
  },
  updateLegendData(){
    if(!this.legendSelectedAttribute || !this.legendSelectedLayer){
      this.legendDataRange={min:0,max:0};
      return;
    }
    const item = this.vectorItems[this.legendSelectedLayer]
    if(!item) return;

    let values=[];

    if(item.pointFeatures && item.pointFeatures.length>0){
      values = item.pointFeatures
      .map(feature=>parseFloat(feature.properties[this.legendSelectedAttribute]))
      .filter(v=>!isNaN(v));
    }else if(item.dataSource && item.dataSource.entities.values.length>0){
      values = item.dataSource.entities.values
      .map(entity=>{
        if(entity.properties){
          return parseFloat(entity.properties[this.legendSelectedAttribute].getValue());
        }
        return NaN;
      })
      .filter(v=>!isNaN(v));
    }
    if(values.length>0){
      this.legendDataRange={
        min:Math.min(...values),
        max:Math.max(...values)
      };
    }else{
      this.legendDataRange={
        min:0,
        max:0
      };
    }
  },
  getLayerName(layerId){
    const item = this.vectorItems[layerId];
    return item ? item.name:''
  },
  getLegendColorGradient(){
    if(!this.legendSelectedLayer)return{};

    const item = this.vectorItems[this.legendSelectedLayer];
    if(!item || !item.selectedColorScheme) return{};

    const colors = this.colorScheme[item.selectedColorScheme];
    if(!colors || colors.length === 0)return{};

    if(colors.length ===1){
      return{background:colors[0]}
    }
    return{
      background:`linear-gradient(to right,${colors.join(',')})`
    }
  },
  onLayerChange(layerId){
    this.selectedLayer = layerId;
    this.selectedAttribute='';
    //自行选择第一个属性
    this.$nextTick(()=>{
      if (this.attributeOption.length > 0) {  
      this.selectedAttribute = this.attributeOption[0];
    }
    });
    this.updateSmallChart();
  },
  onAttributeChange(attribute){
    this.selectedAttribute = attribute;
    this.updateSmallChart();
  },
  updateSmallChart() {
    if (!this.selectedAttribute || !this.selectedLayer) return;

    // 避免嵌套的 nextTick
    this.$nextTick(() => {
      this.initSmallChart();
  });
},
  initSmallChart(){
    if(!this.$refs.smallChart) return;

    const chart = echarts.init(this.$refs.smallChart);
        // 强制重新计算尺寸
    this.$nextTick(() => {
      chart.resize();
    });

    if(this.intersectingPoints.length === 0){
      const option={
        title:{textStyle:{ fontSize: 10},left:'center',top:5},
        xAxis:{type:'category',data:[],axisLine:{show:false},axisTick:{show:true},axisLabel:{show:true}},
        yAxis:{type:'value',show:true,axisLine:{show:false},axisTick:{show:true},axisLabel:{show:true}},
        series:[{type:'line',data:[],showSymbol:false}],
        grid:{
          top:30,
          bottom:30,
          left:40,
          right:20,
          contianLabel:true
        }
      };
      chart.setOption(option);
      return;
    }

    const chartData = this.prepareChartData(this.intersectingPoints, this.selectedAttribute);

    const option={
      title:{textStyle:{fontSize:10},left:'center',top:5},
      xAxis:{type:'category',data:chartData.xAxis,show:true,axisLine:{show:true},axisTick:{show:true},axisLabel:{show:true}},
      yAxis:{type:'value',show:true,axisLine:{show:true},axisLabel:{show:true},axisTick:{show:true}},
      tooltip:{trigger:'axis'},
      series:[{type:'line',data:chartData.series,smooth:true,showSymbol:false}],
      grid:{top:30, bottom:30, left:40, right:20,contianLabel:true}
    };
    chart.setOption(option);
  },
  getSelectedItems(){
    return Object.values(this.vectorItems).filter(item => item.visible);
  },
  //准备图表数据
  prepareChartData(intersectingPoints, attribute){
    if(!intersectingPoints || intersectingPoints.length ===0){
      return{xAxis:[],series:[]};
    }

    //按照经度排序（自西向东）
    const sortedPoints = [...intersectingPoints].sort((a,b)=>
    a.geometry.coordinates[0] - b.geometry.coordinates[0]
  );
  const xAxis = [];
  const series = [];

  sortedPoints.forEach((point) => {
    const values = parseFloat(point.properties[attribute]);
    if(!isNaN(values)){
      xAxis.push(point.geometry.coordinates[0].toFixed(4));
      series.push(values);
    }
  });
  return {xAxis,series};
  },
  initLargeChart(){
    if(!this.$refs.largeChart) return;
    

    //如果已有实例，先销毁
    if(this.largeChartInstance){
      this.largeChartInstance.dispose();
    }

    const chart = echarts.init(this.$refs.largeChart);
    this.largeChartInstance = chart;

    if(this.intersectingPoints.length === 0){
      console.log('没有相交点');
      return;
    }

    if(!this.selectedAttribute || !this.selectedLayer){
      console.log('请选择属性和图层');
      return
    }

    const chartData = this.prepareChartData(this.intersectingPoints, this.selectedAttribute);

    const option ={
      title:{
        text:`剖面分析 - ${this.selectedAttribute}`,
        left:'center'
      },
      tooltip:{
        trigger:'axis',
        formatter:function(params){
          const data = params[0];
          return `经度: ${data.name}°<br/>${this.selectedAttribute}: ${data.value}`;

        }.bind(this)
      },
      xAxis:{
        type:'category',
        data:chartData.xAxis,
        name:'经度(°)',
        axisLabel:{
          interval:Math.floor(chartData.xAxis.length / 8),
          maxInterval:12,
          rotate:45,
          fontSize:10
        }
      },
      yAxis:{
        type:'value',
        show:true,
        axisLine:{show:true},
        axisLabel:{show:true},
        axisTick:{show:true},
        // name:this.selectedAttribute
      },
      series:[{
        data:chartData.series,
        type:'line',
        smooth:true,
        name:this.selectedAttribute
      }]
    };
    chart.setOption(option);
  },
  closePopover() {
      this.popoverVisible = false;
    },
  showPointAttributeLargeChart(){
    if(this.pointAttributeChartData.length===0)return;

    this.showDialog = true;
    this.$nextTick(()=>{
      this.renderPointAttributeLargeChart();
    })
  },
  showLargeChart() {
      console.log('显示放大版折线图');
      // 这里可以添加显示大图表的逻辑
      this.showDialog = true;
      this.$nextTick(()=>{
        this.initLargeChart();
      });
    },
    showProfileAnalysis(){
      this.popoverVisible = true;
    },
  //绘制折线
    drawLine(){
      
      if(this.isDrawingLine) return;

      this.isDrawingLine = true;
      
      this.drawLinePoints = [];

      if(this.tempLine){
        this.viewer.entities.remove(this.tempLine);
      };

      //创建临时实体线
      this.tempLine = this.viewer.entities.add({
        polyline:{
          positions:new Cesium.CallbackProperty(()=>this.drawLinePoints,false),
          width:3,
          material:new Cesium.Color.fromCssColorString('#ff0000'),
          clampToGround:true,
        }
      });

      //绘制图
      this.drawHandler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);

      this.drawHandler.setInputAction(click => {
        const ray = this.viewer.camera.getPickRay(click.position);
        const position = this.viewer.scene.globe.pick(ray, this.viewer.scene);

        if(position && this.isValidCartesian(position)){
          this.drawLinePoints.push(Cesium.Cartesian3.clone(position));
        }else{
          console.warn('Invalid point position', position)
        }
      },Cesium.ScreenSpaceEventType.LEFT_CLICK);

      //鼠标移动
      this.drawHandler.setInputAction(move => {
        if(this.drawLinePoints.length > 0){
          const ray = this.viewer.camera.getPickRay(move.endPosition);
          const position = this.viewer.scene.globe.pick(ray, this.viewer.scene);

          if(position && this.isValidCartesian(position)){
            // 直接更新最后一个点
          const lastIndex = this.drawLinePoints.length - 1;
          this.drawLinePoints[lastIndex] = Cesium.Cartesian3.clone(position);
        }
      }
      },Cesium.ScreenSpaceEventType.MOUSE_MOVE);

      //右键结束绘制
      this.drawHandler.setInputAction(()=>{
        this.finalizeLine();
      },Cesium.ScreenSpaceEventType.RIGHT_CLICK);
      
    },

    finalizeLine(){
      if(!this.isDrawingLine || this.drawLinePoints.length < 2) return;

      const validPoints = this.drawLinePoints.filter(point =>this.isValidCartesian(point));

      if(validPoints.length <2){
        console.error('Not enough valid points to create a line');
      this.cleanupDrawing();
      return;
      }

      //创建最终实体线
      const line = this.viewer.entities.add({
        polyline:{
          positions:this.drawLinePoints,
          width:4,
          material:new Cesium.Color.fromCssColorString('#ff0000'),
          clampToGround:true,
        }
      });
      this.drawlines.push(line);
      
  
      const items = this.getItems();
      const pointFeatureWithDistance = this.getIntersectingPoints(validPoints, items);
      
      this.intersectingPoints=pointFeatureWithDistance;
      this.cleanupDrawing();
    },
getIntersectingPoints(linePositions, items){
      const result = [];
  const minDistance = 0.001; // 经纬度阈值（约10米）

  // 1. 将线段点转为经纬度
  const linePositionsCartographic = linePositions.map(pos => 
    Cesium.Cartographic.fromCartesian(pos)
  );

  // 2. 预处理线段（经纬度表示）
  const segments = [];
  for (let i = 0; i < linePositionsCartographic.length - 1; i++) {
    const start = linePositionsCartographic[i];
    const end = linePositionsCartographic[i + 1];

    segments.push({
      startLon: Cesium.Math.toDegrees(start.longitude),
      startLat: Cesium.Math.toDegrees(start.latitude),
      deltaLon: Cesium.Math.toDegrees(end.longitude - start.longitude),
      deltaLat: Cesium.Math.toDegrees(end.latitude - start.latitude),
      lengthSquared: Math.pow(Cesium.Math.toDegrees(end.longitude) - Cesium.Math.toDegrees(start.longitude), 2) + 
                    Math.pow(Cesium.Math.toDegrees(end.latitude) - Cesium.Math.toDegrees(start.latitude), 2)
    });
  }

  // 3. 计算点到线段的距离
  Object.keys(items).forEach(key => {
    const item = items[key];

    item.pointFeatures.forEach(feature => {
      const [lon, lat] = feature.geometry.coordinates;
      
      let minDist = Infinity;
      
      segments.forEach(segment => {
        // 向量AP（点到线段起点）
        const deltaLonP = lon - segment.startLon;
        const deltaLatP = lat - segment.startLat;
        
        // 计算投影比例t
        let t = 0;
        if (segment.lengthSquared > 0) {
          t = (deltaLonP * segment.deltaLon + deltaLatP * segment.deltaLat) / 
              segment.lengthSquared;
          t = Math.max(0, Math.min(1, t));
        }
        
        // 计算最近点
        const closestLon = segment.startLon + t * segment.deltaLon;
        const closestLat = segment.startLat + t * segment.deltaLat;
        // 计算距离（经纬度差值）
        const dLon = lon - closestLon;
        const dLat = lat - closestLat;
        const distance = Math.sqrt(dLon*dLon + dLat*dLat);
        
        minDist = Math.min(minDist, distance);
      });
      
      if (minDist < minDistance) {
        result.push({ ...feature});
      }
    });
  });
  
  return result;
},
isValidCartesian(cartesian) {
  return cartesian &&
    !isNaN(cartesian.x) && 
    !isNaN(cartesian.y) && 
    !isNaN(cartesian.z) &&
    isFinite(cartesian.x) &&
    isFinite(cartesian.y) &&
    isFinite(cartesian.z);
},
    computePointToPolylineDistance(point, polylinePositions){

      for (let i =0;i<polylinePositions.length-1;i++){
        const segmentStart = polylinePositions[i];
        const segmentEnd = polylinePositions[i+1];

        const distance = computePointToLineSegmentDistance(point, segmentStart, segmentEnd);

        if(distance < minDistance){

        };
      }
    },
    getItems(){
      const visibleItems={};
      Object.keys(this.vectorItems).forEach(key=>{
        const item = this.vectorItems[key];
        if (item && item.visible){
          visibleItems[key] = item;
        }
      });
      return visibleItems
    },

    cleanupDrawing(){
      if (this.drawHandler){
        this.drawHandler.destroy();
        this.drawHandler = null;
      }

      if(this.tempLine){
        this.viewer.entities.remove(this.tempLine);
        this.tempLine = null;
      }

      this.drawLinePoints = [];
      this.isDrawingLine = false;
    },

    cleardraw(){
      this.drawlines.forEach(line => this.viewer.entities.remove(line));
      this.drawlines = [];
      if(this.isDrawingLine){
        this.cleanupDrawing();
      }
      this.intersectingPoints=[];
      this.updateSmallChart();
    },

    //切换侧边栏
    toggleSidebar(){
      this.showSidebar = !this.showSidebar;
    },

    // 切换到影像地图
    switchToImagery() {
      this.viewer.imageryLayers.removeAll();
      this.viewer.imageryLayers.addImageryProvider(
        Cesium.Ion.defaultImageryProvider
      );
    },

    // 切换到矢量地图
    switchToVector() {
      this.viewer.imageryLayers.removeAll();
      this.viewer.imageryLayers.addImageryProvider(
        new Cesium.OpenStreetMapImageryProvider()
      );
    },

    beforeUpload(file) {
      //获取文件后缀
      const validExtensions = ['zip'];
      const fileExt = file.name.split('.').pop().toLowerCase();
      if (!validExtensions.includes(fileExt)) {
        this.$message.error('请上传zip文件');
        return false;
      }
      console.log('upload')
      return true;
    },

    // 加载矢量数据
    async loadVectorData(geoJSON, name) {
      try {
        // const response = await fetch(url);
        // const geoJSON = await response.json();
        const id = Date.now().toString();

        const vectorItem = {
          id,
          name,
          // color:`#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`,
          points:null,
          dataSource:null,
          visible: true,
          pointFeatures:[],//存储点数据的属性和坐标
          selectedAttribute: '',
          selectedColorScheme: '纯白色',
          color: '#ffffff' // 添加颜色
        };
        //新加入
        // 确保 geoJSON 是有效的 FeatureCollection
        if (!geoJSON || !geoJSON.features || !Array.isArray(geoJSON.features)) {
          throw new Error("Invalid GeoJSON format");
        }
        
        const pointFeatures = geoJSON.features.filter(
          feature => feature.geometry && feature.geometry.type === 'Point'
        );

        const otherFeatures = geoJSON.features.filter(
          feature => feature.geometry && feature.geometry.type !=='Point'
        );


        // 处理点数据
        if (pointFeatures.length > 0){
          vectorItem.points = this.viewer.scene.primitives.add(
            new Cesium.PointPrimitiveCollection()
          );
          vectorItem.pointFeatures = pointFeatures
          this.addPoints(vectorItem.points, pointFeatures)
          
          //为点数据添加点击事件
          // const handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
          // handler.setInputAction((movement) => {
          //   const pickedObject = this.viewer.scene.pick(movement.position);
          //   if (pickedObject && pickedObject.primitive){
          //       const position = pickedObject.primitive.position;
          //       const cartographic = Cesium.Cartographic.fromCartesian(position);
          //       const lon = Cesium.Math.toDegrees(cartographic.longitude);
          //       const lat = Cesium.Math.toDegrees(cartographic.latitude);

          //       const clickedFeature = pointFeatures.find(feature =>{
          //         const [featureLon, featureLat] = feature.geometry.coordinates;
          //         return Math.abs(featureLon - lon) < 0.0001 && Math.abs(featureLat - lat)<0.0001;
          //       });
          //       if (clickedFeature && clickedFeature.properties){
          //         this.currentAttributes = clickedFeature.properties;
          //         this.attributeColumns = Object.keys(this.currentAttributes).map(key => ({
          //           prop:key,
          //           label: key
          //         }));
          //         this.attributeDialogVisible = true;
          //       }
          //   }
          // },Cesium.ScreenSpaceEventType.LEFT_CLICK);

          // 计算点数据的经纬度范围
          let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
          pointFeatures.forEach(feature => {
            const [lon, lat] = feature.geometry.coordinates;
            minLon = Math.min(minLon, lon);
            minLat = Math.min(minLat, lat);
            maxLon = Math.max(maxLon, lon);
            maxLat = Math.max(maxLat, lat);
          });

          // 处理单点数据：扩展为固定范围（如±0.1度）
          if (pointFeatures.length === 1) {
            minLon -= 0.1; maxLon += 0.1;
            minLat -= 0.1; maxLat += 0.1;
          }

          // 飞向矩形区域
          await this.viewer.camera.flyTo({
            destination: Cesium.Rectangle.fromDegrees(minLon, minLat, maxLon, maxLat),
            orientation: {
              heading: 0,
              pitch: -Cesium.Math.PI_OVER_TWO, // 俯视视角
              roll: 0
            }
          });
        }
        //渲染面和线
        if (otherFeatures.length > 0){
          vectorItem.dataSource = await Cesium.GeoJsonDataSource.load({
            type: "FeatureCollection",
            features: otherFeatures
          });
            // 应用动态颜色
          this.updateDataSourceColors(vectorItem);
          this.viewer.dataSources.add(vectorItem.dataSource);

                // 监听屏幕点击事件
      const handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
      handler.setInputAction((movement) => {
        const pickedObject = this.viewer.scene.pick(movement.position);
        if (pickedObject && pickedObject.id) {
          const entity = pickedObject.id;
          if (entity.properties) {
            this.currentAttributes = entity.properties.getValue();
            this.attributeColumns = Object.keys(this.currentAttributes).map(key => ({
              prop: key,
              label: key
            }));
            this.attributeDialogVisible = true;
          }
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

          await this.viewer.flyTo(vectorItem.dataSource)
        }
      
      //保存引用并更新树数据
      this.$set(this.vectorItems, id, vectorItem);
      console.log('Added vectorItem:', id, vectorItem);
      console.log('Current vectorItems:', this.vectorItems);

      this.updateTreeData();
      
      // 强制触发响应式更新
      this.$forceUpdate();
      
      // 如果还没有选择图层，自动选择第一个
      if (!this.selectedLayer && Object.keys(this.vectorItems).length > 0) {
        const firstLayerId = Object.keys(this.vectorItems)[0];
        console.log('Auto selecting first layer:', firstLayerId);
        setTimeout(() => {
          this.onLayerChange(firstLayerId);
        }, 0);
      }

      } catch (e) {
        console.error("加载矢量数据失败:", e);
      }
    },
    addPoints(points, features){
      // const cesiumColor = Cesium.Color.fromCssColorString(color)
      features.forEach(feature => {
        points.add({
          position: Cesium.Cartesian3.fromDegrees(
            feature.geometry.coordinates[0],
            feature.geometry.coordinates[1]
          ),
          // color: cesiumColor,
          pixelSize: 5
        });
      });
    },

    //设置数量数据样式
    setDataSourceStyle(dataSource, color){
      const cesiumColor = Cesium.Color.fromCssColorString(color);
      dataSource.entities.values.forEach(entity =>{
        if(entity.polygon){
          entity.polygon.material = cesiumColor;
        }
        if (entity.polyline){
          entity.polyline.material = cesiumColor;
        }
      });
    },

    //更新数据
    updateTreeData(){
      // console.log(this.vectorItems)
      this.vectorTreeData = Object.values(this.vectorItems).map(item =>{
        if(!item.selectedAttribute){
          if(item.pointFeatures.length>0){
            item.selectedAttribute = Object.keys(item.pointFeatures[0].properties)[0];
          }else if (item.dataSource && item.dataSource.entities.values.length > 0){
            const firstEntity = item.dataSource.entities.values[0];
            if(firstEntity.properties){
              item.selectedAttribute = Object.keys(firstEntity.properties.getValue())[0];

            }
          }
        }
        if(!item.selectedColorScheme){
          item.selectedColorScheme = 'red-yellow-green';
        }
        return {
        id:item.id,
        label: item.name,
        name:item.name,
        selectedAttribute:item.selectedAttribute,
        selectedColorScheme:item.selectedColorScheme,
        children:[
        {
            id: `${item.id}-color`,
            type: 'color-preview',
            colorScheme: item.selectedColorScheme,
            parentData:item
          },
          {
            id: `${item.id}-attribute`,
            label: `${item.selectedAttribute || ''}`,
            type: 'attribute-preview',
            parentData:item
          }
        ],
        expanded: true
        };
      });

      // 默认勾选所有节点
      this.defaultCheckedKeys = this.vectorTreeData.map(node => node.id);
    },

    //处理勾选变化
    handleCheckChange(data, checked){
      const item = this.vectorItems[data.id];
      if (item){
        item.visible = checked;
        this.toggleVectorVisibility(item);
      }
    },

    //切换矢量可视化
    toggleVectorVisibility(item){
      if(item.points){
        item.points.show = item.visible;
        // 确保每个点都同步显隐状态
      item.points._pointPrimitives.forEach(point => {
        point.show = item.visible;
      });
      }
      if(item.dataSource){
        item.dataSource.show = item.visible;
      }
      this.viewer.scene.requestRender(); // 关键：强制渲染
    },

    //更新矢量颜色
    updataVectorColor(data){
      const item = this.vectorItems[data.id];
      if(item){
        item.color = data.color;
        if (item.points){
          this.updatePointsColor(item.points, data.color);
        }
        if(item.dataSource){
          this.setDataSourceStyle(item.dataSource, data.color);
        }
      }
    },
    //更新点颜色
    updatePointsColor(points, color){
      const cesium = Cesium.Color.fromCssColorString(color);
      points._pointPrimitives.forEach(point =>{
        point.color = cesiumColor;
      });
    },

    //清空数据
    clearData() {
          // 清空通过 loadTiffImage 加载的影像图层（保留底图）
          const imageryLayers = this.viewer.imageryLayers;
          for (let i = imageryLayers.length - 1; i >= 0; i--) {
              const layer = imageryLayers.get(i);
              // 检查是否为 SingleTileImageryProvider（通过 loadTiffImage 添加的图层）
              if (layer.imageryProvider instanceof Cesium.SingleTileImageryProvider) {
              imageryLayers.remove(layer);
              }
            }


        this.viewer.dataSources.removeAll();

        const primitives = this.viewer.scene.primitives
        for (let i = primitives.length -1 ; i>=0; i--){
          if (primitives.get(i) instanceof Cesium.PointPrimitiveCollection){
            primitives.remove(primitives.get(i))
          }
        }

        //情况tree
        this.vectorTreeData = [];
        this.vectorItems = {};
        this.defaultCheckedKeys = [];
    },
        // 加载 TIF 影像
    async loadTiffImage(imageData) {
      try {
        // const response = await fetch(url);
        // const data = await response.json();
        // const imageUrl = data.image;
        console.log(imageData)
        if (!imageData || !imageData.image || !imageData.bounds){
          throw new Error ('无效的影像数据格式')
        }

        const {image, bounds} = imageData;
        const { minLon, minLat, maxLon, maxLat} = bounds

        // 创建图片图层
        const imageryProvider = new Cesium.SingleTileImageryProvider({
          url: image,
          rectangle: Cesium.Rectangle.fromDegrees(minLon, minLat, maxLon, maxLat),
        });

        this.viewer.imageryLayers.addImageryProvider(imageryProvider);
        await this.viewer.camera.flyTo({
          destination: Cesium.Rectangle.fromDegrees(minLon,minLat,maxLon,maxLat),
          orientation:{
            heading: 0,
            pitch: -Cesium.Math.PI_OVER_TWO,
            roll: 0,
          }
        })
      } catch (e) {
        console.error("加载失败:", e);
      }
    },

    async handleSuccess(response) {

      //根据文件扩展名调用对应的方法
      if (response.tiffImages){
        for (const imageUrl of response.tiffImages){
            await this.loadTiffImage(imageUrl);
        }
      }
      if (response.vectorData){
        for (let i=0; i<response.vectorData.length;i++){
          const geoJsonUrl = response.vectorData[i];
          const name = response.name[i];
          console.log(name);
          await this.loadVectorData(geoJsonUrl,name);
        }
      }
    },
    

    handleNodeClick(data, node){
      // 如果是色带或属性预览子节点，则触发对话框
      if (data.type === 'color-preview' || data.type === 'attribute-preview') {
        this.showEditDialog(data.parentData); // 传递父节点数据
        } else {
    // 默认行为（如展开/折叠）
        node.expanded = !node.expanded;
        }
    },

    updateColorForNode(parentNode, color){
      const id = parentNode.data.id.split('-')[0];
      const item = this.vectorItems[id];
      if (item){
        item.color = color;
        parentNode.data.color = color;
        // console.log(parentNode)
        this.updataVectorColor(item);
      }
    },

    getColorScale(minvalue, maxvalue){
      const colors = this.colorScheme[this.selectedColorScheme];
      return(value) =>{
        const ratio = (value - minvalue) / (maxvalue - minvalue);
        if(colors.length === 2){
          return Cesium.Color.fromCssColorString(colors[0]).lerp(
            Cesium.Color.fromCssColorString(colors[1]),
            ratio
          );
        }else{
          if(ratio <= 0.5){
            return Cesium.Color.fromCssColorString(colors[0]).lerp(
              Cesium.Color.fromCssColorString(colors[1]),
              ratio * 2
            );
          } else{
            return Cesium.Color.fromCssColorString(colors[1]).lerp(
              Cesium.Color.fromCssColorString(colors[2]),
              (ratio - 0.5) * 2
            );
          }
        }
      };
    },

    //切换色带
    changeColorScheme(Scheme){
      this.selectedColorScheme = Scheme;
      this.updatePointsColors();
    },


    handleAttributeChange(id, val) {
      
      const item = this.vectorItems[id];
  if (!item || item.selectedAttribute === val) return; // 无变化时退出

  // 手动更新 selectedAttribute，避免触发 v-model
  item.selectedAttribute = val;
  this.updatePointsColorsDirectly(item);
},
    //更新单个数据集的属性字段
    updateVectorItemAttribute(id, attribute){
      console.log('222')
      const item = this.vectorItems[id];
      if(item){
        item.selectedAttribute = attribute;
        this.updatePointsColorsDirectly(item);
      }
    },

    //更新单个数据集的色带
    updateVectorItemColorScheme(id, Scheme) {
      const item = this.vectorItems[id];
      if (item){
        item.selectedColorScheme = Scheme;
        this.updatePointsColorsDirectly(item);
      }
    },

    //获取当前数据集的可用属性字段
getAvailableAttributes(id){
  const item = this.vectorItems[id];
  if (!item) return [];
  
  // 优先使用点数据的属性
  if (item.pointFeatures.length > 0) {
    return Object.keys(item.pointFeatures[0].properties);
  }
  
  // 如果没有点数据，使用线面数据的属性
  if (item.dataSource && item.dataSource.entities.values.length > 0) {
    const firstEntity = item.dataSource.entities.values[0];
    if (firstEntity.properties) {
      return Object.keys(firstEntity.properties.getValue());
    }
  }
  
  return [];
    },

  updatePointsColorsDirectly(vectorItem) {
  if (!vectorItem.points) return;
  

  vectorItem.points.removeAll();
  const values = vectorItem.pointFeatures
    .map(feature => parseFloat(feature.properties[vectorItem.selectedAttribute]))
    .filter(v => !isNaN(v));

  if (values.length === 0) return;  // 无有效数据时退出
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const colorScale = this.getColorScale(minValue, maxValue, vectorItem.selectedColorScheme);

  vectorItem.pointFeatures.forEach(feature => {
    const value = parseFloat(feature.properties[vectorItem.selectedAttribute]);
    const color = isNaN(value) ? Cesium.Color.WHITE : colorScale(value);
    vectorItem.points.add({
      position: Cesium.Cartesian3.fromDegrees(...feature.geometry.coordinates),
      color,
      pixelSize: 5
    });
  });
},

    //修改颜色插值函数
    getColorScale(minValue, maxValue, scheme) {
      const colors = this.colorScheme[scheme];
      if (!colors || colors.length === 0) {
        console.error("Invalid color scheme or insufficient colors:", scheme);
        return () => Cesium.Color.WHITE;
      }


      //如果时纯色
      if(colors.length === 1){
        const singleColor = Cesium.Color.fromCssColorString(colors[0]);
        return ()=> singleColor;
      }
  return (value) => {
    const ratio = (value - minValue) / (maxValue - minValue);
    const result = new Cesium.Color();

    // 处理2色渐变
    if (colors.length === 2) {
      const color1 = Cesium.Color.fromCssColorString(colors[0]);
      const color2 = Cesium.Color.fromCssColorString(colors[1]);
      return Cesium.Color.lerp(color1, color2, ratio, result);
    }

    // 处理多色渐变（分段插值）
    const segment = 1 / (colors.length - 1);
    const segmentIndex = Math.min(
      Math.floor(ratio / segment),
      colors.length - 2
    );
    const segmentRatio = (ratio - segmentIndex * segment) / segment;

    const color1 = Cesium.Color.fromCssColorString(colors[segmentIndex]);
    const color2 = Cesium.Color.fromCssColorString(colors[segmentIndex + 1]);
    return Cesium.Color.lerp(color1, color2, segmentRatio, result);
  };
  },

  //显示编辑对话框
  showEditDialog(nodeData){
    this.editingData={
      id:nodeData.id,
      selectedAttribute:nodeData.selectedAttribute,
      selectedColorScheme:nodeData.selectedColorScheme
    };
    this.editDialogVisible = true;
  },

  //确定修改
  confirmEdit(){
    const item = this.vectorItems[this.editingData.id];
    if(item){
      item.selectedAttribute = this.editingData.selectedAttribute;
      item.selectedColorScheme = this.editingData.selectedColorScheme;

      
      if(item.points){
        this.updatePointsColorsDirectly(item);
      }
      if(item.dataSource){
        this.updateDataSourceColors(item);
      }

      this.updateTreeData();

      //如果当前图例显示的是这个图层，则同步更新图例
      if(this.legendSelectedLayer === this.editingData.id){
        this.legendSelectedAttribute = this.editingData.selectedAttribute;
        this.updateLegendData();
      }

          //如果当前折线图显示的是这个图层，则更新图例
    if(this.selectedLayer === this.editingData.id){
      this.selectedAttribute = this.editingData.selectedAttribute;
      this.updateSmallChart();
    }
    }
    this.editDialogVisible = false;
  },

  //获取色带预览
  getPreviewStyle(schemeName){
    const colors = this.colorScheme[schemeName] || ['#ccc'];

    if(colors.length === 1){
      return{
        background: colors[0]
      };
    }
    return{
      background:colors.length > 1
      ? `linear-gradient(to right, ${colors.join(',')})`
      : colors[0]
    };
  },

  updateDataSourceColors(vectorItem) {
  if (!vectorItem.dataSource || !vectorItem.selectedAttribute) return;
  
  const entities = vectorItem.dataSource.entities.values;
  const values = [];
  
  // 收集所有实体的属性值
  entities.forEach(entity => {
    if (entity.properties) {
      const value = parseFloat(entity.properties[vectorItem.selectedAttribute].getValue());
      if (!isNaN(value)) {
        values.push(value);
      }
    }
  });
  
  if (values.length === 0) return;
  
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const colorScale = this.getColorScale(minValue, maxValue, vectorItem.selectedColorScheme);
  
  // 为每个实体设置颜色
  entities.forEach(entity => {
    if (entity.properties) {
      const value = parseFloat(entity.properties[vectorItem.selectedAttribute].getValue());
      const color = isNaN(value) ? Cesium.Color.WHITE : colorScale(value);
      
      if (entity.polygon) {
        entity.polygon.material = color;
      }
      if (entity.polyline) {
        entity.polyline.material = color;
      }
    }
  });
},
  },
beforeDestroy(){
  if(this.drawHandler){
    this.drawHandler.destroy();
  }
  if(this.largeChartInstance){
    this.largeChartInstance.dispose();
    this.largeChartInstance = null;
  }
  if(this.dialogResizeObserver){
    this.dialogResizeObserver.disconnect();
    this.dialogResizeObserver = null;
  }
}
};



</script>

<style lang="less" scoped>
  .color-preview-block {
    display: inline-block;
    width: 60px;
    height: 16px;
    margin-left: 10px;
    border: 1px solid #ddd;
    vertical-align: middle;
  }
.color-sheme-preview{
  display: inline-block;
  width: 60px;
  height: 16px;
  margin-left: 10px;
  border: 1px solid #ddd;
  vertical-align: middle;
}

.attribute-preview {
  padding: 5px 10px;
  background:#f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  margin: 5px 0;
  font-size: 12px;
}

.color-sheme-preview:hover,
.attribute-preview:hover{
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

//对话框中的预览
.dialog-preview {
  height: 30px;
  width: 100%;
  margin-top: 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.tree-node{
  display: flex;
  flex-direction: column;
}

#cesiumContainer {
  display: flex;
  width: 100%;
  height: calc(100vh - 10px);
  border-radius: 8px;
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
  position: relative;
}

.map-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  margin-top: 7vh;
  background: black;
}

/* 侧边栏样式 */
.sidebar {
  padding-top: 15px;
  width: 300px;
  height: 100%;
  background: rgba(30, 30, 30, 0.8);
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}


/* 按钮和侧边栏的容器 */
.controls-sidebar-container {
  display: flex;
  align-items: flex-start; /* 顶部对齐 */
  z-index: 10; /* 确保按钮和侧边栏在地图上方 */
  background: transparent !important;
  // position: absolute;
}

/* 控制按钮样式 */
.map-controls {
  display: flex;
  flex-direction: column; /* 垂直排列 */
  gap: 10px; /* 按钮间距 */
  padding: 10px;
  background: transparent; /* 半透明背景 */
  border-radius: 4px;
  margin-right: 5px; /* 与侧边栏的间距 */
  
}

.map-controls .el-button {
  margin: 10px;
  padding: 10px;
  border: 1px solid #ccc;
  background: rgba(15, 15, 15, 0.8);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  border-radius: 4px;
}
/* 悬停效果 */
.map-controls .el-button:hover {
  background: rgba(255, 255, 255, 1);
  i{
    color: black ;
  }
}

/deep/ .el-tree{
  background: rgba(30, 30, 30, 0.8);

    // 禁用点击背景色变化
    .el-tree-node:focus > .el-tree-node__content {
      background: rgba(30, 30, 30, 0.8);
  }

}

/deep/ .el-tree-node__content:hover{
  background: transparent !important;
  // color: #ffffff !important;
  cursor: default;
}

/deep/ .el-tree-node__children{

  //隐藏复选框
  .el-checkbox{
    display: none;
  }

  //调整节点内容的左边距
  .el-tree-node__content{
    padding-left: 25px !important;
  }
}

/deep/ .el-color-picker {
  // 移除白色边框
  .el-color-picker__trigger {
    border: none !important;
  }
}
.tree-node{
  display: flex;
  align-items: center;
  gap: 10px;
  .el-select{
    width: 100px;
  }
}
.toolbar-buttons{
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin: 5px;
}
.toolbar-buttons .el-button{
  margin: 10px;
  padding: 10px;
  border: 1px solid rgba(15, 15, 15, 0.8);
  background: #ccc;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  border-radius: 4px;
}
.popover-content{
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.small-chart{
  width: 100%;
  height: 120px;
  cursor: pointer;
  margin-top: 15px;
}
.attribute-select-container{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.attribute-label{
  flex-shrink: 0;
}
.popover-refresh{
  position: static;
  border: transparent;
}
.popover-edit{
  position: static;
  border: transparent;
}
.popover-close{
  position:static;

  border: transparent;
}
.custom-popover{
  pointer-events:auto !important
}
.popover-controls{
  position: absolute;
  top: 5px;
  right: 5px;
  display: flex;
  gap:5px;
  z-index: 10;
}
.legend-popover-content{
  padding: 10px;
}
.legend-selector{
  margin-bottom: 20px;
}
.legend-selector{
  margin-bottom: 20px;
}
.legend-selector h4{
  margin-bottom: 15px;
  color: #333;
  font-size: 16px;

}
.legend-display{
  border-top: 1px solid #eee;
  padding-top: 15px;
}
.legend-info{
  margin-bottom: 15px;
}
.legend-info p{
  margin: 5px 0;
  font-size: 12px;
  line-height: 1.4;
}
.color-scheme-preview {
  margin-top: 10px;
}
.color-scheme-preview h5 {
  margin-bottom: 8px;
  color: #333;
  font-size: 14px;
}
.color-gradient {
  height: 25px;
  border-radius: 4px;
  border: 1px solid #ddd;
  margin-bottom: 6px;
}
.color-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #666;
}
.measure-popover-content{
  padding: 0px;
}
.measure-controls{
  display: flex;
  gap: 8px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}
.measure-result{
  background-color: #f5f5f5;
  padding:10px;
  border-radius: 4px;
  margin-top: 10px;
}
.measure-result p{
  margin: 5px 0;
}
.measure-result ul {
  margin: 5px 0;
  padding-left: 20px;
}

.measure-instruction {
  color: #909399;
  font-size: 12px;
  text-align: center;
  margin-top: 20px;
}
.large-chart-container {
  height: 400px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
.el-dialog .large-chart-container {
  height: 450px;
  width: 100%;
}
.single-point-analysis{
  margin-top: 25px;
}
.single-point-controls{
  right: 5px !important;
  left: auto !important;
  top: -8px !important; 
}
</style>