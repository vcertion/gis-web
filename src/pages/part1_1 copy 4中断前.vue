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
                  <template v-if="data.type === 'color-picker'">
                    <!-- <span>{{ node.label }}</span> -->
                    <el-color-picker 
                      v-model="data.color"
                      @change="(val) => updateColorForNode(node, val)"
                      size="small"
                      show-alpha
                      :predefine="predefineColors"
                  />
                  </template>
            </span>
          </template>
        </el-tree>
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
import { GeoJsonDataSource } from "cesium";
import Color from "cesium/Source/Core/Color";
import CheckerboardMaterialProperty from "cesium/Source/DataSources/CheckerboardMaterialProperty";
import Cesium3DTile from "cesium/Source/Scene/Cesium3DTile";
import { pitch } from "file-loader";
import { point } from "leaflet";
import { head } from "shelljs";
import { expand } from "shelljs/src/common";
import 'element-ui/lib/theme-chalk/icon.css'
import { LabelsLayer } from "@amap/amap-vue";
export default {
  data() {
    return {
        selectedAttribute:'default',//当前选择中的属性字段
        selectedColorScheme:'red-yellow-green',
        colorScheme:{
          'red-yellow-green':['#ff0000', '#ffff00', '#00ff00'],
          'blue-purple-red':['#0000ff', '#800080', '#ff0000'],
          'viridis':['#440154', '#21908d', '#fde725'],
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
          selectedAttribute: 'default',
          selectedColorScheme: 'red-yellow-green'
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
          this.addPoints(vectorItem.points, pointFeatures, vectorItem.color)
          
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
          // const points = this.viewer.scene.primitives.add(new Cesium.PointPrimitiveCollection());
          
          // const unusedColors = this.availableColors.filter(color => !this.useColors.has(color))
          // if (unusedColors.length === 0){
          //   this.useColors.clear();
          //   unusedColors.push(...this.availableColors);
          // }
          
          // const randomColor = unusedColors[Math.floor(Math.random() * unusedColors.length)];
          // this.useColors.add(randomColor)
          
          // pointFeatures.forEach(feature => {
          //   points.add(
          //     {
          //       position: Cesium.Cartesian3.fromDegrees(
          //         feature.geometry.coordinates[0],
          //         feature.geometry.coordinates[1]
          //       ),
          //       color: randomColor,
          //       pixelSize: 5
          //     }
          //   );
          // });
        }
        //渲染面和线
        if (otherFeatures.length > 0){
          vectorItem.dataSource = await Cesium.GeoJsonDataSource.load({
            type: "FeatureCollection",
            features: otherFeatures
          });
          this.setDataSourceStyle(vectorItem.dataSource, vectorItem.color);
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
    addPoints(points, features, color){
      const cesiumColor = Cesium.Color.fromCssColorString(color)
      features.forEach(feature => {
        points.add({
          position: Cesium.Cartesian3.fromDegrees(
            feature.geometry.coordinates[0],
            feature.geometry.coordinates[1]
          ),
          color: cesiumColor,
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
      this.vectorTreeData = Object.values(this.vectorItems).map(item =>({
        id:item.id,
        label: item.name,
        name:item.name,
        color:item.color,
        children:[
          {
            id: `${item.id}-color-picker`,
            type:'color-picker',
            color:item.color
          },
        ],
        expanded: false
      }));

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
      }
      if(item.dataSource){
        item.dataSource.show = item.visible;
      }
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
          console.log(item.dataSource)
          console.log(data.color)
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
      if(data.type !== 'color-picker'){
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

    //更新单个数据集的属性字段
    updateVectorItemAttribute(id, attribute){
      const item = this.vectorItems[id];
      if(item){
        item.selectedAttribute = attribute;
        this.updatePointsColors(item);
      }
    },

    //更新单个数据集的色带
    updateVectorItemColorScheme(id, Scheme) {
      const item = this.vectorItems[id];
      if (item){
        item.selectedColorScheme = Scheme;
        this.updatePointsColors(item);
      }
    },

    updatePointsColors(){
      Object.values(this.vectorItems).forEach(vectorItem =>{
        if (vectorItem.points){
          vectorItem.points.removeAll();

          const values = vectorItem.pointFeatures.map(feature =>
            parseFloat(feature.properties[this.selectedAttribute])
          ).filter(v => !isNaN(v));
          const minvalue = Math.min(...values);
          const maxvalue = Math.max(...values);
          const colorScale = this.getColorScale(minvalue, maxvalue);

          vectorItem.pointFeatures.forEach(feature => {
            const value = parseFloat(feature.properties[this.selectedAttribute]);
            const color = isNaN(value)?
                Cesium.Color.WHITE:
                colorScale(value);
            
            vectorItem.points.add({
              position: Cesium.Cartesian3.fromDegrees(
                feature.geometry.coordinates[0],
                feature.geometry.coordinates[1]
              ),
              color: color,
              pixelSize: 5
            });
          });
        }
      });
    },


  },
};
</script>

<style lang="less" scoped>
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
</style>