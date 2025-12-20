/**
 * 检验标准面板组件
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  message, Empty, Select, Tabs, Tooltip
} from 'antd';
import {
  PlusOutlined, EditOutlined, HistoryOutlined, CheckCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { inspectionAPI } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

// 检验阶段配置
const stageConfig = {
  incoming: { label: 'IQC 来料检验', color: 'blue' },
  process: { label: 'IPQC 过程检验', color: 'cyan' },
  final: { label: 'FQC 最终检验', color: 'green' },
  outgoing: { label: 'OQC 出货检验', color: 'orange' }
};

// 状态配置
const statusConfig = {
  draft: { label: '草稿', color: 'default' },
  active: { label: '生效中', color: 'success' },
  deprecated: { label: '已废弃', color: 'error' }
};

function InspectionPanel({ productId, partNumber }) {
  const [criteria, setCriteria] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [activeStage, setActiveStage] = useState('incoming');
  const [form] = Form.useForm();

  // 加载检验标准
  const loadCriteria = async () => {
    setLoading(true);
    try {
      const response = await inspectionAPI.getByProduct(productId, { current_only: false });
      if (response.success) {
        setCriteria(response.data || []);
      }
    } catch (error) {
      message.error('加载检验标准失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      loadCriteria();
    }
  }, [productId]);

  // 按阶段分组
  const criteriaByStage = {
    incoming: criteria.filter(c => c.inspection_stage === 'incoming'),
    process: criteria.filter(c => c.inspection_stage === 'process'),
    final: criteria.filter(c => c.inspection_stage === 'final'),
    outgoing: criteria.filter(c => c.inspection_stage === 'outgoing')
  };

  // 新建/编辑
  const handleEdit = (item = null) => {
    setEditingItem(item);
    if (item) {
      form.setFieldsValue(item);
    } else {
      form.resetFields();
      form.setFieldsValue({
        part_number: partNumber,
        inspection_stage: activeStage,
        inspection_method: 'sampling',
        status: 'draft'
      });
    }
    setModalVisible(true);
  };

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      if (editingItem) {
        await inspectionAPI.update(editingItem.id, values);
        message.success('更新成功');
      } else {
        await inspectionAPI.create(productId, values);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadCriteria();
    } catch (error) {
      if (error.errorFields) return;
      message.error(error.error || '保存失败');
    }
  };

  // 审批
  const handleApprove = async (item) => {
    Modal.confirm({
      title: '确认审批',
      content: `确定要审批通过 "${item.criteria_name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await inspectionAPI.approve(item.id);
          message.success('审批成功');
          loadCriteria();
        } catch (error) {
          message.error('审批失败');
        }
      }
    });
  };

  // 表格列
  const columns = [
    {
      title: '标准编码',
      dataIndex: 'criteria_code',
      width: 120
    },
    {
      title: '标准名称',
      dataIndex: 'criteria_name',
      ellipsis: true
    },
    {
      title: '检验方式',
      dataIndex: 'inspection_method',
      width: 100,
      render: (method) => {
        const methods = { full: '全检', sampling: '抽检', skip: '免检' };
        return methods[method] || method;
      }
    },
    {
      title: '抽样方案',
      dataIndex: 'sampling_plan',
      width: 120
    },
    {
      title: '版本',
      dataIndex: 'version',
      width: 60,
      render: (v) => `v${v}`
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status) => {
        const config = statusConfig[status] || { label: status, color: 'default' };
        return <Tag color={config.color}>{config.label}</Tag>;
      }
    },
    {
      title: '操作',
      width: 140,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {record.status === 'draft' && (
            <Tooltip title="审批">
              <Button
                type="link"
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => handleApprove(record)}
              />
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 渲染阶段内容
  const renderStageContent = (stage) => {
    const stageData = criteriaByStage[stage] || [];

    if (stageData.length === 0) {
      return (
        <Empty description="暂无检验标准">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleEdit()}>
            添加检验标准
          </Button>
        </Empty>
      );
    }

    return (
      <div>
        <div style={{ marginBottom: 16, textAlign: 'right' }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleEdit()}>
            添加
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={stageData}
          rowKey="id"
          size="small"
          pagination={false}
          loading={loading}
        />
      </div>
    );
  };

  // Tab 项
  const tabItems = Object.entries(stageConfig).map(([key, config]) => ({
    key,
    label: (
      <span>
        {config.label}
        <Tag style={{ marginLeft: 8 }}>{criteriaByStage[key]?.length || 0}</Tag>
      </span>
    ),
    children: renderStageContent(key)
  }));

  return (
    <div>
      <Tabs
        activeKey={activeStage}
        onChange={setActiveStage}
        items={tabItems}
        size="small"
      />

      {/* 编辑弹窗 */}
      <Modal
        title={editingItem ? '编辑检验标准' : '添加检验标准'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={700}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="part_number" label="品番号" hidden>
            <Input />
          </Form.Item>

          <Form.Item
            name="criteria_code"
            label="标准编码"
            rules={[{ required: true, message: '请输入标准编码' }]}
          >
            <Input placeholder="如: IQC-001" />
          </Form.Item>

          <Form.Item
            name="criteria_name"
            label="标准名称"
            rules={[{ required: true, message: '请输入标准名称' }]}
          >
            <Input placeholder="检验标准名称" />
          </Form.Item>

          <Form.Item
            name="inspection_stage"
            label="检验阶段"
            rules={[{ required: true }]}
          >
            <Select>
              {Object.entries(stageConfig).map(([key, config]) => (
                <Option key={key} value={key}>{config.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="inspection_method" label="检验方式">
            <Select>
              <Option value="full">全检</Option>
              <Option value="sampling">抽检</Option>
              <Option value="skip">免检</Option>
            </Select>
          </Form.Item>

          <Form.Item name="sampling_plan" label="抽样方案">
            <Input placeholder="如: AQL 1.0 Level II" />
          </Form.Item>

          <Form.Item label="AQL 标准">
            <Space>
              <Form.Item name="aql_critical" noStyle>
                <InputNumber placeholder="严重" style={{ width: 100 }} />
              </Form.Item>
              <span>严重</span>
              <Form.Item name="aql_major" noStyle>
                <InputNumber placeholder="主要" style={{ width: 100 }} />
              </Form.Item>
              <span>主要</span>
              <Form.Item name="aql_minor" noStyle>
                <InputNumber placeholder="次要" style={{ width: 100 }} />
              </Form.Item>
              <span>次要</span>
            </Space>
          </Form.Item>

          <Form.Item name="status" label="状态">
            <Select>
              <Option value="draft">草稿</Option>
              <Option value="active">生效中</Option>
              <Option value="deprecated">已废弃</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default InspectionPanel;
