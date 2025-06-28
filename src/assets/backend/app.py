from flask import Flask, send_file, jsonify
# from osgeo import gdal
import gdal
from flask_cors import CORS
import fiona
import os 
import base64

app = Flask(__name__)
CORS(app)

@app.route('/shapefile-to-geojson')
def shapefile_to_geojson():
    shapefile_path = "D:\中国标准行政区划数据\shp格式\中国_省.shp"

    with fiona.open(shapefile_path) as src:
        features = [feature for feature in src]


    return jsonify({
        'type': 'FeatureCollection',
        'features': features
    })

@app.route('/tif-to-image')
def tif_to_image():
    tif_path = r"C:\Users\Admin\Desktop\新建文件夹\RGI60-13.04946\dem.tif"
    output_path = r"D:\7.png"

    # 将 TIF 转换为 PNG
    if os.path.exists(output_path):
        os.remove(output_path)
    gdal.Translate(output_path, tif_path, format='PNG')

    # 读取 PNG 文件并转换为 Base64
    with open(output_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    return jsonify({
        'image': f"data:image/png;base64,{encoded_image}"
    })
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
