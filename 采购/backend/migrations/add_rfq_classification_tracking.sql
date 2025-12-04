-- =============================================
-- 添加 RFQ 分类状态追踪字段
-- =============================================

USE caigou;

-- 添加分类状态追踪字段（安全方式：忽略已存在的列）
ALTER TABLE rfqs
ADD COLUMN classification_status VARCHAR(20) NULL COMMENT '分类状态: pending/processing/completed/failed';

ALTER TABLE rfqs
ADD COLUMN classification_task_id VARCHAR(100) NULL COMMENT 'Celery任务ID';

ALTER TABLE rfqs
ADD COLUMN classification_started_at DATETIME NULL COMMENT '分类开始时间';

ALTER TABLE rfqs
ADD COLUMN classification_completed_at DATETIME NULL COMMENT '分类完成时间';

-- 添加索引
CREATE INDEX idx_rfq_classification_status ON rfqs(classification_status);

SELECT '✅ RFQ 分类追踪字段添加完成' AS Result;
