from flask import Flask, send_file, jsonify,request
from osgeo import gdal
# from GDAL import gdal
from flask_cors import CORS
from sqlalchemy import create_engine, inspect, text
import geopandas as gpd
import fiona
import os
import base64
import zipfile
import shutil
import uuid
import json
import time
from shapely.geometry import mapping

try:
    from geoalchemy2 import Geometry
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

app = Flask(__name__)
CORS(app)

#数据库配置
DB_CONN = 'postgresql://postgres:q1w2e3r4@localhost:5432/test'
engine = create_engine(DB_CONN)

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

    '''处理tif文件并返回Base64图片'''
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
    '''处理shp文件并返回GeoJSON'''
    with fiona.open(file_path) as src:
        features = []
        for feature in src:
            geom = feature['geometry']
            if geom is not None:
                geom ={
                    'type':geom['type'],
                    'coordinates':geom['coordinates']
                }
            properties = dict(feature['properties']) if feature['properties'] else {}
            features.append({
                'type':'Feature',
                'geometry':geom,
                'properties':properties
            })
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

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      for file_info in zip_ref.infolist():
        try:
          file_info.filename = file_info.filename.encode('cp437').decode('gbk')
        except:
          file_info.filename = file_info.filename.encode('utf-8').decode('utf-8')
        zip_ref.extract(file_info,extracted_folder)

    tiff_images = []
    vector_data = []
    filenames = []

    for root, dirs, files in os.walk(extracted_folder):
        for filename in files:
            file_path = os.path.join(root, filename)
            if filename.lower().endswith('.tif'):
                tiff_images.append(process_tif(file_path))
            elif filename.lower().endswith('.shp'):
                filenames.append(filename.split('.')[0])
                vector_data.append(process_shp(file_path))

    os.remove(zip_path)
    shutil.rmtree(extracted_folder)

    layer_name = str(int(time.time() * 1000))
    gdf = gpd.GeoDataFrame.from_features(vector_data[0]['features'])

    if HAS_GEOALCHEMY:
       gdf.to_postgis(
        name=layer_name,
        con=engine,
        if_exists='replace',
        index=False,
        dtype={'geometry': Geometry('GEOMETRY', srid=4326)}
        )
    else:
        with engine.connect() as conn:
            conn.execute(text(f"""CREATE TABLE IF NOT EXISTS "{layer_name}" (id SERIAL PRIMARY KEY,geometry GEOMETRY(GEOMETRY, 4326),properties JSONB);"""))

            for feature in vector_data[0]['features']:
                geom = f"ST_GeomFromGeoJSON('{json.dumps(feature['geometry'])}')"
                props = json.dumps(feature['properties'])
                conn.execute(text(f"""
                    INSERT INTO "{layer_name}" (geometry, properties)
                    VALUES ({geom}, '{props}');
                """))
            conn.commit()


    return jsonify({
      'tiffImages':tiff_images,
      'vectorData':vector_data,
      'name':layer_name
    })


@app.route('/shapefile-to-geojson')
def shapefile_to_geojson():
    shapefile_path = r"D:\wechats\WeChat Files\wxid_a1pnsm9pota922\FileStorage\File\2025-06\050A_GISSHP.shp"

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


# 千万级数据支持
@app.route('/vector-tiles', methods=['GET'])
def get_vector_tiles():
    '''
    动态矢量切片接口
    参数：
    minLon,minLat,maxLon,maxLat
    zoom
    layer
    '''
    # 获取参数并验证
    min_lon = request.args.get('minLon', type=float)
    min_lat = request.args.get('minLat', type=float)
    max_lon = request.args.get('maxLon', type=float)
    max_lat = request.args.get('maxLat', type=float)
    layer = request.args.get('layer')
    page = request.args.get('page', default=0, type=int)
    page_size = request.args.get('pageSize', default=2000, type=int)

    # 验证参数
    if None in [min_lon, min_lat, max_lon, max_lat, layer]:
      return jsonify({"error": "Missing required parameters"}), 400

    # 使用参数化查询防止SQL注入
    sql = f"""SELECT geometry,properties  FROM "{layer}" WHERE ST_Intersects(geometry,ST_MakeEnvelope(%s, %s, %s, %s, 4326)) ORDER BY id LIMIT %s OFFSET %s;"""

    # 计算offset
    offset = page * page_size
    gdf = gpd.read_postgis(sql, engine, params=(min_lon, min_lat, max_lon, max_lat, page_size, offset),
                           geom_col='geometry')

    return gdf_to_geojson(gdf)




