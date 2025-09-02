
from inspect import Attribute
from flask import Flask, jsonify, request
from osgeo import gdal
from flask_cors import CORS
import fiona
import os
import base64
import zipfile
import shutil
import uuid
import gc
import logging
import math

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://vcertion.github.io",
    "http://localhost:8080"
]}})
# CORS(app)

CHUNK_SIZE = 10000
# CHUNK_SIZE = 10

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_shp_with_pagination(file_path):
    """分页处理shapefile"""
    with fiona.open(file_path) as src:
        total_features = len(src)
        total_chunks = (total_features + CHUNK_SIZE - 1) // CHUNK_SIZE
        attribute_keys = list((src.schema or {}).get('properties',{}).keys())
        return {
            'type': 'FeatureCollection',
            'totalFeatures': total_features,
            'totalChunks': total_chunks,
            'chunkSize': CHUNK_SIZE,
            'filePath': file_path,  # 保存文件路径
            'attributeKeys':attribute_keys
        }
@app.route('/load-vector-geometry', methods=['POST'])
def load_vector_geometry():
    """只加载几何信息"""
    data = request.get_json(silent=True) or {}
    chunk_index = data.get('chunkIndex', 0)
    file_path = data.get('filePath')

    if not file_path or not os.path.exists(file_path):
      return jsonify({'error': 'File not found'}), 404

    with fiona.open(file_path) as src:
      start_idx = chunk_index * CHUNK_SIZE
      end_idx = min(start_idx + CHUNK_SIZE, len(src))

      features = []
      for i in range(start_idx, end_idx):
        feature = src[i].__geo_interface__

        geometry_only = {
          'type': 'Feature',
          'id': feature.get('id', i),
          'geometry': feature['geometry'],
          'properties': {}
        }
        features.append(geometry_only)
      gc.collect()
      return jsonify({
        'features': features,
        'chunkIndex': chunk_index,
        'hasMore': end_idx < len(src)
      })
    # try:

    # except Exception as e:
    #     return jsonify({'error':str(e)}),500

@app.route('/load-point-attributes', methods=['POST'])
def load_point_attributes():
    """按需加载指定点的属性信息"""
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get('file_path')
        point_ids = data.get('pointIds',[])

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error':'未找到文件'}),404

        attributes = {}
        with fiona.open(file_path) as src:
            for i, feature in enumerate(src):
                feature_data = feature.__geo_interface__
                feature_id = feature_data.get('id',i)

                if feature_id in point_ids:
                    attributes[feature_id] = feature_data.get('properties')
        return jsonify({'attributes':attributes})
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route('/get-attribute-stats', methods=['POST'])
def get_attribute_stats():
    """获取字段的统计信息（min, max, count等）"""
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get('filePath')
        attribute_name = data.get('attributeName')

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        if not attribute_name:
            return jsonify({'error': 'No attribute name provided'}), 400

        values = []
        with fiona.open(file_path) as src:
            for feature in src:
                feature_data = feature.__geo_interface__
                properties = feature_data.get('properties', {})
                if attribute_name in properties:
                    try:
                        value = float(properties[attribute_name])
                        if not math.isnan(value):
                            values.append(value)
                    except (ValueError, TypeError):
                        continue

        if not values:
            return jsonify({'error': 'No valid values found'}), 404

        stats = {
            'min': min(values),
            'max': max(values),
            'count': len(values),
            'mean': sum(values) / len(values)
        }

        return jsonify(stats)
    except Exception as e:
        app.logger.exception('get_attribute_stats failed')
        return jsonify({'error': str(e)}), 500

