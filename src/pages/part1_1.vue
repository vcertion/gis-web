<template>
  <div class="map-container">
    <div id="cesiumContainer">
      <div class="map-controls">
        <!-- <button @click="switchToImagery">影像地图</button> -->
        <!-- <button @click="switchToVector">矢量地图</button> -->
        <button @click="loadVectorData('http://10.1.99.20:5000/shapefile-to-geojson')">加载矢量数据</button>
        <button @click="loadTiffImage('http://10.1.99.20:5000/tif-to-image')">加载TIF影像</button>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { GeoJsonDataSource } from "cesium";
export default {
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

    // 加载 TIF 影像
    async loadTiffImage(url) {
      try {
        const response = await fetch(url);
        const data = await response.json();
        const imageUrl = data.image;

        // 创建图片图层
        const imageryProvider = new Cesium.SingleTileImageryProvider({
          url: imageUrl,
          rectangle: Cesium.Rectangle.fromDegrees(105.602725, 37.076636, 106.602725, 38.076636),
        });

        this.viewer.imageryLayers.addImageryProvider(imageryProvider);
      } catch (e) {
        console.error("加载失败:", e);
      }
    },

    // 加载矢量数据
    async loadVectorData(url) {
      try {
        const response = await fetch(url);
        const geoJSON = await response.json();

        // 加载 GeoJSON 数据
        const dataSource = await Cesium.GeoJsonDataSource.load(geoJSON);
        this.viewer.dataSources.add(dataSource);

        // 调整视角以显示所有数据
        this.viewer.flyTo(dataSource);
      } catch (e) {
        console.error("加载矢量数据失败:", e);
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