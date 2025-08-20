const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  publicPath: process.env.NODE_ENV === 'production'
    ? '/gis-web/' // 替换为你的 GitHub 仓库名
    : '/',
  configureWebpack: {
    plugins: [
      new CopyWebpackPlugin({
        patterns: [
          {
            from: 'node_modules/cesium/Build/Cesium', // 修正为正确的 Cesium 路径
            to: 'Cesium'
          }
        ]
      })
    ]
  }
};