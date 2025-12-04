#!/usr/bin/env python
"""
Startup script for quotation backend
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv('PORT', 9001))  # 使用9001端口避开冲突
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # PM2 handles restarts
    )
