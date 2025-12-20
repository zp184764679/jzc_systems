/**
 * 产品详情页面
 */
import { useState, useEffect } from 'react';
import {
  Card, Tabs, Descriptions, Button, Space, Tag, Spin, message, Empty, Row, Col, Typography, Divider
} from 'antd';
import {
  ArrowLeftOutlined, EditOutlined, FileTextOutlined, SafetyCertificateOutlined,
  ToolOutlined, FolderOutlined, HistoryOutlined
} from '@ant-design/icons';
import { productAPI, techSpecAPI, inspectionAPI, processAPI, fileAPI } from '../services/api';

// 子组件
import TechSpecPanel from '../components/TechSpecPanel';
import InspectionPanel from '../components/InspectionPanel';
import ProcessPanel from '../components/ProcessPanel';
import FilePanel from '../components/FilePanel';

const { Title, Text } = Typography;

// 状态标签
const statusLabels = {
  draft: { text: '草稿', color: 'default' },
  active: { text: '生效中', color: 'success' },
  discontinued: { text: '已停产', color: 'warning' },
  obsolete: { text: '已废弃', color: 'error' }
};

function ProductDetail({ productId, onBack }) {
  const [loading, setLoading] = useState(true);
  const [product, setProduct] = useState(null);
  const [activeTab, setActiveTab] = useState('info');

  // 加载产品详情
  const loadProduct = async () => {
    setLoading(true);
    try {
      const response = await productAPI.getById(productId, true);
      if (response.success) {
        setProduct(response.data);
      } else {
        message.error('加载产品信息失败');
      }
    } catch (error) {
      message.error('加载产品信息失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      loadProduct();
    }
  }, [productId]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!product) {
    return (
      <Card>
        <Empty description="产品不存在" />
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button onClick={onBack}>返回列表</Button>
        </div>
      </Card>
    );
  }

  const statusInfo = statusLabels[product.status] || { text: product.status, color: 'default' };

  // Tab 项
  const tabItems = [
    {
      key: 'info',
      label: (
        <span>
          <FileTextOutlined />
          基本信息
        </span>
      ),
      children: (
        <Card size="small">
          <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
            <Descriptions.Item label="品番号">{product.part_number}</Descriptions.Item>
            <Descriptions.Item label="产品名称">{product.product_name}</Descriptions.Item>
            <Descriptions.Item label="英文名称">{product.product_name_en || '-'}</Descriptions.Item>
            <Descriptions.Item label="客户名称">{product.customer_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="客户料号">{product.customer_part_number || '-'}</Descriptions.Item>
            <Descriptions.Item label="产品分类">{product.category || '-'}</Descriptions.Item>
            <Descriptions.Item label="子分类">{product.sub_category || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前版本">v{product.current_version}</Descriptions.Item>
            <Descriptions.Item label="创建人">{product.created_by_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {product.created_at ? new Date(product.created_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {product.updated_at ? new Date(product.updated_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="产品描述" span={3}>
              {product.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={3}>
              {product.remarks || '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )
    },
    {
      key: 'tech-spec',
      label: (
        <span>
          <FileTextOutlined />
          技术规格
        </span>
      ),
      children: <TechSpecPanel productId={productId} partNumber={product.part_number} />
    },
    {
      key: 'inspection',
      label: (
        <span>
          <SafetyCertificateOutlined />
          检验标准
        </span>
      ),
      children: <InspectionPanel productId={productId} partNumber={product.part_number} />
    },
    {
      key: 'process',
      label: (
        <span>
          <ToolOutlined />
          工艺文件
        </span>
      ),
      children: <ProcessPanel productId={productId} partNumber={product.part_number} />
    },
    {
      key: 'files',
      label: (
        <span>
          <FolderOutlined />
          相关文件
        </span>
      ),
      children: <FilePanel productId={productId} partNumber={product.part_number} />
    }
  ];

  return (
    <div>
      {/* 页头 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
                返回
              </Button>
              <Divider type="vertical" />
              <Title level={4} style={{ margin: 0 }}>
                {product.part_number}
              </Title>
              <Text type="secondary">{product.product_name}</Text>
              <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<HistoryOutlined />}>
                版本历史
              </Button>
              <Button type="primary" icon={<EditOutlined />}>
                编辑
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 详情 Tabs */}
      <Card size="small">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="small"
        />
      </Card>
    </div>
  );
}

export default ProductDetail;
