import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Modal, Form, Input, Select, DatePicker,
  TimePicker, message, Tag, Tabs, Row, Col, Statistic, InputNumber
} from 'antd';
import {
  ClockCircleOutlined, LoginOutlined, LogoutOutlined, PlusOutlined,
  CalendarOutlined, FieldTimeOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { attendanceAPI, employeeAPI } from '../services/api';

const { RangePicker } = DatePicker;
const { Option } = Select;

export default function AttendanceManagement() {
  const [activeTab, setActiveTab] = useState('checkin');
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [overtimeRequests, setOvertimeRequests] = useState([]);
  const [dailyStats, setDailyStats] = useState(null);

  // Modals
  const [shiftModalOpen, setShiftModalOpen] = useState(false);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [overtimeModalOpen, setOvertimeModalOpen] = useState(false);
  const [editingShift, setEditingShift] = useState(null);

  const [form] = Form.useForm();
  const [scheduleForm] = Form.useForm();
  const [overtimeForm] = Form.useForm();

  // Filters
  const [filters, setFilters] = useState({
    employee_id: null,
    start_date: dayjs().startOf('month').format('YYYY-MM-DD'),
    end_date: dayjs().endOf('month').format('YYYY-MM-DD'),
  });

  useEffect(() => {
    fetchEmployees();
    fetchShifts();
    fetchDailyStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'records') {
      fetchRecords();
    } else if (activeTab === 'schedules') {
      fetchSchedules();
    } else if (activeTab === 'overtime') {
      fetchOvertimeRequests();
    }
  }, [activeTab, filters]);

  const fetchEmployees = async () => {
    try {
      const res = await employeeAPI.getEmployees();
      setEmployees(res.employees || res.items || []);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
    }
  };

  const fetchShifts = async () => {
    try {
      const res = await attendanceAPI.getShifts();
      setShifts(res.items || []);
    } catch (error) {
      console.error('Failed to fetch shifts:', error);
    }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const res = await attendanceAPI.getRecords(filters);
      setRecords(res.items || []);
    } catch (error) {
      message.error('获取考勤记录失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const res = await attendanceAPI.getSchedules(filters);
      setSchedules(res.items || []);
    } catch (error) {
      message.error('获取排班记录失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchOvertimeRequests = async () => {
    setLoading(true);
    try {
      const res = await attendanceAPI.getOvertimeRequests({});
      setOvertimeRequests(res.items || []);
    } catch (error) {
      message.error('获取加班申请失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyStats = async () => {
    try {
      const res = await attendanceAPI.getDailyStats(dayjs().format('YYYY-MM-DD'));
      setDailyStats(res);
    } catch (error) {
      console.error('Failed to fetch daily stats:', error);
    }
  };

  // 打卡
  const handleCheckIn = async () => {
    const userId = localStorage.getItem('User-ID');
    if (!userId) {
      message.error('请先登录');
      return;
    }
    try {
      await attendanceAPI.checkIn({ employee_id: parseInt(userId) });
      message.success('上班打卡成功');
      fetchDailyStats();
    } catch (error) {
      message.error(error.response?.data?.error || '打卡失败');
    }
  };

  const handleCheckOut = async () => {
    const userId = localStorage.getItem('User-ID');
    if (!userId) {
      message.error('请先登录');
      return;
    }
    try {
      await attendanceAPI.checkOut({ employee_id: parseInt(userId) });
      message.success('下班打卡成功');
      fetchDailyStats();
    } catch (error) {
      message.error(error.response?.data?.error || '打卡失败');
    }
  };

  // 班次管理
  const handleSaveShift = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        start_time: values.start_time.format('HH:mm'),
        end_time: values.end_time.format('HH:mm'),
      };

      if (editingShift) {
        await attendanceAPI.updateShift(editingShift.id, data);
        message.success('班次更新成功');
      } else {
        await attendanceAPI.createShift(data);
        message.success('班次创建成功');
      }

      setShiftModalOpen(false);
      form.resetFields();
      setEditingShift(null);
      fetchShifts();
    } catch (error) {
      message.error(error.response?.data?.error || '操作失败');
    }
  };

  const handleDeleteShift = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个班次吗？',
      onOk: async () => {
        try {
          await attendanceAPI.deleteShift(id);
          message.success('删除成功');
          fetchShifts();
        } catch (error) {
          message.error(error.response?.data?.error || '删除失败');
        }
      },
    });
  };

  // 排班
  const handleSaveSchedule = async () => {
    try {
      const values = await scheduleForm.validateFields();
      const data = {
        ...values,
        schedule_date: values.schedule_date.format('YYYY-MM-DD'),
      };

      await attendanceAPI.createSchedule(data);
      message.success('排班成功');
      setScheduleModalOpen(false);
      scheduleForm.resetFields();
      fetchSchedules();
    } catch (error) {
      message.error(error.response?.data?.error || '排班失败');
    }
  };

  // 加班申请
  const handleSaveOvertime = async () => {
    try {
      const values = await overtimeForm.validateFields();
      const data = {
        ...values,
        overtime_date: values.overtime_date.format('YYYY-MM-DD'),
        start_time: values.start_time.format('HH:mm'),
        end_time: values.end_time.format('HH:mm'),
      };

      await attendanceAPI.createOvertimeRequest(data);
      message.success('加班申请提交成功');
      setOvertimeModalOpen(false);
      overtimeForm.resetFields();
      fetchOvertimeRequests();
    } catch (error) {
      message.error(error.response?.data?.error || '申请失败');
    }
  };

  const handleApproveOvertime = async (id, action) => {
    try {
      await attendanceAPI.approveOvertime(id, { action });
      message.success('审批成功');
      fetchOvertimeRequests();
    } catch (error) {
      message.error(error.response?.data?.error || '审批失败');
    }
  };

  // 表格列定义
  const recordColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '日期', dataIndex: 'record_date', key: 'record_date' },
    { title: '上班打卡', dataIndex: 'check_in_time', key: 'check_in_time' },
    { title: '下班打卡', dataIndex: 'check_out_time', key: 'check_out_time' },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (status) => {
        const colors = {
          normal: 'green', late: 'orange', early_leave: 'orange',
          absent: 'red', leave: 'blue'
        };
        const labels = {
          normal: '正常', late: '迟到', early_leave: '早退',
          absent: '缺勤', leave: '请假'
        };
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>;
      }
    },
    { title: '工作时长', dataIndex: 'work_hours', key: 'work_hours', render: (h) => h ? `${h}小时` : '-' },
    { title: '备注', dataIndex: 'remark', key: 'remark' },
  ];

  const shiftColumns = [
    { title: '班次编码', dataIndex: 'code', key: 'code' },
    { title: '班次名称', dataIndex: 'name', key: 'name' },
    { title: '上班时间', dataIndex: 'start_time', key: 'start_time' },
    { title: '下班时间', dataIndex: 'end_time', key: 'end_time' },
    { title: '工作时长', dataIndex: 'work_hours', key: 'work_hours', render: (h) => `${h}小时` },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (active) => <Tag color={active ? 'green' : 'red'}>{active ? '启用' : '停用'}</Tag>
    },
    {
      title: '操作', key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => { setEditingShift(record); setShiftModalOpen(true); form.setFieldsValue({ ...record, start_time: dayjs(record.start_time, 'HH:mm'), end_time: dayjs(record.end_time, 'HH:mm') }); }}>编辑</Button>
          <Button type="link" danger onClick={() => handleDeleteShift(record.id)}>删除</Button>
        </Space>
      )
    },
  ];

  const scheduleColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '日期', dataIndex: 'schedule_date', key: 'schedule_date' },
    { title: '班次', dataIndex: 'shift_name', key: 'shift_name' },
    { title: '上班时间', dataIndex: 'start_time', key: 'start_time' },
    { title: '下班时间', dataIndex: 'end_time', key: 'end_time' },
  ];

  const overtimeColumns = [
    { title: '员工', dataIndex: 'employee_name', key: 'employee_name' },
    { title: '加班日期', dataIndex: 'overtime_date', key: 'overtime_date' },
    { title: '开始时间', dataIndex: 'start_time', key: 'start_time' },
    { title: '结束时间', dataIndex: 'end_time', key: 'end_time' },
    { title: '加班时长', dataIndex: 'hours', key: 'hours', render: (h) => `${h}小时` },
    { title: '加班类型', dataIndex: 'overtime_type', key: 'overtime_type' },
    { title: '原因', dataIndex: 'reason', key: 'reason' },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (status) => {
        const colors = { pending: 'gold', approved: 'green', rejected: 'red' };
        const labels = { pending: '待审批', approved: '已通过', rejected: '已拒绝' };
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>;
      }
    },
    {
      title: '操作', key: 'action',
      render: (_, record) => record.status === 'pending' && (
        <Space>
          <Button type="link" onClick={() => handleApproveOvertime(record.id, 'approve')}>通过</Button>
          <Button type="link" danger onClick={() => handleApproveOvertime(record.id, 'reject')}>拒绝</Button>
        </Space>
      )
    },
  ];

  const tabItems = [
    {
      key: 'checkin',
      label: <span><ClockCircleOutlined /> 打卡</span>,
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic title="今日出勤" value={dailyStats?.checked_in || 0} suffix="人" />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="迟到" value={dailyStats?.late || 0} suffix="人" valueStyle={{ color: '#faad14' }} />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="早退" value={dailyStats?.early_leave || 0} suffix="人" valueStyle={{ color: '#faad14' }} />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="缺勤" value={dailyStats?.absent || 0} suffix="人" valueStyle={{ color: '#ff4d4f' }} />
              </Card>
            </Col>
          </Row>

          <Card title="快速打卡" style={{ marginBottom: 24 }}>
            <Space size="large">
              <Button type="primary" size="large" icon={<LoginOutlined />} onClick={handleCheckIn}>
                上班打卡
              </Button>
              <Button size="large" icon={<LogoutOutlined />} onClick={handleCheckOut}>
                下班打卡
              </Button>
              <span style={{ color: '#999' }}>当前时间: {dayjs().format('YYYY-MM-DD HH:mm:ss')}</span>
            </Space>
          </Card>
        </div>
      )
    },
    {
      key: 'records',
      label: <span><CalendarOutlined /> 考勤记录</span>,
      children: (
        <Card
          title="考勤记录"
          extra={
            <Space>
              <RangePicker
                value={[dayjs(filters.start_date), dayjs(filters.end_date)]}
                onChange={(dates) => setFilters({
                  ...filters,
                  start_date: dates?.[0]?.format('YYYY-MM-DD'),
                  end_date: dates?.[1]?.format('YYYY-MM-DD')
                })}
              />
              <Select
                placeholder="选择员工"
                allowClear
                style={{ width: 150 }}
                value={filters.employee_id}
                onChange={(v) => setFilters({ ...filters, employee_id: v })}
              >
                {employees.map(emp => (
                  <Option key={emp.id} value={emp.id}>{emp.name}</Option>
                ))}
              </Select>
              <Button onClick={fetchRecords}>查询</Button>
            </Space>
          }
        >
          <Table columns={recordColumns} dataSource={records} rowKey="id" loading={loading} />
        </Card>
      )
    },
    {
      key: 'shifts',
      label: <span><FieldTimeOutlined /> 班次管理</span>,
      children: (
        <Card
          title="班次管理"
          extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingShift(null); form.resetFields(); setShiftModalOpen(true); }}>新建班次</Button>}
        >
          <Table columns={shiftColumns} dataSource={shifts} rowKey="id" loading={loading} />
        </Card>
      )
    },
    {
      key: 'schedules',
      label: <span><CalendarOutlined /> 排班管理</span>,
      children: (
        <Card
          title="排班管理"
          extra={
            <Space>
              <RangePicker
                value={[dayjs(filters.start_date), dayjs(filters.end_date)]}
                onChange={(dates) => setFilters({
                  ...filters,
                  start_date: dates?.[0]?.format('YYYY-MM-DD'),
                  end_date: dates?.[1]?.format('YYYY-MM-DD')
                })}
              />
              <Button type="primary" icon={<PlusOutlined />} onClick={() => { scheduleForm.resetFields(); setScheduleModalOpen(true); }}>新建排班</Button>
            </Space>
          }
        >
          <Table columns={scheduleColumns} dataSource={schedules} rowKey="id" loading={loading} />
        </Card>
      )
    },
    {
      key: 'overtime',
      label: <span><ClockCircleOutlined /> 加班管理</span>,
      children: (
        <Card
          title="加班申请"
          extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { overtimeForm.resetFields(); setOvertimeModalOpen(true); }}>申请加班</Button>}
        >
          <Table columns={overtimeColumns} dataSource={overtimeRequests} rowKey="id" loading={loading} />
        </Card>
      )
    },
  ];

  return (
    <div>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      {/* 班次表单 */}
      <Modal
        title={editingShift ? '编辑班次' : '新建班次'}
        open={shiftModalOpen}
        onOk={handleSaveShift}
        onCancel={() => setShiftModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="code" label="班次编码" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="班次名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="start_time" label="上班时间" rules={[{ required: true }]}>
            <TimePicker format="HH:mm" />
          </Form.Item>
          <Form.Item name="end_time" label="下班时间" rules={[{ required: true }]}>
            <TimePicker format="HH:mm" />
          </Form.Item>
          <Form.Item name="work_hours" label="工作时长(小时)">
            <InputNumber min={0} max={24} />
          </Form.Item>
          <Form.Item name="is_active" label="是否启用" initialValue={true}>
            <Select>
              <Option value={true}>启用</Option>
              <Option value={false}>停用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 排班表单 */}
      <Modal
        title="新建排班"
        open={scheduleModalOpen}
        onOk={handleSaveSchedule}
        onCancel={() => setScheduleModalOpen(false)}
      >
        <Form form={scheduleForm} layout="vertical">
          <Form.Item name="employee_id" label="员工" rules={[{ required: true }]}>
            <Select placeholder="选择员工">
              {employees.map(emp => (
                <Option key={emp.id} value={emp.id}>{emp.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="shift_id" label="班次" rules={[{ required: true }]}>
            <Select placeholder="选择班次">
              {shifts.map(shift => (
                <Option key={shift.id} value={shift.id}>{shift.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="schedule_date" label="日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 加班申请表单 */}
      <Modal
        title="申请加班"
        open={overtimeModalOpen}
        onOk={handleSaveOvertime}
        onCancel={() => setOvertimeModalOpen(false)}
      >
        <Form form={overtimeForm} layout="vertical">
          <Form.Item name="employee_id" label="员工" rules={[{ required: true }]}>
            <Select placeholder="选择员工">
              {employees.map(emp => (
                <Option key={emp.id} value={emp.id}>{emp.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="overtime_date" label="加班日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="start_time" label="开始时间" rules={[{ required: true }]}>
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="end_time" label="结束时间" rules={[{ required: true }]}>
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="overtime_type" label="加班类型" rules={[{ required: true }]}>
            <Select placeholder="选择类型">
              <Option value="workday">工作日加班</Option>
              <Option value="weekend">周末加班</Option>
              <Option value="holiday">节假日加班</Option>
            </Select>
          </Form.Item>
          <Form.Item name="reason" label="加班原因" rules={[{ required: true }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
