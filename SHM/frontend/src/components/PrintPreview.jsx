/**
 * 打印预览组件
 * 支持送货单和装箱单两种格式
 */
import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Spin, message, Space, Divider } from 'antd';
import { PrinterOutlined, CloseOutlined, DownloadOutlined } from '@ant-design/icons';
import { shipmentApi } from '../api';

// 打印样式
const printStyles = `
  @media print {
    body * {
      visibility: hidden;
    }
    .print-content, .print-content * {
      visibility: visible;
    }
    .print-content {
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
    }
    .no-print {
      display: none !important;
    }
    @page {
      size: A4;
      margin: 10mm;
    }
  }
`;

// 送货单模板
const DeliveryNoteTemplate = ({ data }) => {
  if (!data) return null;

  return (
    <div className="print-content" style={{ padding: '20px', fontFamily: 'SimSun, serif' }}>
      {/* 公司抬头 */}
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>
          {data.company_info?.name || '金正昌五金制品（惠州）有限公司'}
        </h1>
        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
          地址：{data.company_info?.address} | 电话：{data.company_info?.phone} | 传真：{data.company_info?.fax}
        </div>
      </div>

      {/* 单据标题 */}
      <h2 style={{ textAlign: 'center', fontSize: '20px', fontWeight: 'bold', margin: '20px 0', borderBottom: '2px solid #000', paddingBottom: '10px' }}>
        送 货 单
      </h2>

      {/* 基本信息 */}
      <table style={{ width: '100%', marginBottom: '20px', fontSize: '14px' }}>
        <tbody>
          <tr>
            <td style={{ width: '50%' }}>
              <strong>送货单号：</strong>{data.shipment?.shipment_no}
            </td>
            <td style={{ width: '50%' }}>
              <strong>订单号：</strong>{data.shipment?.order_no || '-'}
            </td>
          </tr>
          <tr>
            <td>
              <strong>送货日期：</strong>{data.shipment?.delivery_date || '-'}
            </td>
            <td>
              <strong>预计到达：</strong>{data.shipment?.expected_arrival || '-'}
            </td>
          </tr>
          <tr>
            <td>
              <strong>运输方式：</strong>{data.shipment?.shipping_method || '-'}
            </td>
            <td>
              <strong>承运商：</strong>{data.shipment?.carrier || '-'}
            </td>
          </tr>
          <tr>
            <td colSpan={2}>
              <strong>物流单号：</strong>{data.shipment?.tracking_no || '-'}
            </td>
          </tr>
        </tbody>
      </table>

      {/* 客户信息 */}
      <div style={{ border: '1px solid #000', padding: '10px', marginBottom: '20px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '10px', borderBottom: '1px solid #ccc', paddingBottom: '5px' }}>
          收货信息
        </div>
        <table style={{ width: '100%', fontSize: '14px' }}>
          <tbody>
            <tr>
              <td style={{ width: '50%' }}>
                <strong>客户名称：</strong>{data.customer?.name}
              </td>
              <td style={{ width: '50%' }}>
                <strong>联系人：</strong>{data.customer?.contact}
              </td>
            </tr>
            <tr>
              <td>
                <strong>联系电话：</strong>{data.customer?.phone}
              </td>
              <td></td>
            </tr>
            <tr>
              <td colSpan={2}>
                <strong>收货地址：</strong>{data.customer?.address}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 产品明细 */}
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>序号</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>产品编码</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>产品名称</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>数量</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>单位</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>批次号</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>备注</th>
          </tr>
        </thead>
        <tbody>
          {data.items?.map((item, index) => (
            <tr key={index}>
              <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>{item.seq}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.product_code}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.product_name}</td>
              <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'right' }}>{item.qty}</td>
              <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>{item.unit}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.batch_no || '-'}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.remark || '-'}</td>
            </tr>
          ))}
          <tr style={{ backgroundColor: '#f9f9f9', fontWeight: 'bold' }}>
            <td colSpan={3} style={{ border: '1px solid #000', padding: '8px', textAlign: 'right' }}>合计：</td>
            <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'right' }}>{data.summary?.total_qty}</td>
            <td colSpan={3} style={{ border: '1px solid #000', padding: '8px' }}>共 {data.summary?.total_items} 项</td>
          </tr>
        </tbody>
      </table>

      {/* 备注 */}
      {data.shipment?.remark && (
        <div style={{ marginBottom: '20px' }}>
          <strong>备注：</strong>{data.shipment.remark}
        </div>
      )}

      {/* 签收栏 */}
      <div style={{ marginTop: '40px', borderTop: '1px dashed #000', paddingTop: '20px' }}>
        <table style={{ width: '100%', fontSize: '14px' }}>
          <tbody>
            <tr>
              <td style={{ width: '33%' }}>发货人签字：________________</td>
              <td style={{ width: '33%' }}>收货人签字：________________</td>
              <td style={{ width: '33%' }}>签收日期：________________</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 打印时间 */}
      <div style={{ marginTop: '30px', fontSize: '12px', color: '#999', textAlign: 'right' }}>
        打印时间：{data.print_time}
      </div>
    </div>
  );
};

