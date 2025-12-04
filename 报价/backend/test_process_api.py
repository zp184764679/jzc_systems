"""
测试工序API响应
"""
from fastapi import FastAPI
from api.schemas import ProcessResponse
from datetime import datetime

app = FastAPI()

@app.get("/test/process", response_model=ProcessResponse)
def test_process():
    """测试返回一个硬编码的工序对象"""
    return ProcessResponse(
        id=999,
        process_code="TEST",
        process_name="测试工序",
        category="测试",
        machine_type=None,
        machine_model=None,
        hourly_rate=100.0,
        setup_time=0.5,
        daily_fee=500.0,  # 测试这个字段
        daily_output=1000,
        defect_rate=1.0,
        icon="🔧",  # 测试这个字段
        description="测试工序说明",
        is_active=True,
        created_at=datetime.now(),
        updated_at=None
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
