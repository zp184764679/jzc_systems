import { useState, useEffect } from 'react';
import { Card, Typography, Tag, Space, Button, Spin, Empty, List, Row, Col, Divider } from 'antd';
import { ArrowLeftOutlined, FileOutlined, DownloadOutlined, PrinterOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getDocument } from '../services/api';

const { Title, Text } = Typography;

// 文档类型名称映射
const docTypeNames = {
  SOP: { zh: '作业指导书', en: 'Work Instructions', ja: '作業手順書' },
  Notice: { zh: '通知公告', en: 'Notice', ja: 'お知らせ' },
  Manual: { zh: '操作手册', en: 'Manual', ja: 'マニュアル' },
  Other: { zh: '其他文档', en: 'Document', ja: 'その他' }
};

export default function DocumentView() {
  const { t, i18n } = useTranslation();
  const { slug } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocument = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDocument(slug, i18n.language);
      if (res.data.data && res.data.data.length > 0) {
        setDocument(res.data.data[0]);
      } else {
        setError('Document not found');
      }
    } catch (err) {
      console.error('Failed to fetch document:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocument();
    const handleLangChange = () => fetchDocument();
    window.addEventListener('langChange', handleLangChange);
    return () => window.removeEventListener('langChange', handleLangChange);
  }, [slug, i18n.language]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !document) {
    return (
      <Card>
        <Empty description={error || t('msg.noData')}>
          <Button onClick={() => navigate('/')}>{t('btn.back')}</Button>
        </Empty>
      </Card>
    );
  }

  const doc = document;
  const attachments = doc.attachments || [];
  const docTypeName = docTypeNames[doc.docType]?.[i18n.language] || doc.docType;
  const isSOP = doc.docType === 'SOP';
  const isMarkdown = doc.contentFormat === 'markdown';

  // 渲染内容 (支持 Markdown 和 HTML)
  const renderContent = (content) => {
    if (!content) return null;
    if (isMarkdown) {
      return (
        <ReactMarkdown remarkPlugins={[remarkGfm]} className="markdown-body">
          {content}
        </ReactMarkdown>
      );
    }
    return <div dangerouslySetInnerHTML={{ __html: content }} />;
  };

  // SOP 章节组件
  const SOPSection = ({ title, content, number }) => {
    if (!content) return null;
    return (
      <div className="sop-section">
        <Title level={4} className="sop-section-title">
          {number}. {title}
        </Title>
        <div className="sop-section-content">
          {isMarkdown ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          ) : (
            <Text style={{ whiteSpace: 'pre-wrap' }}>{content}</Text>
          )}
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* 工具栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }} className="no-print">
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          style={{ padding: 0 }}
        >
          {t('btn.back')}
        </Button>
        <Button icon={<PrinterOutlined />} onClick={handlePrint}>
          打印
        </Button>
      </div>

      {/* 文档容器 - A4 纸张样式 */}
      <div className="document-paper">
        {/* 文档头部 */}
        <div className="document-header">
          <Row justify="space-between" align="middle">
            <Col>
              <div className="company-name">JZC Hardware</div>
            </Col>
            <Col>
              <Tag color="blue" style={{ fontSize: 14, padding: '4px 12px' }}>
                {docTypeName}
              </Tag>
            </Col>
          </Row>
        </div>

        {/* 文档标题块 */}
        <div className="document-title-block">
          <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
            {doc.title}
          </Title>

          {/* 文档信息表格 */}
          <table className="document-info-table">
            <tbody>
              <tr>
                <td className="label">文档编号</td>
                <td>{doc.slug?.toUpperCase() || '-'}</td>
                <td className="label">版本</td>
                <td>{doc.version || '1.0'}</td>
              </tr>
              <tr>
                <td className="label">分类</td>
                <td>{doc.category?.name || '-'}</td>
                <td className="label">发布日期</td>
                <td>{doc.publishedDate || '-'}</td>
              </tr>
              {isSOP && (
                <>
                  <tr>
                    <td className="label">生效日期</td>
                    <td>{doc.effectiveDate || '-'}</td>
                    <td className="label">复审日期</td>
                    <td>{doc.reviewDate || '-'}</td>
                  </tr>
                  <tr>
                    <td className="label">编写人</td>
                    <td>{doc.author || '-'}</td>
                    <td className="label">审核人</td>
                    <td>{doc.reviewer || '-'}</td>
                  </tr>
                  <tr>
                    <td className="label">批准人</td>
                    <td colSpan={3}>{doc.approver || '-'}</td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        </div>

        {/* 摘要 */}
        {doc.summary && (
          <div className="document-summary">
            <Text strong>摘要：</Text>
            <Text>{doc.summary}</Text>
          </div>
        )}

        {/* SOP 模板内容 */}
        {isSOP ? (
          <div className="document-body sop-body">
            <SOPSection number="1" title="目的" content={doc.sopPurpose} />
            <SOPSection number="2" title="适用范围" content={doc.sopScope} />
            <SOPSection number="3" title="定义" content={doc.sopDefinitions} />
            <SOPSection number="4" title="职责" content={doc.sopResponsibilities} />
            <SOPSection number="5" title="操作步骤" content={doc.sopProcedure} />
            <SOPSection number="6" title="安全注意事项" content={doc.sopSafetyNotes} />
            <SOPSection number="7" title="参考文档" content={doc.sopReferences} />

            {/* 如果还有额外的 content 字段内容 */}
            {(doc.content || doc.markdownContent) && (
              <>
                <Divider />
                <div className="sop-extra-content">
                  {renderContent(isMarkdown ? doc.markdownContent : doc.content)}
                </div>
              </>
            )}
          </div>
        ) : (
          /* 普通文档内容 */
          <div className="document-body">
            {renderContent(isMarkdown ? doc.markdownContent : doc.content)}
          </div>
        )}

        {/* 附件列表 */}
        {attachments.length > 0 && (
          <div className="document-attachments">
            <Title level={4}>{t('doc.attachments')}</Title>
            <List
              size="small"
              bordered
              dataSource={attachments}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      type="link"
                      icon={<DownloadOutlined />}
                      href={item.url}
                      target="_blank"
                      key="download"
                    >
                      下载
                    </Button>
                  ]}
                >
                  <Space>
                    <FileOutlined />
                    {item.name}
                  </Space>
                </List.Item>
              )}
            />
          </div>
        )}

        {/* 文档页脚 */}
        <div className="document-footer">
          <Row justify="space-between">
            <Col>
              <Text type="secondary">文档编号: {doc.slug?.toUpperCase()}</Text>
            </Col>
            <Col>
              <Text type="secondary">版本 {doc.version || '1.0'}</Text>
            </Col>
            <Col>
              <Text type="secondary">第 1 页</Text>
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
}
