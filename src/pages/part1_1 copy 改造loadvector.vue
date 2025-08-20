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
          <!-- <el-button type="primary" style="color: black;">上传数据</el-button> -->
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
  </div>
</template>

<script>
/* eslint-disable */
import { GeoJsonDataSource, objectToQuery } from "cesium";
import Color from "cesium/Source/Core/Color";
import CheckerboardMaterialProperty from "cesium/Source/DataSources/CheckerboardMaterialProperty";
import Cesium3DTile from "cesium/Source/Scene/Cesium3DTile";
import { pitch } from "file-loader";
import { point } from "leaflet";
import { head } from "shelljs";
import { expand } from "shelljs/src/common";
import 'element-ui/lib/theme-chalk/icon.css'
import { LabelsLayer } from "@amap/amap-vue";
import { values } from "shelljs/commands";
import { Loading } from "element-ui";
export default {
  data() {
    return {

      //增加动态加载相关状态
      LoadingTiles: false,
      currentZoom: 10,
      currentBounds: null,
      titleLayers: {},
      throttledLoad: null,
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
  },
  methods: {
    //新增动态加载方法
    async loadDataByView(){
      if (!this.currentBounds || this.LoadingTiles) return;

      this.LoadingTiles = true

      try{
        const { west, south, east, north} = this.currentBounds
        const zoom = Math.floor(this.viewer.camera.positionCartographic.height / 1000);

        //只处理矢量数据
        const vectorPromises = Object.values(this.vectorItems)
          .filter(item => item.visible)
          .map(async item => {
            const response = await fetch(
              `http://localhost:5000/vector-tiles?` +
              `minLon=${Cesium.Math.toDegrees(west)}&minLat=${Cesium.Math.toDegrees(south)}&maxLon=${Cesium.Math.toDegrees(east)}&maxLat=${Cesium.Math.toDegrees(north)}` +
              `&zoom=${zoom}&layer=${item.name}`
            );
            const geojson = await response.json();

            //清除旧瓦片
            if (this.titleLayers[item.id]){
              this.viewer.dataSources.remove(this.titleLayers[item.id]);
            }

            //加载数据
            const dataSource = await Cesium.GeoJsonDataSource.load(geojson);
            this.titleLayers[item.id] = dataSource

            //应用样式
            if(item.pointFeatures.length > 0){
              this.updatePointsColorsDirectly(item);
            } else{
              this.updateDataSourceColors(item);
            }

            this.viewer.dataSources.add(dataSource)
          });

          await Promise.all(vectorPromises);
      } catch(e){
        console.error('动态加载失败：',e)
      } finally{
        this.LoadingTiles=false;
      }
    },
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
      
      //添加相机移动监听
      this.viewer.camera.moveEnd.addEventListener(() => {
        this.currentZoom = this.viewer.camera.positionCartographic.height;
        this.currentBounds = this.viewer.camera.computeViewRectangle();
        // this.loadDataByView();
      });

      //节流处理
      // this.throttledLoad = Cesium.throttle(this.loadDataByView, 1000);
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
          color: '#ffffff', // 添加颜色
          isDynamic:geoJSON.features.length > 10000,// 超过一万条自动启动动态加载
          currentPage:0,  // 新增：当前页码
          pageSize:2000,  // 新增：每页大小
          isLoading:false,// 新增：加载状态
          isPaused:false,// 新增：暂停状态
          handler:null,// 新增：事件处理器
          bounds:null// 新增：当前视图范围
        };

        //动态加载处理
        if (vectorItem.isDynamic){
          //仅加载初始视图数据
          const initBounds = this.viewer.camera.computeViewRectangle();
          const response = await fetch(
            `http://localhost:5000/vector-tiles?` +
            `minLon=${Cesium.Math.toDegrees(initBounds.west)}&minLat=${Cesium.Math.toDegrees(initBounds.south)}` +
            `&maxLon=${Cesium.Math.toDegrees(initBounds.east)}&maxLat=${Cesium.Math.toDegrees(initBounds.north)}` +
            `&zoom=10&layer=${vectorItem.name}`
          );

          geoJSON = await response.json();
          
        }

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
          const handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
          handler.setInputAction((movement) => {
            const pickedObject = this.viewer.scene.pick(movement.position);
            if (pickedObject && pickedObject.primitive){
                const position = pickedObject.primitive.position;
                const cartographic = Cesium.Cartographic.fromCartesian(position);
                const lon = Cesium.Math.toDegrees(cartographic.longitude);
                const lat = Cesium.Math.toDegrees(cartographic.latitude);

                const clickedFeature = pointFeatures.find(feature =>{
                  const [featureLon, featureLat] = feature.geometry.coordinates;
                  return Math.abs(featureLon - lon) < 0.0001 && Math.abs(featureLat - lat)<0.0001;
                });
                if (clickedFeature && clickedFeature.properties){
                  this.currentAttributes = clickedFeature.properties;
                  this.attributeColumns = Object.keys(this.currentAttributes).map(key => ({
                    prop:key,
                    label: key
                  }));
                  this.attributeDialogVisible = true;
                }
            }
          },Cesium.ScreenSpaceEventType.LEFT_CLICK);



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
          // vectorItem.dataSource.entities.values.forEach(entity => {
          //   entity.description = entity.properties.getValue();
          //   entity.onClick=()=>{
          //     console.log('111')
          //     this.currentAttributes = entity.properties.getValue();
          //     this.attributeColumns = Object.keys(this.currentAttributes).map(key =>({
          //       prop:key,
          //       label:key
          //     }));
          //     this.attributeDialogVisible = true;
          //   };
          // });

          await this.viewer.flyTo(vectorItem.dataSource)
        }
      
      //保存引用并更新树数据
      this.vectorItems[id] = vectorItem;
      this.updateTreeData();

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
      console.log("item",item)
      if (item){
        item.visible = checked;
        this.toggleVectorVisibility(item);
      }
    },

    //切换矢量可视化
    toggleVectorVisibility(item){
      if (item.isDynamic) {
        // 动态图层处理
        const tileLayer = this.tileLayers[item.id];
        if (tileLayer) {
          tileLayer.show = item.visible;
        }
      } else {
        // 原有静态数据处理
        if (item.points) item.points.show = item.visible;
        if (item.dataSource) item.dataSource.show = item.visible;
      }
      this.viewer.scene.requestRender();
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
          const name = response.name;
          console.log(response.name);
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
}
},
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
</style>