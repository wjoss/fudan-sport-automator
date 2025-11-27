import random
from math import pi

from geopy.distance import distance
from geopy.point import Point

l = 86.96
r = 36.5
c = pi * r
d = 400


def rad2ang(rad):
    return (rad / pi) * 180


class Playground:
    def __init__(self, point, direction):
        self.start = point
        self.direction = direction
        self.center_1 = distance(meters=r).destination(self.start, direction + 90)
        self.center_2 = distance(meters=l).destination(self.center_1, direction - 180)
        self.anchor_1 = distance(meters=r).destination(self.center_1, direction + 90)
        self.anchor_2 = distance(meters=l).destination(self.start, direction + 180)

    def coordinate(self, x):
        x = x % d

        if x < c:
            angle = self.direction - 90 + rad2ang(x / r)
            return distance(meters=r).destination(self.center_1, angle)
        x = x - c
        if x < l:
            angle = self.direction + 180
            return distance(meters=x).destination(self.anchor_1, angle)
        x = x - l
        if x < c:
            angle = self.direction + 90 + rad2ang(x / r)
            return distance(meters=r).destination(self.center_2, angle)
        x = x - c
        return distance(meters=x).destination(self.anchor_2, self.direction)

    def random_offset(self, x):
        angle = random.randint(0, 360)
        offset = random.uniform(0, 0.3)
        coord = self.coordinate(x)
        return distance(meters=offset).destination(coord, angle)


playgrounds = {
    # 邯郸校区
    28: Playground(Point(31.291805, 121.502810), 180),  # 邯郸南区田径场早操
    29: Playground(Point(31.299212, 121.497172), 180),  # 邯郸北区早操
    33: Playground(Point(31.290807, 121.502805), 180),  # 邯郸南区田径场课外活动
    34: Playground(Point(31.296773, 121.507075), 216.5),  # 邯郸校外田径场课外活动
    38: Playground(Point(31.291805, 121.502805), 180),  # 邯郸南区田径场夜跑
    39: Playground(Point(31.295949, 121.507585), 216.5),  # 邯郸校外田径场夜跑
    47: Playground(Point(31.300564, 121.507174), 180),  # 邯郸东区早操
    48: Playground(Point(31.298228, 121.506942), 180),  # 邯郸本部早操
    
    # 江湾校区
    30: Playground(Point(31.334087, 121.501873), 166.3),  # 江湾田径场早操
    35: Playground(Point(31.333924, 121.501948), 166.3),  # 江湾田径场课外活动
    40: Playground(Point(31.335219, 121.502667), 166.3),  # 江湾校区夜跑
    
    # 枫林校区
    31: Playground(Point(31.195844, 121.451268), 180),  # 枫林田径场早操
    36: Playground(Point(31.195866, 121.451262), 180),  # 枫林田径场课外活动
    41: Playground(Point(31.195866, 121.451283), 180),  # 枫林校区夜跑
    
    # 张江校区
    32: Playground(Point(31.189964, 121.598392), 180),  # 张江校区早操
    37: Playground(Point(31.189906, 121.598406), 180),  # 张江校区课外活动
    42: Playground(Point(31.189915, 121.598419), 180),  # 张江校区夜跑
}