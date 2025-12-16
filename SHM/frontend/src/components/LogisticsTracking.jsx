/**
 * 物流追踪组件
 */
import { useState, useEffect } from 'react';
import {
  Modal,
  Timeline,
  Card,
  Button,
  Form,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Descriptions,
  message,
  Spin,
  Empty,
  Popconfirm,
  Divider,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  EnvironmentOutlined,
  ClockCircleOutlined,
  UserOutlined,
  PhoneOutlined,
  PlusOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CarOutlined,
  InboxOutlined,
  SendOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { logisticsApi } from '../api';

const { TextArea } = Input;

// 事件类型图标和颜色
const EVENT_CONFIG = {
  created: { icon: <InboxOutlined />, color: 'default', text: '已创建' },
  picked_up: { icon: <SendOutlined />, color: 'processing', text: '已揽收' },
  in_transit: { icon: <CarOutlined />, color: 'processing', text: '运输中' },
  arrived: { icon: <EnvironmentOutlined />, color: 'processing', text: '已到达' },
  out_for_delivery: { icon: <CarOutlined />, color: 'warning', text: '派送中' },
  delivered: { icon: <CheckCircleOutlined />, color: 'success', text: '已签收' },
  exception: { icon: <ExclamationCircleOutlined />, color: 'error', text: '异常' },
  returned: { icon: <ExclamationCircleOutlined />, color: 'error', text: '已退回' },
};

/**
 * 物流追踪详情弹窗
 */
export function LogisticsTrackingModal({ visible, shipmentId, shipment, onClose, onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [traces, setTraces] = useState([]);
  const [trackingInfo, setTrackingInfo] = useState(null);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [eventTypes, setEventTypes] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible && shipmentId) {
      fetchTraces();
      fetchEventTypes();
    }
  }, [visible, shipmentId]);

  const fetchTraces = async () => {
    setLoading(true);
    try {
      const res = await logisticsApi.getTraces(shipmentId);
      if (res.code === 0) {
        setTraces(res.data.traces || []);
        setTrackingInfo(res.data);
      }
    } catch (err) {
      console.error('获取物流轨迹失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchEventTypes = async () => {
    try {
      const res = await logisticsApi.getEventTypes();
      if (res.code === 0) {
        setEventTypes(res.data || []);
      }
    } catch (err) {
      console.error('获取事件类型失败:', err);
    }
  };

  const handleAddTrace = async (values) => {
    try {
      const data = {
        ...values,
        event_time: values.event_time?.format('YYYY-MM-DD HH:mm:ss'),
      };
      const res = await logisticsApi.addTrace(shipmentId, data);
      if (res.code === 0) {
        message.success('添加成功');
        setAddModalVisible(false);
        form.resetFields();
        fetchTraces();
        onRefresh?.();
      } else {
        message.error(res.message || '添加失败');
      }
    } catch (err) {
      message.error('添加失败');
    }
  };

  const handleDeleteTrace = async (traceId) => {
    try {
      const res = await logisticsApi.deleteTrace(traceId);
      if (res.code === 0) {
        message.success('删除成功');
        fetchTraces();
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (err) {
      message.error('删除失败');
    }
  };

  return (
    <>
      <Modal
        title="物流追踪"
        open={visible}
        onCancel={onClose}
        width={700}
        footer={[
          <Button key="add" type="primary" icon={<PlusOutlined />} onClick={() => setAddModalVisible(true)}>
            添加轨迹
          </Button>,
          <Button key="close" onClick={onClose}>
            关闭
          </Button>,
        ]}
      >
        <Spin spinning={loading}>
          {/* 物流信息概览 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="出货单号"
                  value={trackingInfo?.shipment_no || shipment?.shipment_no || '-'}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="承运商"
                  value={trackingInfo?.carrier || shipment?.carrier || '-'}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="物流单号"
                  value={trackingInfo?.tracking_no || shipment?.tracking_no || '-'}
                  valueStyle={{ fontSize: 14 }}
                />
              </Col>
            </Row>
          </Card>

          {/* 物流轨迹时间线 */}
          {traces.length > 0 ? (
            <Timeline
              mode="left"
              items={traces.map((trace) => {
                const config = EVENT_CONFIG[trace.event_type] || EVENT_CONFIG.created;
                return {
                  key: trace.id,
                  dot: config.icon,
                  color: config.color === 'default' ? 'gray' : config.color,
                  children: (
                    <div style={{ paddingBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <Tag color={config.color}>{trace.event_type_label || config.text}</Tag>
                          <span style={{ color: '#999', fontSize: 12, marginLeft: 8 }}>
                            <ClockCircleOutlined /> {trace.event_time}
                          </span>
                        </div>
                        <Popconfirm
                          title="确定删除此轨迹?"
                          onConfirm={() => handleDeleteTrace(trace.id)}
                        >
                          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                      </div>
                      {trace.location && (
                        <div style={{ marginTop: 4, color: '#666' }}>
                          <EnvironmentOutlined /> {trace.location}
                        </div>
                      )}
                      {trace.description && (
                        <div style={{ marginTop: 4 }}>{trace.description}</div>
                      )}
                      {trace.operator && (
                        <div style={{ marginTop: 4, color: '#999', fontSize: 12 }}>
                          <UserOutlined /> {trace.operator}
                          {trace.operator_phone && (
                            <span style={{ marginLeft: 8 }}>
                              <PhoneOutlined /> {trace.operator_phone}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ),
                };
              })}
            />
          ) : (
            <Empty description="暂无物流轨迹" />
          )}
        </Spin>
      </Modal>

      {/* 添加轨迹弹窗 */}
      <Modal
        title="添加物流轨迹"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddTrace}
          initialValues={{
            event_time: dayjs(),
          }}
        >
          <Form.Item
            name="event_type"
            label="事件类型"
            rules={[{ required: true, message: '请选择事件类型' }]}
          >
            <Select placeholder="请选择">
              {eventTypes.map((t) => (
                <Select.Option key={t.value} value={t.value}>
                  {t.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="event_time"
            label="事件时间"
            rules={[{ required: true, message: '请选择时间' }]}
          >
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="location" label="地点">
            <Input placeholder="请输入地点" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="请输入描述" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="operator" label="操作人">
                <Input placeholder="请输入操作人" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="operator_phone" label="联系电话">
                <Input placeholder="请输入电话" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="remark" label="备注">
            <TextArea rows={2} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

/**
 * 签收回执弹窗
 */
export function DeliveryReceiptModal({ visible, shipmentId, shipment, onClose, onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [conditions, setConditions] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible && shipmentId) {
      fetchReceipt();
      fetchConditions();
    }
  }, [visible, shipmentId]);

  const fetchReceipt = async () => {
    setLoading(true);
    try {
      const res = await logisticsApi.getReceipt(shipmentId);
      if (res.code === 0) {
        setReceipt(res.data.receipt);
        if (res.data.receipt) {
          form.setFieldsValue({
            ...res.data.receipt,
            sign_time: res.data.receipt.sign_time ? dayjs(res.data.receipt.sign_time) : null,
          });
        }
      }
    } catch (err) {
      console.error('获取签收回执失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchConditions = async () => {
    try {
      const res = await logisticsApi.getReceiptConditions();
      if (res.code === 0) {
        setConditions(res.data || []);
      }
    } catch (err) {
      console.error('获取收货状况枚举失败:', err);
    }
  };

  const handleSubmit = async (values) => {
    try {
      const data = {
        ...values,
        sign_time: values.sign_time?.format('YYYY-MM-DD HH:mm:ss'),
      };

      let res;
      if (receipt) {
        res = await logisticsApi.updateReceipt(shipmentId, data);
      } else {
        res = await logisticsApi.createReceipt(shipmentId, data);
      }

      if (res.code === 0) {
        message.success(receipt ? '更新成功' : '签收成功');
        setEditMode(false);
        fetchReceipt();
        onRefresh?.();
      } else {
        message.error(res.message || '操作失败');
      }
    } catch (err) {
      message.error('操作失败');
    }
  };

  const renderReceiptInfo = () => (
    <Descriptions column={2} bordered size="small">
      <Descriptions.Item label="签收人">{receipt?.receiver_name}</Descriptions.Item>
      <Descriptions.Item label="联系电话">{receipt?.receiver_phone}</Descriptions.Item>
      <Descriptions.Item label="签收时间">{receipt?.sign_time}</Descriptions.Item>
      <Descriptions.Item label="签收地点">{receipt?.sign_location}</Descriptions.Item>
      <Descriptions.Item label="收货状况">
        <Tag color={receipt?.receipt_condition === '完好' ? 'success' : 'error'}>
          {receipt?.receipt_condition}
        </Tag>
      </Descriptions.Item>
      <Descriptions.Item label="实际收货数量">{receipt?.actual_qty}</Descriptions.Item>
      {receipt?.damage_description && (
        <Descriptions.Item label="损坏描述" span={2}>
          {receipt?.damage_description}
        </Descriptions.Item>
      )}
      {receipt?.feedback && (
        <Descriptions.Item label="客户反馈" span={2}>
          {receipt?.feedback}
        </Descriptions.Item>
      )}
      {receipt?.remark && (
        <Descriptions.Item label="备注" span={2}>
          {receipt?.remark}
        </Descriptions.Item>
      )}
    </Descriptions>
  );

  const renderReceiptForm = () => (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        receiver_name: shipment?.receiver_contact,
        receiver_phone: shipment?.receiver_phone,
        sign_location: shipment?.receiver_address,
        sign_time: dayjs(),
        receipt_condition: '完好',
      }}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="receiver_name"
            label="签收人"
            rules={[{ required: true, message: '请输入签收人' }]}
          >
            <Input placeholder="请输入签收人姓名" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="receiver_phone" label="联系电话">
            <Input placeholder="请输入联系电话" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="sign_time"
            label="签收时间"
            rules={[{ required: true, message: '请选择签收时间' }]}
          >
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="receipt_condition" label="收货状况">
            <Select>
              {conditions.map((c) => (
                <Select.Option key={c.value} value={c.value}>
                  {c.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="sign_location" label="签收地点">
        <Input placeholder="请输入签收地点" />
      </Form.Item>

      <Form.Item name="actual_qty" label="实际收货数量">
        <Input type="number" placeholder="请输入实际收货数量" />
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prev, curr) => prev.receipt_condition !== curr.receipt_condition}
      >
        {({ getFieldValue }) =>
          getFieldValue('receipt_condition') !== '完好' && (
            <Form.Item name="damage_description" label="损坏描述">
              <TextArea rows={2} placeholder="请描述损坏情况" />
            </Form.Item>
          )
        }
      </Form.Item>

      <Form.Item name="feedback" label="客户反馈">
        <TextArea rows={2} placeholder="请输入客户反馈" />
      </Form.Item>

      <Form.Item name="remark" label="备注">
        <TextArea rows={2} placeholder="请输入备注" />
      </Form.Item>
    </Form>
  );

  return (
    <Modal
      title="签收回执"
      open={visible}
      onCancel={onClose}
      width={600}
      footer={
        receipt && !editMode
          ? [
              <Button key="edit" type="primary" onClick={() => setEditMode(true)}>
                编辑
              </Button>,
              <Button key="close" onClick={onClose}>
                关闭
              </Button>,
            ]
          : [
              <Button
                key="cancel"
                onClick={() => {
                  if (editMode) {
                    setEditMode(false);
                    form.setFieldsValue({
                      ...receipt,
                      sign_time: receipt?.sign_time ? dayjs(receipt.sign_time) : null,
                    });
                  } else {
                    onClose();
                  }
                }}
              >
                取消
              </Button>,
              <Button key="submit" type="primary" onClick={() => form.submit()}>
                {receipt ? '更新' : '确认签收'}
              </Button>,
            ]
      }
    >
      <Spin spinning={loading}>
        {receipt && !editMode ? renderReceiptInfo() : renderReceiptForm()}
      </Spin>
    </Modal>
  );
}

/**
 * 快速发货弹窗
 */
export function ShipOutModal({ visible, shipmentId, shipment, onClose, onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible && shipment) {
      form.setFieldsValue({
        carrier: shipment.carrier,
        tracking_no: shipment.tracking_no,
        delivery_date: shipment.delivery_date ? dayjs(shipment.delivery_date) : dayjs(),
        expected_arrival: shipment.expected_arrival ? dayjs(shipment.expected_arrival) : null,
      });
    }
  }, [visible, shipment]);

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const data = {
        ...values,
        delivery_date: values.delivery_date?.format('YYYY-MM-DD'),
        expected_arrival: values.expected_arrival?.format('YYYY-MM-DD'),
      };
      const res = await logisticsApi.shipOut(shipmentId, data);
      if (res.code === 0) {
        message.success('发货成功');
        onClose();
        onRefresh?.();
      } else {
        message.error(res.message || '发货失败');
      }
    } catch (err) {
      message.error('发货失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="发货操作"
      open={visible}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      width={500}
    >
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item
          name="carrier"
          label="承运商"
          rules={[{ required: true, message: '请输入承运商' }]}
        >
          <Input placeholder="请输入承运商名称" />
        </Form.Item>

        <Form.Item
          name="tracking_no"
          label="物流单号"
          rules={[{ required: true, message: '请输入物流单号' }]}
        >
          <Input placeholder="请输入物流单号" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="delivery_date"
              label="发货日期"
              rules={[{ required: true, message: '请选择发货日期' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="expected_arrival" label="预计到达日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="location" label="发货地点">
          <Input placeholder="请输入发货地点（可选）" />
        </Form.Item>

        <Form.Item name="operator" label="操作人">
          <Input placeholder="请输入操作人（可选）" />
        </Form.Item>

        <Form.Item name="remark" label="备注">
          <TextArea rows={2} placeholder="请输入备注（可选）" />
        </Form.Item>
      </Form>
    </Modal>
  );
}

/**
 * 快速签收弹窗
 */
export function QuickSignModal({ visible, shipmentId, shipment, onClose, onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [conditions, setConditions] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible) {
      fetchConditions();
      form.setFieldsValue({
        receiver_name: shipment?.receiver_contact,
        receiver_phone: shipment?.receiver_phone,
        sign_location: shipment?.receiver_address,
        receipt_condition: '完好',
      });
    }
  }, [visible, shipment]);

  const fetchConditions = async () => {
    try {
      const res = await logisticsApi.getReceiptConditions();
      if (res.code === 0) {
        setConditions(res.data || []);
      }
    } catch (err) {
      console.error('获取收货状况枚举失败:', err);
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const res = await logisticsApi.signDelivery(shipmentId, values);
      if (res.code === 0) {
        message.success('签收成功');
        onClose();
        onRefresh?.();
      } else {
        message.error(res.message || '签收失败');
      }
    } catch (err) {
      message.error('签收失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="快速签收"
      open={visible}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={loading}
      width={500}
    >
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="receiver_name"
              label="签收人"
              rules={[{ required: true, message: '请输入签收人' }]}
            >
              <Input placeholder="请输入签收人姓名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="receiver_phone" label="联系电话">
              <Input placeholder="请输入联系电话" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="sign_location" label="签收地点">
          <Input placeholder="请输入签收地点" />
        </Form.Item>

        <Form.Item name="receipt_condition" label="收货状况">
          <Select>
            {conditions.map((c) => (
              <Select.Option key={c.value} value={c.value}>
                {c.label}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="feedback" label="客户反馈">
          <TextArea rows={2} placeholder="请输入客户反馈（可选）" />
        </Form.Item>

        <Form.Item name="remark" label="备注">
          <TextArea rows={2} placeholder="请输入备注（可选）" />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export default {
  LogisticsTrackingModal,
  DeliveryReceiptModal,
  ShipOutModal,
  QuickSignModal,
};
