# -*- coding: utf-8 -*-
from app import app

print("=" * 80)
print("所有注册的路由:")
print("=" * 80)

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
        'path': str(rule)
    })

# 按路径排序
routes.sort(key=lambda x: x['path'])

# 只显示我们关心的路由
for route in routes:
    if '/invoice' in route['path'] or '/receipt' in route['path'] or route['path'] == '/api/v1/' or '/api/v1/login' in route['path']:
        print(f"{route['methods']:10} {route['path']:50} -> {route['endpoint']}")

print("=" * 80)
