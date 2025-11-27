import json
import os
import hashlib
import time
import aiohttp
from geopy.point import Point


def _get_arg_from_env_or_json(arg_name, default=None):
    value = os.getenv(arg_name)
    if value is None or not value.strip():
        try:
            with open('settings.json', 'r', encoding='utf-8') as fp:
                value = json.load(fp)[arg_name]
        except Exception:
            value = default
    return value


def generate_sign(params):
    """新版签名算法"""
    filtered_params = {k: v for k, v in params.items() if k not in ['sign', 'filter']}
    keys = sorted(filtered_params.keys())
    values = []
    for key in keys:
        value = filtered_params[key]
        if isinstance(value, (list, dict)):
            value_str = json.dumps(value, separators=(',', ':'))
        else:
            value_str = str(value)
        values.append(value_str)
    values_str = ','.join(values)
    secret_key = "moveclub123123123"
    sign_string = secret_key + values_str
    return hashlib.md5(sign_string.encode()).hexdigest()


def get_common_headers(token):
    return {
        'xweb_xhr': '1',
        'access-token': token,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'content-type': 'application/json',
        'accept': '*/*',
        'referer': 'https://servicewechat.com/wx07ea19ad2c2b98f3/17/page-frame.html'
    }


async def get_routes():
    route_url = 'https://sport.fudan.edu.cn/sapi/route/list'
    user_id = _get_arg_from_env_or_json('USER_ID')
    token = _get_arg_from_env_or_json('FUDAN_SPORT_TOKEN')
    params = {
        "area_id": "0",
        "type": "0",
        "is_paged": "0",
        "is_show": "1", 
        "status": "2",
        "userid": user_id,
        "token": token
    }
    params['sign'] = generate_sign(params)
    headers = get_common_headers(token)
    async with aiohttp.request('POST', route_url, json=params, headers=headers) as response:
        data = await response.json()
    try:
        route_data_list = filter(lambda route: route['points'] is not None and len(route['points']) >= 1,
                                 data['data']['list'])
        return [FudanRoute(route_data) for route_data in route_data_list]
    except Exception:
        print(f"ERROR: {data['message']}")
        exit(1)


class FudanAPI:
    def __init__(self, route):
        self.route = route
        self.user_id = _get_arg_from_env_or_json('USER_ID')
        self.token = _get_arg_from_env_or_json('FUDAN_SPORT_TOKEN')
        self.system = _get_arg_from_env_or_json('PLATFORM_OS', 'iOS 2016.3.1')
        self.device = _get_arg_from_env_or_json('PLATFORM_DEVICE', 'iPhone|iPhone 13<iPhone14,5>')
        self.run_id = None
        self.start_timestamp = None
        self.track_points = []  # 新增：存储所有轨迹点
        self.distances = []     # 新增：存储每个点的距离

    async def start(self):
        start_url = 'https://sport.fudan.edu.cn/sapi/v2/run/start'
        self.start_timestamp = int(time.time())
        params = {
            'userid': self.user_id,
            'token': self.token,
            'route_id': self.route.id,
            'route_type': self.route.type,
            'system': self.system,
            'device': self.device,
            'lng': str(self.route.start_point.longitude),
            'lat': str(self.route.start_point.latitude),
            'timestamp': str(self.start_timestamp)
        }
        params['sign'] = generate_sign(params)
        headers = get_common_headers(self.token)
        async with aiohttp.request('POST', start_url, json=params, headers=headers) as response:
            data = await response.json()
        try:
            self.run_id = data['data']['run_id']
        except Exception:
            print(f"ERROR: {data['message']}")
            exit(1)

    async def update(self, point, current_distance):
        update_url = 'https://sport.fudan.edu.cn/sapi/v2/run/sync'
        current_time = int(time.time())
        duration = current_time - self.start_timestamp
        
        # 记录轨迹点
        track_point = {
            'lng': round(point.longitude, 6),
            'lat': round(point.latitude, 6),
            't': int(time.time() * 1000)  # 毫秒级时间戳
        }
        self.track_points.append(track_point)
        self.distances.append(current_distance)
        
        # 改进配速计算，避免异常值
        if current_distance > 0 and duration > 0:
            pace = duration / current_distance
            # 限制配速在合理范围内 (3-10分钟/公里)
            min_pace = 180  # 3分钟/公里
            max_pace = 600  # 10分钟/公里
            pace = max(min(pace, max_pace), min_pace)
        else:
            pace = 300  # 默认5分钟/公里
        
        params = {
            'userid': self.user_id,
            'token': self.token,
            'run_id': self.run_id,
            'lng': str(round(point.longitude, 6)),
            'lat': str(round(point.latitude, 6)),
            'distance': str(int(current_distance)),
            'duration': str(duration),
            'pace': f"{pace:.2f}",
            'timestamp': str(current_time)
        }
        params['sign'] = generate_sign(params)
        headers = get_common_headers(self.token)
        
        async with aiohttp.request('POST', update_url, json=params, headers=headers) as response:
            try:
                data = await response.json()
                return data.get('message', 'OK')
            except Exception as e:
                return f"Error: {str(e)}"

    async def finish(self, point, total_distance):
        finish_url = 'https://sport.fudan.edu.cn/sapi/v2/run/finish'
        total_duration = int(time.time()) - self.start_timestamp
        
        # 添加最后一个点
        final_point = {
            'lng': round(point.longitude, 6),
            'lat': round(point.latitude, 6),
            't': int(time.time() * 1000)
        }
        self.track_points.append(final_point)
        self.distances.append(total_distance)
        
        # 构建轨迹数据（二维数组格式）
        track_data = [self.track_points]  # 整个轨迹作为一个分段
        
        total_pace = 0
        if total_distance > 0:
            total_pace = total_duration / total_distance
        
        params = {
            'userid': self.user_id,
            'token': self.token,
            'run_id': self.run_id,
            'system': self.system,
            'device': self.device,
            'lng': str(round(point.longitude, 6)),
            'lat': str(round(point.latitude, 6)),
            'distance': str(int(total_distance)),
            'duration': str(total_duration),
            'pace': f"{total_pace:.2f}",
            'timestamp': str(int(time.time())),
            'points': json.dumps(track_data),  # 轨迹数据作为JSON字符串
            'is_abnormal': '0',  # 正常完成
            'check_points': '[]'  # 空打卡点数组
        }
        params['sign'] = generate_sign(params)
        headers = get_common_headers(self.token)
        
        print(f"上传轨迹数据: {len(self.track_points)}个点")
        async with aiohttp.request('POST', finish_url, json=params, headers=headers) as response:
            data = await response.json()
        return data['message']


class FudanRoute:
    def __init__(self, data):
        self.id = data['route_id']
        self.name = data['name']
        self.type = data['types'][0]
        self.start_point = Point(data['points'][0]['lat'], data['points'][0]['lng'])

    def pretty_print(self):
        print(f"#{self.id}: {self.name}")