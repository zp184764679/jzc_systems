import { useState, useEffect } from 'react';
import { Table, Card, Input, Select, Tag, Space, Button, Empty, Spin } from 'antd';
import { SearchOutlined, FileTextOutlined, EyeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { getDocuments, getCategories } from '../services/api';

const { Search } = Input;

// 文档类型颜色映射
const typeColors = {
  SOP: 'blue',
  Notice: 'orange',
  Manual: 'green',
  Other: 'default'
};

export default function DocumentList() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    category: null,
    docType: null,
    keyword: ''
  });

  // 获取数据
  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.category) {
        params.filters = { ...params.filters, category: { id: { $eq: filters.category } } };
      }
      if (filters.docType) {
        params.filters = { ...params.filters, docType: { $eq: filters.docType } };
      }
      if (filters.keyword) {
        params.filters = {
          ...params.filters,
          $or: [
            { title: { $containsi: filters.keyword } },
            { summary: { $containsi: filters.keyword } }
          ]
        };
      }

      const [docsRes, catsRes] = await Promise.all([
        getDocuments(i18n.language, params),
        getCategories(i18n.language)
      ]);

      setDocuments(docsRes.data.data || []);
      setCategories(catsRes.data.data || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // 监听语言切换
    const handleLangChange = () => fetchData();
    window.addEventListener('langChange', handleLangChange);
    return () => window.removeEventListener('langChange', handleLangChange);
  }, [i18n.language, filters]);

  // 表格列定义 (Strapi 5 扁平数据结构)
  const columns = [
    {
      title: t('doc.title'),
      dataIndex: 'title',
      key: 'title',
      render: (text) => (
        <Space>
          <FileTextOutlined />
          <span style={{ fontWeight: 500 }}>{text}</span>
        </Space>
      )
    },
    {
      title: t('doc.type'),
      dataIndex: 'docType',
      key: 'docType',
      width: 120,
      render: (type) => (
        <Tag color={typeColors[type] || 'default'}>
          {t(`doc.type.${type}`)}
        </Tag>
      )
    },
    {
      title: t('doc.category'),
      dataIndex: ['category', 'name'],
      key: 'category',
      width: 150,
    },
    {
      title: t('doc.version'),
      dataIndex: 'version',
      key: 'version',
      width: 100,
    },
    {
      title: t('doc.date'),
      dataIndex: 'publishedDate',
      key: 'publishedDate',
      width: 120,
    },
    {
      title: t('doc.summary'),
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
    },
    {
      title: '',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/view/${record.slug || record.documentId}`)}
        >
          {t('btn.view')}
        </Button>
      )
    }
  ];

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          {t('nav.documents')}
        </Space>
      }
      extra={
        <Space>
          <Search
            placeholder={t('search.placeholder')}
            allowClear
            onSearch={(value) => setFilters(f => ({ ...f, keyword: value }))}
            style={{ width: 200 }}
          />
          <Select
            placeholder={t('filter.category')}
            allowClear
            style={{ width: 150 }}
            value={filters.category}
            onChange={(value) => setFilters(f => ({ ...f, category: value }))}
            options={categories.map(cat => ({
              value: cat.id,
              label: cat.name
            }))}
          />
          <Select
            placeholder={t('filter.type')}
            allowClear
            style={{ width: 120 }}
            value={filters.docType}
            onChange={(value) => setFilters(f => ({ ...f, docType: value }))}
            options={[
              { value: 'SOP', label: t('doc.type.SOP') },
              { value: 'Notice', label: t('doc.type.Notice') },
              { value: 'Manual', label: t('doc.type.Manual') },
              { value: 'Other', label: t('doc.type.Other') }
            ]}
          />
        </Space>
      }
    >
      <Spin spinning={loading}>
        {documents.length > 0 ? (
          <Table
            columns={columns}
            dataSource={documents}
            rowKey="id"
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `${total} ${t('nav.documents')}`
            }}
          />
        ) : (
          <Empty description={t('msg.noData')} />
        )}
      </Spin>
    </Card>
  );
}
