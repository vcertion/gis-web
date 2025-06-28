<template>
  <div class="map-container">
    <div id="container">
      <div class="map-controls">
        <button @click="switchToNormal">标准地图</button>
        <button @click="switchToSatellite">影像地图</button>
        <button @click="loadVectorData('http://10.1.99.20:5000/shapefile-to-geojson')">加载矢量数据</button>
        <button @click="loadTiffImage('http://10.1.99.20:5000/tif-to-image')">加载TIF影像</button>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
// 引入缺德地图
import AMapLoader from '@amap/amap-jsapi-loader';
import { Amap } from '@amap/amap-vue';
import { SatelliteLayer } from '@amap/amap-vue';
import { Message } from 'element-ui';

window.AMapSecurityConfig = {
  securityJsCode: '4e69b3dde83938619d98d34570732cbe', // 你的安全密钥
};
export default {
  data() {
    return {
      map: null,
      satelliteLayer: null,
    };
  },
  mounted() {
    // DOM初始化完成进行地图初始化
    this.initMap();
  },
  methods: {
    async initMap() {
      try {
        const AMap = await AMapLoader.load({
          key: '411f0b0c5cf116eb869da6cebaf0b5d8', // 你的高德地图 key  
          version: '2.0',
          plugins: ['AMap.ImageLayer', 'AMap.GeoJSON','AMap.TileLayer','AMap.MapType'],
        });

        this.map = new AMap.Map('container', {
          viewMode: '3D',
          zoom: 5,
          center: [105.602725, 37.076636],
        });
        
        this.satelliteLayer = new AMap.TileLayer.Satellite();
        // 加载 TIF 影像
        // await this.loadTiffImage('http://your-backend-service/tif-to-image');

        // 加载矢量数据
        // await this.loadVectorData('http://10.181.24.94:5000/shapefile-to-geojson');
      } catch (e) {
        console.error('地图初始化失败:', e);
      }
    },

    async loadTiffImage(url) {
      try {
        const response = await fetch(url);
        const data = await response.json(); // 解析 JSON 数据
        const imageUrl = data.image; // 获取 Base64 图片 URL
        console.log(imageUrl);
        const imageLayer = new AMap.ImageLayer({
          url: imageUrl, // 使用 Base64 图片 URL
          bounds: new AMap.Bounds(
            [105.602725, 37.076636], // 西南角
            [106.602725, 38.076636]  // 东北角
          ),
          opacity: 0.8,
          zIndex: 1000,
        });

        this.map.add(imageLayer);
        this.map.setFitView([imageLayer]); // 调整地图视图范围
        // Message.success('TIF 影像加载成功！');
      } catch (e) {
        console.error('加载失败:', e);
        Message.error('加载失败');
      }
    },

    async loadVectorData(url) {
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const geoJSON = await response.json();

        const vectorLayer = new AMap.GeoJSON({
          geoJSON: geoJSON,
          getMarker: (feature, lnglat) => {
            return new AMap.Marker({
              position: lnglat,
              content: feature.properties.name,
            });
          },
          getPolyline: (feature, lnglats) => {
            return new AMap.Polyline({
              path: lnglats,
              strokeColor: '#FF33FF',
              strokeWeight: 2,
            });
          },
          getPolygon: (feature, lnglats) => {
            return new AMap.Polygon({
              path: lnglats,
              fillColor: '#1791fc',
              strokeColor: '#ffffff',
              strokeWeight: 1,
            });
          },
        });

        this.map.add(vectorLayer);
        // Message.success('加载矢量数据成功');
      } catch (e) {
        console.error('加载矢量数据失败:', e);
      }
    },
    
    // 切换到标准地图
    switchToNormal() {
      this.map.setLayers([new AMap.TileLayer()]); // 使用默认的矢量地图图层
    },

    // 切换到影像地图
    switchToSatellite() {
      this.map.setLayers([this.satelliteLayer]); // 使用影像地图图层
    },
  },
};
</script>

<style lang="less" scoped>
#container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.map-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  margin-top: 33px;
}

.map-controls{
  position: absolute;
  top: 20px;
  right: 20px;
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
