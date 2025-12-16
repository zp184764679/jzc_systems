#!/usr/bin/env python3
"""
Dashboard 可视化追踪系统 - 主入口
精密加工行业订单追踪、生产流程可视化
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app, db

app = create_app()


# Database initialization command
@app.cli.command('init-db')
def init_db():
    """Initialize the database tables."""
    with app.app_context():
        db.create_all()
        print('Database tables created successfully!')


@app.cli.command('seed-demo')
def seed_demo_data():
    """Seed demo data for testing."""
    from datetime import date, datetime, timedelta
    from app.models import ProductionPlan, ProductionStep, Task

    with app.app_context():
        # Clear existing data
        ProductionStep.query.delete()
        ProductionPlan.query.delete()
        Task.query.delete()

        # Create demo production plans
        demo_plans = [
            {
                'plan_no': 'PP-20241201-001',
                'order_id': 1,
                'order_no': 'ORD-2024-001',
                'customer_id': 1,
                'customer_name': '深圳精密科技有限公司',
                'product_code': 'PART-A001',
                'product_name': 'CNC精密轴套',
                'plan_start_date': date.today() - timedelta(days=10),
                'plan_end_date': date.today() + timedelta(days=5),
                'plan_quantity': 5000,
                'completed_quantity': 3500,
                'status': 'in_progress',
                'priority': 2,
                'department': '生产部',
                'responsible_person': '张工'
            },
            {
                'plan_no': 'PP-20241202-001',
                'order_id': 2,
                'order_no': 'ORD-2024-002',
                'customer_id': 2,
                'customer_name': '东莞机械制造厂',
                'product_code': 'PART-B002',
                'product_name': '精密齿轮',
                'plan_start_date': date.today() - timedelta(days=5),
                'plan_end_date': date.today() + timedelta(days=10),
                'plan_quantity': 2000,
                'completed_quantity': 800,
                'status': 'in_progress',
                'priority': 3,
                'department': '生产部',
                'responsible_person': '李工'
            },
            {
                'plan_no': 'PP-20241203-001',
                'order_id': 3,
                'order_no': 'ORD-2024-003',
                'customer_id': 1,
                'customer_name': '深圳精密科技有限公司',
                'product_code': 'PART-C003',
                'product_name': '连接器外壳',
                'plan_start_date': date.today(),
                'plan_end_date': date.today() + timedelta(days=15),
                'plan_quantity': 10000,
                'completed_quantity': 0,
                'status': 'pending',
                'priority': 3,
                'department': '生产部',
                'responsible_person': '王工'
            }
        ]

        plans = []
        for plan_data in demo_plans:
            plan = ProductionPlan(**plan_data)
            db.session.add(plan)
            plans.append(plan)

        db.session.flush()  # Get IDs

        # Create demo production steps
        demo_steps = [
            ('CNC车削', 2),
            ('铣扁', 1),
            ('电镀', 2),
            ('质检', 1),
            ('包装', 1)
        ]

        for plan in plans:
            prev_step = None
            current_date = datetime.combine(plan.plan_start_date, datetime.min.time())

            for seq, (step_name, days) in enumerate(demo_steps, 1):
                step = ProductionStep(
                    plan_id=plan.id,
                    step_name=step_name,
                    step_sequence=seq,
                    plan_start=current_date,
                    plan_end=current_date + timedelta(days=days),
                    status='completed' if plan.status == 'in_progress' and seq <= 2 else 'pending',
                    completion_rate=100 if plan.status == 'in_progress' and seq <= 2 else 0,
                    depends_on_step_id=prev_step.id if prev_step else None
                )
                db.session.add(step)
                db.session.flush()
                prev_step = step
                current_date = current_date + timedelta(days=days)

        # Create demo tasks
        demo_tasks = [
            {
                'task_no': 'TASK-20241213-001',
                'title': '检查订单ORD-2024-001的CNC车削工序',
                'task_type': 'quality_check',
                'order_no': 'ORD-2024-001',
                'due_date': datetime.now() + timedelta(hours=4),
                'assigned_to_name': '质检员小李',
                'assigned_to_dept': '质检部',
                'priority': 'high'
            },
            {
                'task_no': 'TASK-20241213-002',
                'title': '确认订单ORD-2024-003的原材料到货',
                'task_type': 'procurement',
                'order_no': 'ORD-2024-003',
                'due_date': datetime.now() + timedelta(days=1),
                'assigned_to_name': '采购员小王',
                'assigned_to_dept': '采购部',
                'priority': 'normal'
            },
            {
                'task_no': 'TASK-20241213-003',
                'title': '安排订单ORD-2024-002的电镀外协',
                'task_type': 'production_start',
                'order_no': 'ORD-2024-002',
                'due_date': datetime.now() + timedelta(days=3),
                'assigned_to_name': '计划员小张',
                'assigned_to_dept': '生产部',
                'priority': 'normal'
            }
        ]

        for task_data in demo_tasks:
            task = Task(**task_data)
            db.session.add(task)

        db.session.commit()
        print('Demo data seeded successfully!')


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8100))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    print(f'''
    ╔═══════════════════════════════════════════════════════╗
    ║     Dashboard 可视化追踪系统                          ║
    ║     精密加工行业 - 订单与生产流程追踪                  ║
    ╠═══════════════════════════════════════════════════════╣
    ║     Running on: http://{host}:{port}                  ║
    ║     Health: http://{host}:{port}/health               ║
    ╚═══════════════════════════════════════════════════════╝
    ''')

    app.run(host=host, port=port, debug=debug)
