import asyncio
import random
import time
from argparse import ArgumentParser

from playground import playgrounds
from sport_api import FudanAPI, get_routes


async def main():
    parser = ArgumentParser()
    parser.add_argument('-v', '--view', action='store_true', help="list available routes")
    parser.add_argument('-r', '--route', help="set route ID", type=int)
    parser.add_argument('-t', '--time', help="total time, in seconds", type=int)
    parser.add_argument('-d', '--distance', help="total distance, in meters", type=int)
    parser.add_argument('-q', '--delay', action='store_true', help="delay for random time")
    args = parser.parse_args()

    if args.view:
        routes = await get_routes()
        supported_routes = filter(lambda r: r.id in playgrounds, routes)
        for route in supported_routes:
            route.pretty_print()
        exit()

    if args.route:
        # 设置距离（米）
        distance = 850
        if args.distance:
            distance = args.distance
        distance += random.uniform(-25.0, 25.0)

        # 设置总时间（秒）
        total_time = 320
        if args.time:
            total_time = args.time
        total_time += random.uniform(-10.0, 10.0)
        steps = int(total_time)  # 按秒拆分步骤
        distance_per_step = distance / steps  # 每步距离增量

        # 获取选中的路线
        routes = await get_routes()
        selected_route = None
        for route in routes:
            if route.id == args.route:
                selected_route = route
                break
        if not selected_route:
            raise ValueError(f'不存在id为{args.route}的route')

        # 随机延迟
        if args.delay:
            sleep_time = random.randint(0, 240)
            print(f"延迟 {sleep_time} 秒后开始...")
            time.sleep(sleep_time)

        # 开始模拟跑步
        automator = FudanAPI(selected_route)
        playground = playgrounds[args.route]
        current_distance = 0.0
        await automator.start()
        print(f"START: {selected_route.name}")

        # 逐步更新跑步数据（避免初始距离为0导致配速计算错误）
        for _ in range(steps):
            current_distance += distance_per_step
            if current_distance > distance:
                current_distance = distance
            # 确保距离至少为0.1米（避免配速计算时分母为0）
            current_distance = max(current_distance, 0.1)
            
            current_point = playground.random_offset(current_distance)
            message = await automator.update(current_point, current_distance)
            print(f"UPDATE: {message} ({current_distance:.2f}m / {distance:.2f}m)")
            await asyncio.sleep(1)

        # 完成跑步
        finish_point = playground.coordinate(distance)
        finish_message = await automator.finish(finish_point, distance)
        print(f"FINISHED: {finish_message}")

if __name__ == '__main__':
    asyncio.run(main())