@app.route('/load-attribute-values', methods=['POST'])
def load_attribute_values():
    """按字段名批量拉取属性值"""
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get('filePath')
        attribute_name = data.get('attributeName')
        point_ids = data.get('pointIds', [])

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        if not attribute_name:
            return jsonify({'error': 'No attribute name provided'}), 400
        if not isinstance(point_ids, list) or len(point_ids) == 0:
            return jsonify({'values': {}})

        wanted = set(point_ids)
        values = {}
        remaining = len(wanted)

        with fiona.open(file_path) as src:
            for i, feature in enumerate(src):
                if i in wanted:
                    props = feature.__geo_interface__.get('properties', {})
                    if attribute_name in props:
                        values[i] = props[attribute_name]
                        remaining -= 1
                        if remaining <= 0:
                            break

        return jsonify({'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load-attributes-by-coordinates', methods=['POST'])
def load_attributes_by_coordinates():
    """根据坐标批量加载点属性（带容差）"""
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get('filePath')  # 修正参数名
        coordinates = data.get('coordinates', [])
        tolerance = data.get('tolerance', 0.0001)

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': '未找到文件'}), 404

        if not isinstance(coordinates, list) or len(coordinates) == 0:
            return jsonify({'attributes': []})

        attrs = []
        with fiona.open(file_path) as src:
            for idx, feature in enumerate(src):
                feature_data = feature.__geo_interface__  # 修正拼写错误
                geom = feature_data.get('geometry', {})

                if geom and geom.get('type') in ['Point', 'LineString', 'Polygon', 'MultiLineString', 'MultiPolygon']:
                    rep_coord = get_representative_coordinate(geom)

                    if rep_coord and len(rep_coord) >=2:
                        for target_coord in coordinates:
                            if (len(target_coord) >= 2 and
                                abs(rep_coord[0] - target_coord[0]) <= tolerance and
                                abs(rep_coord[1] - target_coord[1]) <= tolerance):
                                attrs.append({
                                    'id': idx,
                                    'coordinates': rep_coord,
                                    'properties': feature_data.get('properties', {})
                                })
                                break
        return jsonify({'attributes': attrs})
    except Exception as e:
        app.logger.exception('load_attributes_by_coordinates failed')
        return jsonify({'error': str(e)}), 500

def get_representative_coordinate(geometry):
    geometry_type = geometry.get('type')
    coordinates = geometry.get('coordinates',[])

    if not coordinates:
        return None

    if geometry_type == 'Point':
        return coordinates if len(coordinates) >= 2 else None;
    elif geometry_type == 'LineString':
        if len(coordinates) >=2:
            return coordinates[len(coordinates) // 2]
        return None
    elif geometry_type == 'Polygon':
        if coordinates and coordinates[0] and len(coordinates[0]) > 2:
            return coordinates[0][0]
        return None
    elif geometry_type == 'MultiLineString':
        if coordinates and len(coordinates) > 0 and coordinates[0] and len(coordinates[0]) > 2:
            return coordinates[0][len(coordinates[0]) // 2]
        return None
    elif geometry_type == 'MultiPolygon':
        if coordinates and len(coordinates) > 0 and coordinates[0] and coordinates[0][0] and len(coordinates[0][0]) > 2:
            return coordinates[0][0][0]
        return None
    else:
        return None

@app.route('/load-vector-chunk', methods=['POST'])
@app.route('/load-vector-chunk/', methods=['POST'])
def load_vector_chunk():
    """分页加载矢量数据"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data received'}), 400

        chunk_index = data.get('chunkIndex', 0)
        file_path = data.get('filePath')

        if not file_path:
            return jsonify({'error': 'No filePath provided'}), 400

        if not os.path.exists(file_path):
            return jsonify({'error': f'File not found: {file_path}'}), 404

        with fiona.open(file_path) as src:
            start_idx = chunk_index * CHUNK_SIZE
            end_idx = min(start_idx + CHUNK_SIZE, len(src))

            features = []
            for i in range(start_idx, end_idx):
                features.append(src[i].__geo_interface__)

            # 强制垃圾回收
            gc.collect()

            return jsonify({
                'features': features,
                'chunkIndex': chunk_index,
                'hasMore': end_idx < len(src)
            })
    except Exception as e:
        print(f"Error in load_vector_chunk: {str(e)}")  # 添加日志
        return jsonify({'error': str(e)}), 500

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
@app.route('/process-zip/', methods=['POST'])
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
                        # 使用分页处理函数
                        vector_metadata = process_shp_with_pagination(file_path)
                        vector_data.append(vector_metadata)
                        filenames.append(base_name)
                        processed_shapes.add(base_name)
                    except Exception as e:
                        print(f"Error processing SHP: {e}")

    os.remove(zip_path)
    # shutil.rmtree(extracted_folder)

    return jsonify({
        'tiffImages': tiff_images,
        'vectorData': vector_data,
        'name': filenames
    })


@app.errorhandler(404)
def _not_found(e):
    app.logger.info(f"404 path={request.path} method={request.method}")
    return jsonify(error="not found", path=request.path), 404

@app.get("/")
def index():
    return jsonify(status="ok")

@app.get("/healthz")
def healthz():
    return jsonify(ok=True)

# 打印到 Gunicorn 日志
logging.getLogger('gunicorn.error').info(f"URL MAP => {app.url_map}")



if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
