/**
 * 工艺文件面板组件
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  message, Empty, Tooltip
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, HistoryOutlined,
  MenuOutlined
} from '@ant-design/icons';
import { processAPI } from '../services/api';

const { TextArea } = Input;

function ProcessPanel({ productId, partNumber }) {
  const [processes, setProcesses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProcess, setEditingProcess] = useState(null);
  const [form] = Form.useForm();

  // 加载工艺文件
  const loadProcesses = async () => {
    setLoading(true);
    try {
      const response = await processAPI.getByProduct(productId, false);
      if (response.success) {
        // 按工序顺序排序
        const sorted = (response.data || []).sort((a, b) =>
          (a.process_sequence || 0) - (b.process_sequence || 0)
        );
        setProcesses(sorted);
      }
    } catch (error) {
      message.error('加载工艺文件失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      loadProcesses();
    }
  }, [productId]);

  // 新建/编辑
  const handleEdit = (process = null) => {
    setEditingProcess(process);
    if (process) {
      form.setFieldsValue(process);
    } else {
      form.resetFields();
      form.setFieldsValue({
        part_number: partNumber,
        process_sequence: processes.length + 1
      });
    }
    setModalVisible(true);
  };

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      if (editingProcess) {
        await processAPI.update(editingProcess.id, values);
        message.success('更新成功');
      } else {
        await processAPI.create(productId, values);
        message.success('创建成功');
      }

      setModalVisible(false);
      loadProcesses();
    } catch (error) {
      if (error.errorFields) return;
      message.error(error.error || '保存失败');
    }
  };

  // 删除
  const handleDelete = (process) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除工艺 "${process.process_name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await processAPI.delete(process.id);
          message.success('删除成功');
          loadProcesses();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 创建新版本
  const handleNewVersion = async (process) => {
    Modal.confirm({
      title: '创建新版本',
      content: `确定要为 "${process.process_name}" 创建新版本吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await processAPI.createVersion(process.id, {
            version_note: '基于上一版本创建'
          });
          message.success('新版本创建成功');
          loadProcesses();
        } catch (error) {
          message.error('创建新版本失败');
        }
      }
    });
  };

  // 表格列
  const columns = [
    {
      title: '序号',
      dataIndex: 'process_sequence',
      width: 60,
      render: (seq) => seq || '-'
    },
    {
      title: '工艺编码',
      dataIndex: 'process_code',
      width: 100
    },
    {
      title: '工艺名称',
      dataIndex: 'process_name',
      ellipsis: true
    },
    {
      title: '设备类型',
      dataIndex: 'machine_type',
      width: 120
    },
    {
      title: '设备型号',
      dataIndex: 'machine_model',
      width: 120
    },
    {
      title: '准备时间',
      dataIndex: 'setup_time',
      width: 90,
      render: (t) => t ? `${t} 分` : '-'
    },
    {
      title: '加工周期',
      dataIndex: 'cycle_time',
      width: 90,
      render: (t) => t ? `${t} 分` : '-'
    },
    {
      title: '版本',
      dataIndex: 'version',
      width: 60,
      render: (v, record) => (
        <Space>
          <span>v{v}</span>
          {record.is_current && <Tag color="green" style={{ marginLeft: 0 }}>当前</Tag>}
        </Space>
      )
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
          <Tooltip title="新版本">
            <Button
              type="link"
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => handleNewVersion(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  if (processes.length === 0 && !loading) {
    return (
      <Card size="small">
        <Empty description="暂无工艺文件">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleEdit()}>
            添加工艺
          </Button>
        </Empty>

        {/* 编辑弹窗 */}
        <Modal
          title="添加工艺"
          open={modalVisible}
          onOk={handleSave}
          onCancel={() => setModalVisible(false)}
          width={700}
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
        <Form.Item name="part_number" label="品番号" hidden>
          <Input />
        </Form.Item>

        <Form.Item
          name="process_sequence"
          label="工序顺序"
          rules={[{ required: true, message: '请输入工序顺序' }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="process_code" label="工艺编码">
          <Input placeholder="如: OP010" />
        </Form.Item>

        <Form.Item
          name="process_name"
          label="工艺名称"
          rules={[{ required: true, message: '请输入工艺名称' }]}
        >
          <Input placeholder="工艺名称" />
        </Form.Item>

        <Form.Item name="machine_type" label="设备类型">
          <Input placeholder="如: 数控车床" />
        </Form.Item>

        <Form.Item name="machine_model" label="设备型号">
          <Input placeholder="如: CK6140" />
        </Form.Item>

        <Form.Item name="setup_time" label="准备时间 (分钟)">
          <InputNumber min={0} precision={2} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="cycle_time" label="加工周期 (分钟)">
          <InputNumber min={0} precision={2} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    );
  }

  return (
    <div>
      {/* 工具栏 */}
      <div style={{ marginBottom: 16, textAlign: 'right' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => handleEdit()}>
          添加工艺
        </Button>
      </div>

      {/* 工艺表格 */}
      <Table
        columns={columns}
        dataSource={processes}
        rowKey="id"
        size="small"
        loading={loading}
        pagination={false}
      />

      {/* 编辑弹窗 */}
      <Modal
        title={editingProcess ? '编辑工艺' : '添加工艺'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={700}
        okText="保存"
        cancelText="取消"
      >
        {renderForm()}
      </Modal>
    </div>
  );
}

export default ProcessPanel;
