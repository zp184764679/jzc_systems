import React from 'react'
import {
  Card,
  Descriptions,
  Button,
  Space,
  message,
  Spin,
  Alert,
  Table,
  Row,
  Col,
  Divider,
  Tag,
} from 'antd'
import {
  ArrowLeftOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getQuote, exportQuoteExcel, exportQuotePDF } from '../services/api'

function QuoteDetail() {
  const { quoteId } = useParams()
  const navigate = useNavigate()

  // 查询报价详情
  const { data: quote, isLoading } = useQuery({
    queryKey: ['quote', quoteId],
    queryFn: () => getQuote(quoteId),
    enabled: !!quoteId,
  })

  // 导出Excel
  const handleExportExcel = async () => {
    try {
      const blob = await exportQuoteExcel(quoteId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `报价单_${quote.quote_number}.xlsx`
      a.click()
      message.success('Excel导出成功!')
    } catch (error) {
      message.error('导出失败')
    }
  }

  // 导出PDF
  const handleExportPDF = async () => {
    try {
      const blob = await exportQuotePDF(quoteId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `报价单_${quote.quote_number}.pdf`
      a.click()
      message.success('PDF导出成功!')
    } catch (error) {
      message.error('导出失败')
    }
  }

  if (isLoading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
        </div>
      </Card>
    )
  }

  if (!quote) {
    return (
      <Card>
        <Alert message="报价单不存在" type="error" />
      </Card>
    )
  }

  const statusConfig = {
    draft: { color: 'default', text: '草稿' },
    sent: { color: 'processing', text: '已发送' },
    approved: { color: 'success', text: '已批准' },
    rejected: { color: 'error', text: '已拒绝' },
  }

  const status = statusConfig[quote.status] || statusConfig.draft

  const processColumns = [
    {
      title: '工序名称',
      dataIndex: 'process_name',
      key: 'process_name',
    },
    {
      title: '工序代码',
      dataIndex: 'process_code',
      key: 'process_code',
    },
    {
      title: '工时费率 (元/小时)',
      dataIndex: 'hourly_rate',
      key: 'hourly_rate',
      render: (val) => `¥${val?.toFixed(2)}`,
    },
    {
      title: '工序成本 (元)',
      dataIndex: 'cost',
      key: 'cost',
      render: (val) => `¥${val?.toFixed(4)}`,
    },
  ]

  return (
    <div>
      <Card
        title={
          <Space>
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/quotes/list')}
            >
              返回
            </Button>
            <span>报价单详情</span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<FileExcelOutlined />} onClick={handleExportExcel}>
              导出Excel
            </Button>
            <Button icon={<FilePdfOutlined />} onClick={handleExportPDF}>
              导出PDF
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 基本信息 */}
          <Card title="基本信息" size="small">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="报价单号">{quote.quote_number}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={status.color}>{status.text}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="客户名称">{quote.customer_name}</Descriptions.Item>
              <Descriptions.Item label="产品名称">{quote.product_name}</Descriptions.Item>
              <Descriptions.Item label="图号">{quote.drawing_number}</Descriptions.Item>
              <Descriptions.Item label="材质">{quote.material}</Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(quote.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="有效期至">
                {quote.valid_until || 'N/A'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 成本统计 */}
          <Row gutter={16}>
            <Col span={6}>
              <Card className="cost-card">
                <div className="cost-card-label">材料成本</div>
                <div className="cost-card-value">¥{quote.material_cost?.toFixed(4)}</div>
              </Card>
            </Col>
            <Col span={6}>
              <Card className="cost-card">
                <div className="cost-card-label">加工成本</div>
                <div className="cost-card-value">¥{quote.process_cost?.toFixed(4)}</div>
              </Card>
            </Col>
            <Col span={6}>
              <Card className="cost-card">
                <div className="cost-card-label">管理费</div>
                <div className="cost-card-value">¥{quote.management_cost?.toFixed(4)}</div>
              </Card>
            </Col>
            <Col span={6}>
              <Card className="cost-card">
                <div className="cost-card-label">利润</div>
                <div className="cost-card-value">¥{quote.profit?.toFixed(4)}</div>
              </Card>
            </Col>
          </Row>

          {/* 工序列表 */}
          {quote.quote_items && quote.quote_items.length > 0 && (
            <Card title="工序明细" size="small">
              <Table
                columns={processColumns}
                dataSource={quote.quote_items}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </Card>
          )}

          {/* 报价汇总 */}
          <Card title="报价汇总" size="small">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="单价">
                ¥{quote.unit_price?.toFixed(4)} / 件
              </Descriptions.Item>
              <Descriptions.Item label="批量">{quote.lot_size} 件</Descriptions.Item>
              <Descriptions.Item label="其他费用">
                ¥{quote.other_cost?.toFixed(4)}
              </Descriptions.Item>
              <Descriptions.Item label="备注">{quote.notes || 'N/A'}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <div className="total-price">
              <div className="total-price-label">总金额</div>
              <div>¥{quote.total_amount?.toFixed(2)}</div>
            </div>
          </Card>
        </Space>
      </Card>
    </div>
  )
}

export default QuoteDetail
