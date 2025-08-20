<template>
  <div class="map-container">
    <div class="sidebar" v-if="shoowSidebar">
          <el-tree
          :data="vectorTreeData"
          show-checkbox
          node-key="id"
          :props="treeProps"
          @check-change="handleCheckChange">
          <template #default="{ node, data}">
            <span class="tree-node">
              <span>{{ node.label }}</span>
              <input 
                type="color"
                v-model="data.color"
                @change="updataVectorColor(data)"
                style="margin-left:10px ;"
                />
            </span>
          </template>
        </el-tree>
      </div>
    <div id="cesiumContainer">
      <div class="map-controls">
        <button @click="toogleSidebar" type="info">
          {{ shoowSidebar ? '隐藏管理' : '显示管理' }}
        </button>
        <!-- <button @click="switchToImagery">影像地图</button> -->
        <!-- <button @click="switchToVector">矢量地图</button> -->
        <!-- <button @click="loadVectorData('http://192.168.1.4:5000/shapefile-to-geojson')">加载矢量数据</button> -->
        <!-- <button @click="loadTiffImage('http://10.1.99.20:5000/tif-to-image')">加载TIF影像</button> -->
        <el-upload
          action="http://127.0.0.1:5000/process-zip"
          :on-success="handleSuccess"
          :show-file-list="false"
          :before-upload="beforeUpload"
          accept=".zip"
        >
          <el-button type="primary" style="color: black;">上传数据</el-button>
        </el-upload>
        <el-button 
        type="danger"
        @click="clearData"
        style="margin-left: 10px; color: red;"
        >清空数据</el-button>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { GeoJsonDataSource } from "cesium";
import Color from "cesium/Source/Core/Color";
import { pitch } from "file-loader";
import { point } from "leaflet";
import { head } from "shelljs";
export default {
  data() {
    return {
        showSidebar: true,
        vectorTreeData: [],
        treeProps:{
          label: 'name',
          children: 'children'
        },
        vectorItems:{},//索引储存
    };
  },
  name: "CesiumView",
  mounted() {
    this.initMap();
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

    //  // 加载矢量数据
    // async loadVectorData(url) {
    //   try {
    //     const response = await fetch(url);
    //     const geoJSON = await response.json();

    //     console.log(geoJSON);
    //     // 加载 GeoJSON 数据
    //     const dataSource = await Cesium.GeoJsonDataSource.load(geoJSON);
    //     this.viewer.dataSources.add(dataSource);

    //     // 调整视角以显示所有数据
    //     this.viewer.flyTo(dataSource);
    //   } catch (e) {
    //     console.error("加载矢量数据失败:", e);
    //   }
    // },

    // 加载矢量数据
    async loadVectorData(geoJSON, name='未命名数据') {
      try {
        // const response = await fetch(url);
        // const geoJSON = await response.json();
        const id = Date.now().toString();

        const vectorItem = {
          id,
          name,
          color:'#FF00000',
          points:null,
          dataSource:null,
          visible: true
        };

        console.log(geoJSON);
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
        
        if (pointFeatures.length > 0){
          const points = this.viewer.scene.primitives.add(new Cesium.PointPrimitiveCollection());
          
          const unusedColors = this.availableColors.filter(color => !this.useColors.has(color))
          if (unusedColors.length === 0){
            this.useColors.clear();
            unusedColors.push(...this.availableColors);
          }
          
          const randomColor = unusedColors[Math.floor(Math.random() * unusedColors.length)];
          this.useColors.add(randomColor)
          
          pointFeatures.forEach(feature => {
            points.add(
              {
                position: Cesium.Cartesian3.fromDegrees(
                  feature.geometry.coordinates[0],
                  feature.geometry.coordinates[1]
                ),
                color: randomColor,
                pixelSize: 5
              }
            );
          });
        }
        //渲染面和线
        let dataSource
        if (otherFeatures.length > 0){
          dataSource = await Cesium.GeoJsonDataSource.load({
            type: "FeatureCollection",
            features: otherFeatures
          });
          this.viewer.dataSources.add(dataSource);
        }
        if (dataSource){
          this.viewer.flyTo(dataSource)
        } else if (pointFeatures.length > 0 ){
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
        // // 加载 GeoJSON 数据
        // // const isPointData = geoJSON.features
        // const dataSource = await Cesium.GeoJsonDataSource.load(geoJSON);
        // this.viewer.dataSources.add(dataSource);

        // // 调整视角以显示所有数据
        // this.viewer.flyTo(dataSource);
      } catch (e) {
        console.error("加载矢量数据失败:", e);
      }
    },

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
      console.log('success');

      //根据文件扩展名调用对应的方法
      if (response.tiffImages){
        for (const imageUrl of response.tiffImages){
            await this.loadTiffImage(imageUrl);
        }
      }
      if (response.vectorData){
        for (const geoJsonUrl of response.vectorData){
          await this.loadVectorData(geoJsonUrl);
        }
      }
    },



  },
};
</script>

<style lang="less" scoped>
#cesiumContainer {
  width: 100%;
  height: calc(100vh - 10px);
  border-radius: 8px;
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
}

.map-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  margin-top: 7vh;
}

.map-controls {
  position: absolute;
  top: 40px;
  left: 20px;
  z-index: 10;
}

.map-controls button {
  margin: 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.map-controls button:hover {
  background-color: #f0f0f0;
}
</style>