// 装箱单模板
const PackingListTemplate = ({ data }) => {
  if (!data) return null;

  return (
    <div className="print-content" style={{ padding: '20px', fontFamily: 'SimSun, serif' }}>
      {/* 公司抬头 */}
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>
          {data.company_info?.name || '金正昌五金制品（惠州）有限公司'}
        </h1>
        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
          地址：{data.company_info?.address} | 电话：{data.company_info?.phone}
        </div>
      </div>

      {/* 单据标题 */}
      <h2 style={{ textAlign: 'center', fontSize: '20px', fontWeight: 'bold', margin: '20px 0', borderBottom: '2px solid #000', paddingBottom: '10px' }}>
        装 箱 单 (Packing List)
      </h2>

      {/* 基本信息 */}
      <table style={{ width: '100%', marginBottom: '20px', fontSize: '14px' }}>
        <tbody>
          <tr>
            <td style={{ width: '50%' }}>
              <strong>出货单号：</strong>{data.shipment?.shipment_no}
            </td>
            <td style={{ width: '50%' }}>
              <strong>订单号：</strong>{data.shipment?.order_no || '-'}
            </td>
          </tr>
          <tr>
            <td>
              <strong>出货日期：</strong>{data.shipment?.delivery_date || '-'}
            </td>
            <td>
              <strong>物流单号：</strong>{data.shipment?.tracking_no || '-'}
            </td>
          </tr>
        </tbody>
      </table>

      {/* 收货人信息 */}
      <div style={{ border: '1px solid #000', padding: '10px', marginBottom: '20px' }}>
        <table style={{ width: '100%', fontSize: '14px' }}>
          <tbody>
            <tr>
              <td><strong>收货人：</strong>{data.customer?.name}</td>
              <td><strong>联系人：</strong>{data.customer?.contact}</td>
              <td><strong>电话：</strong>{data.customer?.phone}</td>
            </tr>
            <tr>
              <td colSpan={3}><strong>地址：</strong>{data.customer?.address}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 装箱明细 */}
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>序号</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>产品编码</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>产品名称</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>数量</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>单位</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>批次号</th>
            <th style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>仓位</th>
          </tr>
        </thead>
        <tbody>
          {data.items?.map((item, index) => (
            <tr key={index}>
              <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>{item.seq}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.product_code}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.product_name}</td>
              <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'right' }}>{item.qty}</td>
              <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'center' }}>{item.unit}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.batch_no || '-'}</td>
              <td style={{ border: '1px solid #000', padding: '8px' }}>{item.bin_code || '-'}</td>
            </tr>
          ))}
          <tr style={{ backgroundColor: '#f9f9f9', fontWeight: 'bold' }}>
            <td colSpan={3} style={{ border: '1px solid #000', padding: '8px', textAlign: 'right' }}>合计：</td>
            <td style={{ border: '1px solid #000', padding: '8px', textAlign: 'right' }}>{data.summary?.total_qty}</td>
            <td colSpan={3} style={{ border: '1px solid #000', padding: '8px' }}>
              共 {data.summary?.total_items} 项，{data.summary?.total_batches} 批次
            </td>
          </tr>
        </tbody>
      </table>

      {/* 批次汇总 */}
      {data.batches && data.batches.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>按批次汇总：</div>
          <table style={{ width: '50%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th style={{ border: '1px solid #000', padding: '6px' }}>批次号</th>
                <th style={{ border: '1px solid #000', padding: '6px' }}>数量</th>
              </tr>
            </thead>
            <tbody>
              {data.batches.map((batch, idx) => (
                <tr key={idx}>
                  <td style={{ border: '1px solid #000', padding: '6px' }}>{batch.batch_no}</td>
                  <td style={{ border: '1px solid #000', padding: '6px', textAlign: 'right' }}>{batch.total_qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 签收栏 */}
      <div style={{ marginTop: '40px', borderTop: '1px dashed #000', paddingTop: '20px' }}>
        <table style={{ width: '100%', fontSize: '14px' }}>
          <tbody>
            <tr>
              <td style={{ width: '50%' }}>制单人：________________</td>
              <td style={{ width: '50%' }}>验收人：________________</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 打印时间 */}
      <div style={{ marginTop: '30px', fontSize: '12px', color: '#999', textAlign: 'right' }}>
        打印时间：{data.print_time}
      </div>
    </div>
  );
};

// 打印预览 Modal
const PrintPreview = ({ visible, onClose, shipmentId, printType = 'delivery_note' }) => {
  const [loading, setLoading] = useState(false);
  const [printData, setPrintData] = useState(null);
  const printRef = useRef(null);

  useEffect(() => {
    if (visible && shipmentId) {
      fetchPrintData();
    }
  }, [visible, shipmentId, printType]);

  const fetchPrintData = async () => {
    setLoading(true);
    try {
      let response;
      if (printType === 'delivery_note') {
        response = await shipmentApi.getDeliveryNote(shipmentId);
      } else {
        response = await shipmentApi.getPackingList(shipmentId);
      }

      if (response.success) {
        setPrintData(response.data);
      } else {
        message.error(response.error || '获取打印数据失败');
      }
    } catch (error) {
      console.error('获取打印数据失败:', error);
      message.error('获取打印数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    // 添加打印样式
    const styleSheet = document.createElement('style');
    styleSheet.textContent = printStyles;
    document.head.appendChild(styleSheet);

    window.print();

    // 移除打印样式
    setTimeout(() => {
      document.head.removeChild(styleSheet);
    }, 1000);
  };

  return (
    <Modal
      title={printType === 'delivery_note' ? '送货单预览' : '装箱单预览'}
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <div className="no-print">
          <Space>
            <Button icon={<CloseOutlined />} onClick={onClose}>关闭</Button>
            <Button
              type="primary"
              icon={<PrinterOutlined />}
              onClick={handlePrint}
              disabled={!printData}
            >
              打印
            </Button>
          </Space>
        </div>
      }
    >
      <div ref={printRef}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" tip="加载中..." />
          </div>
        ) : printType === 'delivery_note' ? (
          <DeliveryNoteTemplate data={printData} />
        ) : (
          <PackingListTemplate data={printData} />
        )}
      </div>
    </Modal>
  );
};

export default PrintPreview;