def query_aggregated_data(bbox, zoom, layer):
    '''
    聚合查询
    返回geojson
    '''
    grid_size = 1000 / (2 ** max(0, 10 - zoom))

    sql = f"""
    WITH clustered AS (
        SELECT
            ST_ClusterDBSCAN(geometry, {grid_size}, 1) OVER() AS cluster_id,
            geometry,
            properties
        FROM "{layer}"
        WHERE ST_Intersects(
            geometry,
            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
        )
    )
    SELECT
        ST_Centroid(ST_Collect(geometry)) AS geometry,
        jsonb_object_agg(key, value) AS properties
    FROM
        clustered,
        jsonb_each_text(properties)
    GROUP BY
        cluster_id
    LIMIT 10000  -- 防止返回过多聚合点
"""

    gdf = gpd.read_postgis(sql, con=engine, params=bbox,geom_col='geometry')
    return gdf_to_geojson(gdf)

def query_raw_data(bbox, zoom, layer):
    '''
    原始数据返回
    '''
    limit = 50000 if zoom >= 14 else 10000
    sql = f"""
    SELECT
        geometry,
        properties
    FROM "{layer}"
    WHERE ST_Intersects(
        geometry,
        ST_MakeEnvelope(%s, %s, %s, %s, 4326)
    )
    LIMIT {limit}
    """
      # result = conn.execute(sql).fetchall()
    gdf = gpd.read_postgis(sql, con=engine, params=bbox,geom_col='geometry')
    return gdf_to_geojson(gdf)

def gdf_to_geojson(gdf):
    '''将geodataframe转为geojson'''
    return{
        'type':'FeatureCollection',
        'features':[
            {
                'type':'Feature',
                'geometry':mapping(gdf.iloc[i].geometry),
                'properties':gdf.iloc[i].properties
            }
            for i in range(len(gdf))
        ]
    }

@app.route('/ingest-shp', methods=['POST'])
def ingest_shp():
    '''
    将上传的shp数据导入POSTgis
    '''
    if 'file' not in request.files:
        return jsonify({'error':'No file'}),400

    file = request.files['file']
    if not file.filename.lower().endswith('.zip'):
        return jsonify({'error':'Invalid file type'}),400

    # 临时解压
    temp_dir = os.path.join(UPLOAD_FOLDER,str(uuid.uuid4()))
    os.makedirs(temp_dir)
    file.save(os.path.join(temp_dir, file.filename))

    with zipfile.ZipFile(os.path.join(temp_dir, file.filename), 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # 找到shp文件
    shp_path = None
    for root, _, files in os.walk(temp_dir):
        for f in files:
            if f.lower().endswith('.shp'):
                shp_path = os.path.join(root, f)
                break
        if shp_path:
            break

    if not shp_path:
        return jsonify({'error':'No SHP file found'}),400

    # 导入postgis
    table_name = f'layer_{uuid.uuid4().hex[:8]}'
    cmd = f"shp2pgsql -s 4326 -I {shp_path} {table_name} | psql -d gis_db"
    os.system(cmd)

    return jsonify({
        'status':'success',
        'table':table_name,
        'count':get_row_count(table_name)
    })

def get_row_count(table_name):
    '''获取表行数'''
    with engine.connect() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
