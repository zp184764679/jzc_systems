/**
 * 技术规格面板组件
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  message, Empty, Descriptions, Tooltip, Row, Col, Select
} from 'antd';
import {
  PlusOutlined, EditOutlined, HistoryOutlined, SaveOutlined
} from '@ant-design/icons';
import { techSpecAPI } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

function TechSpecPanel({ productId, partNumber }) {
  const [specs, setSpecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [editingSpec, setEditingSpec] = useState(null);
  const [versions, setVersions] = useState([]);
  const [form] = Form.useForm();

  // 加载技术规格
  const loadSpecs = async () => {
    setLoading(true);
    try {
      const response = await techSpecAPI.getByProduct(productId, false);
      if (response.success) {
        setSpecs(response.data || []);
      }
    } catch (error) {
      message.error('加载技术规格失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      loadSpecs();
    }
  }, [productId]);

  // 获取当前版本
  const currentSpec = specs.find(s => s.is_current) || specs[0];

  // 新建/编辑
  const handleEdit = (spec = null) => {
    setEditingSpec(spec);
    if (spec) {
      form.setFieldsValue(spec);
    } else {
      form.resetFields();
      form.setFieldsValue({ part_number: partNumber });
    }
    setModalVisible(true);
  };

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      if (editingSpec) {
        await techSpecAPI.update(editingSpec.id, values);
        message.success('更新成功');
      } else {
        await techSpecAPI.create(productId, values);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadSpecs();
    } catch (error) {
      if (error.errorFields) return;
      message.error(error.error || '保存失败');
    }
  };

  // 创建新版本
  const handleNewVersion = async () => {
    if (!currentSpec) return;

    Modal.confirm({
      title: '创建新版本',
      content: '确定要基于当前版本创建新版本吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await techSpecAPI.createVersion(currentSpec.id, {
            version_note: '基于上一版本创建'
          });
          message.success('新版本创建成功');
          loadSpecs();
        } catch (error) {
          message.error('创建新版本失败');
        }
      }
    });
  };

  // 查看版本历史
  const handleViewHistory = async () => {
    if (!currentSpec) return;

    try {
      const response = await techSpecAPI.getVersions(currentSpec.id);
      if (response.success) {
        setVersions(response.data || []);
        setHistoryVisible(true);
      }
    } catch (error) {
      message.error('加载版本历史失败');
    }
  };

  // 版本历史列
  const versionColumns = [
    { title: '版本', dataIndex: 'version', width: 80 },
    {
      title: '当前',
      dataIndex: 'is_current',
      width: 60,
      render: (v) => v ? <Tag color="green">是</Tag> : '-'
    },
    { title: '备注', dataIndex: 'version_note', ellipsis: true },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      render: (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'
    }
  ];

  if (!currentSpec && !loading) {
    return (
      <Card size="small">
        <Empty description="暂无技术规格">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleEdit()}>
            添加技术规格
          </Button>
        </Empty>

        {/* 编辑弹窗 */}
        <Modal
          title="添加技术规格"
          open={modalVisible}
          onOk={handleSave}
          onCancel={() => setModalVisible(false)}
          width={800}
          okText="保存"
          cancelText="取消"
        >
          {renderForm()}
        </Modal>
      </Card>
    );
  }

  function renderForm() {
    return (
      <Form form={form} layout="vertical">
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="part_number" label="品番号">
              <Input disabled />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="material_code" label="材料编码">
              <Input placeholder="材料编码" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="material_name" label="材料名称">
              <Input placeholder="材料名称" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="material_spec" label="材料规格">
              <Input placeholder="材料规格" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="density" label="密度 (g/cm³)">
              <InputNumber style={{ width: '100%' }} precision={4} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="weight" label="重量 (kg)">
              <InputNumber style={{ width: '100%' }} precision={4} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="outer_diameter" label="外径 (mm)">
              <InputNumber style={{ width: '100%' }} precision={4} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="length" label="长度 (mm)">
              <InputNumber style={{ width: '100%' }} precision={4} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="tolerance_class" label="公差等级">
              <Input placeholder="如: IT6" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="surface_roughness" label="表面粗糙度 (Ra)">
              <Input placeholder="如: Ra0.8" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="heat_treatment" label="热处理">
              <Input placeholder="热处理要求" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="surface_treatment" label="表面处理">
              <Input placeholder="表面处理要求" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="special_requirements" label="特殊要求">
          <TextArea rows={3} placeholder="其他特殊要求" />
        </Form.Item>
      </Form>
    );
  }

  return (
    <div>
      {/* 工具栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Tag color="blue">当前版本: v{currentSpec?.version || '1.0'}</Tag>
        </Space>
        <Space>
          <Button icon={<HistoryOutlined />} onClick={handleViewHistory}>
            版本历史
          </Button>
          <Button icon={<PlusOutlined />} onClick={handleNewVersion}>
            新建版本
          </Button>
          <Button type="primary" icon={<EditOutlined />} onClick={() => handleEdit(currentSpec)}>
            编辑
          </Button>
        </Space>
      </div>

      {/* 规格详情 */}
      <Card size="small" loading={loading}>
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
          <Descriptions.Item label="材料编码">{currentSpec?.material_code || '-'}</Descriptions.Item>
          <Descriptions.Item label="材料名称">{currentSpec?.material_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="材料规格">{currentSpec?.material_spec || '-'}</Descriptions.Item>
          <Descriptions.Item label="密度">{currentSpec?.density ? `${currentSpec.density} g/cm³` : '-'}</Descriptions.Item>
          <Descriptions.Item label="外径">{currentSpec?.outer_diameter ? `${currentSpec.outer_diameter} mm` : '-'}</Descriptions.Item>
          <Descriptions.Item label="长度">{currentSpec?.length ? `${currentSpec.length} mm` : '-'}</Descriptions.Item>
          <Descriptions.Item label="重量">{currentSpec?.weight ? `${currentSpec.weight} kg` : '-'}</Descriptions.Item>
          <Descriptions.Item label="公差等级">{currentSpec?.tolerance_class || '-'}</Descriptions.Item>
          <Descriptions.Item label="表面粗糙度">{currentSpec?.surface_roughness || '-'}</Descriptions.Item>
          <Descriptions.Item label="热处理">{currentSpec?.heat_treatment || '-'}</Descriptions.Item>
          <Descriptions.Item label="表面处理">{currentSpec?.surface_treatment || '-'}</Descriptions.Item>
          <Descriptions.Item label="特殊要求" span={3}>{currentSpec?.special_requirements || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 编辑弹窗 */}
      <Modal
        title={editingSpec ? '编辑技术规格' : '添加技术规格'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        {renderForm()}
      </Modal>

      {/* 版本历史弹窗 */}
      <Modal
        title="版本历史"
        open={historyVisible}
        onCancel={() => setHistoryVisible(false)}
        footer={null}
        width={600}
      >
        <Table
          columns={versionColumns}
          dataSource={versions}
          rowKey="id"
          size="small"
          pagination={false}
        />
      </Modal>
    </div>
  );
}

export default TechSpecPanel;
