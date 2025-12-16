/**
 * 销售漏斗看板 (Kanban)
 * 拖拽式阶段管理，可视化销售管道
 */
import { useState, useEffect } from 'react';
import {
  Card, Row, Col, Tag, Space, Button, Modal, Form, Select, Input,
  message, Statistic, Badge, Tooltip, Progress, Empty, Spin
} from 'antd';
import {
  DollarOutlined, UserOutlined, CalendarOutlined,
  RightOutlined, PlusOutlined, ReloadOutlined, EyeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { opportunityAPI } from '../services/api';

const { TextArea } = Input;

// 阶段颜色和样式配置
const STAGE_CONFIG = {
  lead: { color: '#d9d9d9', bgColor: '#fafafa', name: '线索', icon: '🎯' },
  qualified: { color: '#1890ff', bgColor: '#e6f7ff', name: '已确认', icon: '✓' },
  proposal: { color: '#faad14', bgColor: '#fffbe6', name: '方案阶段', icon: '📋' },
  negotiation: { color: '#fa8c16', bgColor: '#fff7e6', name: '商务谈判', icon: '🤝' },
};

// 优先级颜色
const PRIORITY_COLORS = {
  low: '#52c41a',
  medium: '#1890ff',
  high: '#fa8c16',
  urgent: '#f5222d',
};

export default function SalesPipeline() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [pipeline, setPipeline] = useState([]);
  const [stages, setStages] = useState([]);
  const [stageModalVisible, setStageModalVisible] = useState(false);
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [targetStage, setTargetStage] = useState(null);

  const [form] = Form.useForm();

  useEffect(() => {
    loadStages();
    loadPipeline();
  }, []);

  const loadStages = async () => {
    try {
      const res = await opportunityAPI.getStages();
      setStages(res.stages || []);
    } catch (error) {
      console.error('加载阶段定义失败:', error);
    }
  };

  const loadPipeline = async () => {
    setLoading(true);
    try {
      const res = await opportunityAPI.getPipeline();
      setPipeline(res.pipeline || []);
    } catch (error) {
      message.error('加载销售漏斗失败');
    } finally {
      setLoading(false);
    }
  };

  // 点击推进按钮
  const handleMoveStage = (opp, toStage) => {
    setSelectedOpp(opp);
    setTargetStage(toStage);
    form.setFieldsValue({ stage: toStage });
    setStageModalVisible(true);
  };

  // 确认阶段变更
  const handleConfirmMove = async () => {
    try {
      const values = await form.validateFields();
      await opportunityAPI.updateStage(selectedOpp.id, {
        stage: values.stage,
        reason: values.reason,
      });
      message.success('阶段更新成功');
      setStageModalVisible(false);
      loadPipeline();
    } catch (error) {
      message.error(error.message || '更新失败');
    }
  };

  // 查看详情
  const handleViewDetail = (opp) => {
    navigate('/opportunities');
  };

  // 渲染机会卡片
  const renderOpportunityCard = (opp, stageIndex) => {
    const nextStage = Object.keys(STAGE_CONFIG)[stageIndex + 1];

    return (
      <Card
        key={opp.id}
        size="small"
        style={{
          marginBottom: 8,
          borderRadius: 8,
          borderLeft: `4px solid ${PRIORITY_COLORS[opp.priority] || '#1890ff'}`,
          cursor: 'pointer',
        }}
        bodyStyle={{ padding: '12px' }}
        hoverable
      >
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 14 }}>
            {opp.name}
          </div>
          <div style={{ fontSize: 12, color: '#666' }}>
            <UserOutlined style={{ marginRight: 4 }} />
            {opp.customer_name}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontWeight: 600, color: '#1890ff', fontSize: 16 }}>
            ¥{opp.expected_amount?.toLocaleString() || 0}
          </span>
          <Progress
            type="circle"
            percent={opp.probability}
            width={36}
            strokeColor={opp.probability >= 75 ? '#52c41a' : opp.probability >= 50 ? '#faad14' : '#1890ff'}
          />
        </div>

        {opp.expected_close_date && (
          <div style={{ fontSize: 12, color: '#999', marginBottom: 8 }}>
            <CalendarOutlined style={{ marginRight: 4 }} />
            预计成交: {dayjs(opp.expected_close_date).format('MM-DD')}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Tag color={PRIORITY_COLORS[opp.priority]} style={{ margin: 0 }}>
            {opp.priority === 'urgent' ? '紧急' : opp.priority === 'high' ? '高' : opp.priority === 'medium' ? '中' : '低'}
          </Tag>

          <Space size={4}>
            <Tooltip title="查看详情">
              <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(opp)} />
            </Tooltip>
            {nextStage && (
              <Tooltip title={`推进到 ${STAGE_CONFIG[nextStage]?.name}`}>
                <Button
                  size="small"
                  type="primary"
                  icon={<RightOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMoveStage(opp, nextStage);
                  }}
                />
              </Tooltip>
            )}
          </Space>
        </div>
      </Card>
    );
  };

  // 渲染阶段列
  const renderStageColumn = (stageData, index) => {
    const config = STAGE_CONFIG[stageData.stage];
    if (!config) return null;

    return (
      <Col xs={24} sm={12} lg={6} key={stageData.stage}>
        <Card
          style={{
            height: '100%',
            minHeight: 500,
            backgroundColor: config.bgColor,
            borderTop: `3px solid ${config.color}`,
          }}
          bodyStyle={{ padding: '12px' }}
        >
          {/* 阶段头部 */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Space>
                <span style={{ fontSize: 18 }}>{config.icon}</span>
                <span style={{ fontWeight: 600, fontSize: 16 }}>{config.name}</span>
                <Badge count={stageData.count} style={{ backgroundColor: config.color }} />
              </Space>
              <Tag color={config.color}>{stageData.probability}%</Tag>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#666' }}>
              <span>
                <DollarOutlined /> 总额: ¥{stageData.total_amount?.toLocaleString() || 0}
              </span>
            </div>
          </div>

          {/* 机会卡片列表 */}
          <div style={{ maxHeight: 'calc(100vh - 360px)', overflowY: 'auto' }}>
            {stageData.opportunities?.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无机会"
                style={{ padding: '40px 0' }}
              />
            ) : (
              stageData.opportunities?.map(opp => renderOpportunityCard(opp, index))
            )}
          </div>
        </Card>
      </Col>
    );
  };

  // 计算汇总数据
  const getSummary = () => {
    let totalCount = 0;
    let totalAmount = 0;
    let weightedAmount = 0;

    pipeline.forEach(stage => {
      totalCount += stage.count || 0;
      totalAmount += stage.total_amount || 0;
      const prob = stage.probability || 0;
      weightedAmount += (stage.total_amount || 0) * prob / 100;
    });

    return { totalCount, totalAmount, weightedAmount };
  };

  const summary = getSummary();

  return (
    <div>
      {/* 汇总统计 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={24}>
          <Col xs={12} sm={6}>
            <Statistic title="进行中机会" value={summary.totalCount} suffix="个" />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="总预计金额"
              value={summary.totalAmount}
              precision={0}
              prefix="¥"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="加权金额"
              value={summary.weightedAmount.toFixed(0)}
              precision={0}
              prefix="¥"
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={loadPipeline}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/opportunities')}>
                新建机会
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 漏斗看板 */}
      <Spin spinning={loading}>
        <Row gutter={16}>
          {pipeline.map((stageData, index) => renderStageColumn(stageData, index))}
        </Row>
      </Spin>

      {/* 成交/丢单区域 */}
      <Card title="已结束的机会" style={{ marginTop: 16 }} size="small">
        <Row gutter={16}>
          <Col span={12}>
            <div style={{ textAlign: 'center', padding: '20px 0', backgroundColor: '#f6ffed', borderRadius: 8 }}>
              <div style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }}>🎉</div>
              <div style={{ fontWeight: 600, color: '#52c41a' }}>已成交</div>
              <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                成交的机会不在看板显示，请在机会列表中查看
              </div>
            </div>
          </Col>
          <Col span={12}>
            <div style={{ textAlign: 'center', padding: '20px 0', backgroundColor: '#fff2f0', borderRadius: 8 }}>
              <div style={{ fontSize: 24, color: '#ff4d4f', marginBottom: 8 }}>😞</div>
              <div style={{ fontWeight: 600, color: '#ff4d4f' }}>已丢单</div>
              <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                丢单的机会不在看板显示，请在机会列表中查看
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 阶段变更确认弹窗 */}
      <Modal
        title="推进阶段"
        open={stageModalVisible}
        onOk={handleConfirmMove}
        onCancel={() => setStageModalVisible(false)}
        width={480}
      >
        <div style={{ marginBottom: 16 }}>
          <strong>机会:</strong> {selectedOpp?.name}
        </div>
        <div style={{ marginBottom: 16 }}>
          <strong>当前阶段:</strong>{' '}
          <Tag color={STAGE_CONFIG[selectedOpp?.stage]?.color}>
            {STAGE_CONFIG[selectedOpp?.stage]?.name}
          </Tag>
          <RightOutlined style={{ margin: '0 8px' }} />
          <Tag color={STAGE_CONFIG[targetStage]?.color}>
            {STAGE_CONFIG[targetStage]?.name}
          </Tag>
        </div>

        <Form form={form} layout="vertical">
          <Form.Item name="stage" label="目标阶段" rules={[{ required: true }]}>
            <Select>
              {stages.map(s => (
                <Select.Option key={s.value} value={s.value}>
                  {s.label} ({s.probability}%)
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="reason" label="变更原因">
            <TextArea rows={3} placeholder="请说明推进阶段的原因（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
