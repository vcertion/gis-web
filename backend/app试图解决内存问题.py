from flask import Flask, jsonify, request,Response
from osgeo import gdal
from flask_cors import CORS
import fiona
import os
import base64
import zipfile
import shutil
import uuid
import gc
import json
from collections import defaultdict

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)

# 内存优化配置
MAX_POINTS_PER_BATCH = 500
MAX_FILE_SIZE = 1024*1024*1024
CHUNK_SIZE = 500

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
  with fiona.open(file_path) as src:
    features = [feature.__geo_interface__ for feature in src]

  return {
    'type': 'FeatureCollection',
    'features': features
  }
def get_vector_metadata(file_path):
  with fiona.open(file_path) as src:
    first_feature = next(iter(src))
    property = first_feature['properties'] if first_feature['properties'] else {}

    bounds = src.bounds
    return{
      'totalFeatures':len(src),
      'properties':list(property.keys()),
      'bounds':{
        'minLon':bounds[0],
        'minLat':bounds[1],
        'maxLon':bounds[2],
        'maxLat':bounds[3]
      },
      'geometryType':src.schema['geometry'],
      'filePath':file_path
    }
  
def process_shp_chunk(file_path, start_idx, chunk_size):
  features = []

  with fiona.open(file_path) as src:
    for i, feature in enumerate(src):
      if i >= start_idx + chunk_size:
        break
      if i >= start_idx:
        features.append(feature.__geo_interface__)
  import gc
  gc.collect()
  return features

@app.route('/process-zip', methods=['POST'])
def process_zip():
  if 'file' not in request.files:
    return jsonify({'error': 'No file part in the request'}), 400

  file = request.files['file']
  if file.filename == '':
    return jsonify({'error': 'No selected file'}), 400

  if not file.filename.lower().endswith('.zip'):
    return jsonify({'error': 'Invalid file type'}), 400

  # 检查文件大小
  file.seek(0,2)
  file_size = file.tell()
  file.seek(0)

  if file_size > MAX_FILE_SIZE:
    return jsonify({'error':f'文件太大了，最大接收{MAX_FILE_SIZE//(1024*1024*1024)}G'})
  

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
  vector_metadata = []
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
            vector_metadata.append(process_shp(file_path))
            filenames.append(base_name)
            processed_shapes.add(base_name)
          except Exception as e:
            print(f"Error processing SHP: {e}")

  os.remove(zip_path)
  shutil.rmtree(extracted_folder)

  # 垃圾回收
  gc.collect()

  return jsonify({
    'tiffImages': tiff_images,
    'vectorData': vector_metadata,
    'name': filenames
  })

@app.route('/load-vector-chunk',methods=['POST'])
def load_vector_chunk():
  data = request.json
  file_path = data.get('filePath')
  start_idx = data.get('startIdx',0)
  chunk_size = data.get('chunckSize',CHUNK_SIZE)

  if not file_path or not os.path.exists(file_path):
    return jsonify({'error':'文件不存在'}),404
  
  try:
    features = process_shp_chunk(file_path, start_idx, chunk_size)

    gc.collect()

    return jsonify({
      'features':features,
      'startIdx':start_idx,
      'chunkSize':chunk_size,
      'hasMore':len(features) == chunk_size
    })
  except Exception as e:
    return jsonify({'error': str(e)}),500

@app.route('/stream-vector-data', methods=['POST'])
def stream_vector_data():
  data = request.json
  file_path = data.get('filePath')
  chunk_size = data.get('chunkSize',CHUNK_SIZE)

  if not file_path or not os.path.exists(file_path):
    return jsonify({'error':'文件不存在'}),404
  
  def generate():
    try:
      with fiona.open(file_path) as src:
        total_features = len(src)
        processed = 0

        for feature in src:
          feature_data = feature.__geo_interface__
          processed += 1
          if processed % chunk_size == 0:
            yield f"data:{json.dumps({'progress':(processed/total_features)*100,'processed':processed})}"

          yield f"data:{json.dumps({'feature':feature_data,'processed':processed})}\n\n"

          if processed % 10000 == 0:
            gc.collect()
        yield f"data:{json.dumps({'complete':True, 'total':total_features})}\n\n" 
    except Exception as e:
      yield f"data:{json.dumps({'error':str(e)})}\n\n"
  return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
