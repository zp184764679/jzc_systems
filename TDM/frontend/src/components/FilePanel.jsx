/**
 * 文件管理面板组件
 */
import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, Select,
  message, Empty, Tooltip, Upload, Tabs
} from 'antd';
import {
  PlusOutlined, LinkOutlined, DeleteOutlined, DownloadOutlined,
  FileOutlined, FilePdfOutlined, FileImageOutlined, FileExcelOutlined,
  FileWordOutlined, FolderOutlined
} from '@ant-design/icons';
import { fileAPI } from '../services/api';

const { Option } = Select;

// 文件类型配置
const fileTypeConfig = {
  drawing: { label: '图纸', color: 'blue', icon: <FileOutlined /> },
  specification: { label: '规格书', color: 'green', icon: <FilePdfOutlined /> },
  inspection_standard: { label: '检验标准', color: 'orange', icon: <FileOutlined /> },
  work_instruction: { label: '作业指导书', color: 'purple', icon: <FileWordOutlined /> },
  process_sheet: { label: '工艺单', color: 'cyan', icon: <FileExcelOutlined /> },
  photo: { label: '照片', color: 'pink', icon: <FileImageOutlined /> },
  other: { label: '其他', color: 'default', icon: <FileOutlined /> }
};

function FilePanel({ productId, partNumber }) {
  const [files, setFiles] = useState([]);
  const [filesByType, setFilesByType] = useState({});
  const [loading, setLoading] = useState(false);
  const [linkModalVisible, setLinkModalVisible] = useState(false);
  const [activeType, setActiveType] = useState('all');
  const [form] = Form.useForm();

  // 加载文件
  const loadFiles = async () => {
    setLoading(true);
    try {
      const [listRes, typeRes] = await Promise.all([
        fileAPI.getByProduct(productId),
        fileAPI.getByType(productId)
      ]);

      if (listRes.success) {
        setFiles(listRes.data || []);
      }
      if (typeRes.success) {
        setFilesByType(typeRes.data || {});
      }
    } catch (error) {
      message.error('加载文件失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      loadFiles();
    }
  }, [productId]);

  // 关联文件
  const handleLink = () => {
    form.resetFields();
    form.setFieldsValue({
      part_number: partNumber,
      file_type: 'drawing'
    });
    setLinkModalVisible(true);
  };

  // 提交关联
  const handleLinkSubmit = async () => {
    try {
      const values = await form.validateFields();

      await fileAPI.linkFile(productId, values);
      message.success('关联成功');
      setLinkModalVisible(false);
      loadFiles();
    } catch (error) {
      if (error.errorFields) return;
      message.error(error.error || '关联失败');
    }
  };

  // 取消关联
  const handleUnlink = (file) => {
    Modal.confirm({
      title: '确认取消关联',
      content: `确定要取消关联文件 "${file.file_name || file.original_filename}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await fileAPI.unlinkFile(productId, file.id);
          message.success('取消关联成功');
          loadFiles();
        } catch (error) {
          message.error('取消关联失败');
        }
      }
    });
  };

  // 获取文件图标
  const getFileIcon = (filename) => {
    if (!filename) return <FileOutlined />;
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
      case 'doc':
      case 'docx': return <FileWordOutlined style={{ color: '#1890ff' }} />;
      case 'xls':
      case 'xlsx': return <FileExcelOutlined style={{ color: '#52c41a' }} />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif': return <FileImageOutlined style={{ color: '#722ed1' }} />;
      default: return <FileOutlined />;
    }
  };

  // 表格列
  const columns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      ellipsis: true,
      render: (name, record) => (
        <Space>
          {getFileIcon(name || record.original_filename)}
          <span>{name || record.original_filename || '-'}</span>
        </Space>
      )
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      width: 120,
      render: (type) => {
        const config = fileTypeConfig[type] || { label: type, color: 'default' };
        return <Tag color={config.color}>{config.label}</Tag>;
      }
    },
    {
      title: '是否主文件',
      dataIndex: 'is_primary',
      width: 100,
      render: (isPrimary) => isPrimary ? <Tag color="green">主文件</Tag> : '-'
    },
    {
      title: '关联时间',
      dataIndex: 'linked_at',
      width: 160,
      render: (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'
    },
    {
      title: '操作',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="取消关联">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleUnlink(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 过滤文件
  const filteredFiles = activeType === 'all'
    ? files
    : files.filter(f => f.file_type === activeType);

  // Tab 项
  const tabItems = [
    {
      key: 'all',
      label: (
        <span>
          <FolderOutlined /> 全部
          <Tag style={{ marginLeft: 8 }}>{files.length}</Tag>
        </span>
      )
    },
    ...Object.entries(fileTypeConfig).map(([key, config]) => {
      const count = filesByType[key]?.length || 0;
      return {
        key,
        label: (
          <span>
            {config.icon} {config.label}
            <Tag style={{ marginLeft: 8 }}>{count}</Tag>
          </span>
        )
      };
    })
  ];

  if (files.length === 0 && !loading) {
    return (
      <Card size="small">
        <Empty description="暂无关联文件">
          <Button type="primary" icon={<LinkOutlined />} onClick={handleLink}>
            关联文件
          </Button>
        </Empty>

        {/* 关联弹窗 */}
        <Modal
          title="关联文件"
          open={linkModalVisible}
          onOk={handleLinkSubmit}
          onCancel={() => setLinkModalVisible(false)}
          width={500}
          okText="关联"
          cancelText="取消"
        >
          {renderLinkForm()}
        </Modal>
      </Card>
    );
  }

  function renderLinkForm() {
    return (
      <Form form={form} layout="vertical">
        <Form.Item name="part_number" label="品番号" hidden>
          <Input />
        </Form.Item>

        <Form.Item
          name="file_index_id"
          label="文件ID (FileIndex)"
          rules={[{ required: true, message: '请输入文件ID' }]}
          extra="请在文件中心查找对应文件的ID"
        >
          <Input placeholder="输入 FileIndex 中的文件ID" />
        </Form.Item>

        <Form.Item
          name="file_type"
          label="文件类型"
          rules={[{ required: true }]}
        >
          <Select>
            {Object.entries(fileTypeConfig).map(([key, config]) => (
              <Option key={key} value={key}>{config.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="is_primary" label="是否主文件" initialValue={false}>
          <Select>
            <Option value={true}>是</Option>
            <Option value={false}>否</Option>
          </Select>
        </Form.Item>

        <Form.Item name="display_order" label="显示顺序">
          <Input type="number" placeholder="0" />
        </Form.Item>
      </Form>
    );
  }

  return (
    <div>
      {/* 工具栏 */}
      <div style={{ marginBottom: 16, textAlign: 'right' }}>
        <Button type="primary" icon={<LinkOutlined />} onClick={handleLink}>
          关联文件
        </Button>
      </div>

      {/* 文件类型 Tabs */}
      <Tabs
        activeKey={activeType}
        onChange={setActiveType}
        items={tabItems}
        size="small"
      />

      {/* 文件表格 */}
      <Table
        columns={columns}
        dataSource={filteredFiles}
        rowKey="id"
        size="small"
        loading={loading}
        pagination={false}
      />

      {/* 关联弹窗 */}
      <Modal
        title="关联文件"
        open={linkModalVisible}
        onOk={handleLinkSubmit}
        onCancel={() => setLinkModalVisible(false)}
        width={500}
        okText="关联"
        cancelText="取消"
      >
        {renderLinkForm()}
      </Modal>
    </div>
  );
}

export default FilePanel;
