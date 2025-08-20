from flask import Flask, jsonify, request
from osgeo import gdal
from flask_cors import CORS
import fiona
import os
import base64
import zipfile
import shutil
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)


def process_tif(file_path):
  dataset = gdal.Open(file_path)
  if not dataset:
    raise ValueError('无法打开Tiff文件')

  geotransform = dataset.GetGeoTransform()
  width = dataset.RasterXSize
  height = dataset.RasterYSize

  min_x = geotransform[0]
  max_y = geotransform[3]
  max_x = min_x + geotransform[1] * width
  min_y = max_y + geotransform[5] * height

  bounds = {
    'minLon': min_x,
    'minLat': min_y,
    'maxLon': max_x,
    'maxLat': max_y
  }

  output_path = os.path.join(UPLOAD_FOLDER, f'{uuid.uuid4()}.png')
  gdal.Translate(output_path, file_path, format='PNG')

  with open(output_path, 'rb') as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

  os.remove(output_path)
  return {
    'image': f"data:image/png;base64,{encoded_image}",
    'bounds': bounds
  }


def process_shp(file_path):
  # 修复关键错误：使用 __geo_interface__ 转换 Feature 对象
  with fiona.open(file_path) as src:
    features = [feature.__geo_interface__ for feature in src]

  return {
    'type': 'FeatureCollection',
    'features': features
  }


@app.route('/process-zip', methods=['POST'])
def process_zip():
  if 'file' not in request.files:
    return jsonify({'error': 'No file part in the request'}), 400

  file = request.files['file']
  if file.filename == '':
    return jsonify({'error': 'No selected file'}), 400

  if not file.filename.lower().endswith('.zip'):
    return jsonify({'error': 'Invalid file type'}), 400

  zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
  file.save(zip_path)

  # 解压缩
  extracted_folder = os.path.join(UPLOAD_FOLDER, 'extracted')
  if os.path.exists(extracted_folder):
    shutil.rmtree(extracted_folder)
  os.makedirs(extracted_folder)

  # 改进中文文件名处理
  with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    for file_info in zip_ref.infolist():
      # 尝试多种编码方案
      try:
        file_info.filename = file_info.filename.encode('cp437').decode('gbk')
      except:
        try:
          file_info.filename = file_info.filename.encode('cp437').decode('utf-8')
        except:
          try:
            file_info.filename = file_info.filename.encode('utf-8').decode('utf-8')
          except:
            # 如果所有解码都失败，保留原始文件名
            pass
      zip_ref.extract(file_info, extracted_folder)

  tiff_images = []
  vector_data = []
  filenames = []
  processed_shapes = set()  # 避免重复处理shapefile

  for root, _, files in os.walk(extracted_folder):
    for filename in files:
      file_path = os.path.join(root, filename)
      base_name = os.path.splitext(filename)[0]

      if filename.lower().endswith('.tif'):
        try:
          tiff_images.append(process_tif(file_path))
        except Exception as e:
          print(f"Error processing TIFF: {e}")

      elif filename.lower().endswith('.shp'):
        # 确保每个shapefile只处理一次
        if base_name not in processed_shapes:
          try:
            vector_data.append(process_shp(file_path))
            filenames.append(base_name)
            processed_shapes.add(base_name)
          except Exception as e:
            print(f"Error processing SHP: {e}")

  os.remove(zip_path)
  shutil.rmtree(extracted_folder)

  return jsonify({
    'tiffImages': tiff_images,
    'vectorData': vector_data,
    'name': filenames
  })


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
