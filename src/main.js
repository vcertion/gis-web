// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue';
// import ElementUI from 'element-ui';
import {
  Button,
  Carousel,
  CarouselItem,
  Menu,
  MenuItem,
  Dropdown,
  DropdownMenu,
  DropdownItem,
  Row,
  Col,
  Card,
  Header,
  Container,
  Aside,
  Main,
  Upload,
  Tree,
  ColorPicker,
  Dialog,
  Table,
  TableColumn,
  Select,
  Option,
  Form,
  FormItem,
  Popover,
  Tooltip,
  Progress,
  Tabs,
  TabPane,
  Message,
  Switch,
  // Message,
} from 'element-ui';
import Viewer from 'v-viewer';
import VueAMap from 'vue-amap';
import 'element-ui/lib/theme-chalk/index.css';
import 'element-ui/lib/theme-chalk/icon.css';
import App from './App';
import axios from './http';

import router from './router';


Vue.prototype.axios = axios;
Vue.config.productionTip = false;

// 配置 axios
Vue.prototype.$http = axios;

// Vue.use(ElementUI);
Vue.use(Viewer);
Vue.use(VueAMap);
Vue.use(Carousel);
Vue.use(CarouselItem);
Vue.use(Button);
Vue.use(Menu);
Vue.use(MenuItem);
Vue.use(Dropdown);
Vue.use(DropdownItem);
Vue.use(DropdownMenu);
Vue.use(Row);
Vue.use(Col);
Vue.use(Card);
Vue.use(Header);
Vue.use(Container);
Vue.use(Aside);
Vue.use(Main);
Vue.use(Upload);
Vue.use(Tree);
Vue.use(ColorPicker);
Vue.use(Dialog);
Vue.use(Table);
Vue.use(TableColumn);
Vue.use(Select);
Vue.use(Option);
Vue.use(Form);
Vue.use(FormItem);
Vue.use(Popover);
Vue.use(Tooltip);
Vue.use(Progress);
Vue.use(Tabs);
Vue.use(TabPane);
Vue.use(Switch);
// Vue.use(Message);
// Vue.use(Message);
Vue.prototype.$message = Message;
/* eslint-disable no-new */
// eslint-disable-next-line no-underscore-dangle
window._AMapSecurityConfig = {
  securityJsCode: '4e69b3dde83938619d98d34570732cbe',  // 如果需要安全密钥，请填写
};
VueAMap.initAMapApiLoader({
  key: '6aa8b5f9e04bec2e4721d8d89e3090e1',
  plugin: [
    'AMap.Autocomplete',
    'AMap.PlaceSearch',
    'AMap.Scale',
    'AMap.OverView',
    'AMap.ToolBar',
    'AMap.MapType',
    'AMap.PolyEditor',
    'AMap.CircleEditor',
  ],
  // 默认高德 sdk 版本为 1.4.4
  v: '2.0',
  uiVersion: '1.0.11',
});


new Vue({
  el: '#app',
  router,
  template: '<App/>',
  components: {
    App,
  },
});
