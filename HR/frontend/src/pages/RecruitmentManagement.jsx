/**
 * 招聘管理页面
 * 包含: 职位发布、应聘申请、面试安排、面试评价、人才库
 */
import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Table, Button, Modal, Form, Input, Select, DatePicker,
  InputNumber, Space, Tag, message, Popconfirm, Row, Col, Statistic,
  Descriptions, Progress, Rate, Badge, Divider, Typography, Tooltip
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  TeamOutlined, UserAddOutlined, CalendarOutlined, StarOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined,
  SendOutlined, StopOutlined, DatabaseOutlined
} from '@ant-design/icons';
import { recruitmentAPI, baseDataAPI, employeeAPI } from '../services/api';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Text, Title } = Typography;

// 职位状态
const jobStatusColors = {
  draft: 'default',
  open: 'green',
  paused: 'orange',
  closed: 'gray',
  filled: 'blue',
};
const jobStatusLabels = {
  draft: '草稿',
  open: '招聘中',
  paused: '已暂停',
  closed: '已关闭',
  filled: '已招满',
};

// 申请状态
const applicationStatusColors = {
  pending: 'gold',
  screening: 'cyan',
  interview: 'blue',
  offer: 'purple',
  hired: 'green',
  rejected: 'red',
  withdrawn: 'gray',
};
const applicationStatusLabels = {
  pending: '待筛选',
  screening: '筛选中',
  interview: '面试中',
  offer: '已发Offer',
  hired: '已录用',
  rejected: '已拒绝',
  withdrawn: '已撤回',
};

// 面试状态
const interviewStatusColors = {
  scheduled: 'blue',
  confirmed: 'cyan',
  in_progress: 'orange',
  completed: 'green',
  cancelled: 'red',
  no_show: 'gray',
};
const interviewStatusLabels = {
  scheduled: '已安排',
  confirmed: '已确认',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
  no_show: '未到场',
};

const RecruitmentManagement = () => {
  const [activeTab, setActiveTab] = useState('jobs');
  const [loading, setLoading] = useState(false);

  // 职位相关
  const [jobs, setJobs] = useState([]);
  const [jobModalVisible, setJobModalVisible] = useState(false);
  const [jobForm] = Form.useForm();
  const [editingJob, setEditingJob] = useState(null);
  const [jobPagination, setJobPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 申请相关
  const [applications, setApplications] = useState([]);
  const [applicationModalVisible, setApplicationModalVisible] = useState(false);
  const [applicationForm] = Form.useForm();
  const [applicationDetailVisible, setApplicationDetailVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [appPagination, setAppPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 面试相关
  const [interviews, setInterviews] = useState([]);
  const [interviewModalVisible, setInterviewModalVisible] = useState(false);
  const [interviewForm] = Form.useForm();
  const [evaluationModalVisible, setEvaluationModalVisible] = useState(false);
  const [evaluationForm] = Form.useForm();
  const [selectedInterview, setSelectedInterview] = useState(null);
  const [interviewPagination, setInterviewPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 人才库
  const [talentPool, setTalentPool] = useState([]);
  const [talentPagination, setTalentPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 基础数据
  const [departments, setDepartments] = useState([]);
  const [positions, setPositions] = useState([]);
  const [factories, setFactories] = useState([]);
  const [employees, setEmployees] = useState([]);

  // 统计数据
  const [stats, setStats] = useState(null);

  // 筛选条件
  const [jobFilters, setJobFilters] = useState({ status: '', search: '' });
  const [appFilters, setAppFilters] = useState({ job_id: '', status: '', search: '' });

  useEffect(() => {
    loadBaseData();
    loadStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'jobs') {
      loadJobs();
    } else if (activeTab === 'applications') {
      loadApplications();
    } else if (activeTab === 'interviews') {
      loadInterviews();
    } else if (activeTab === 'talent') {
      loadTalentPool();
    }
  }, [activeTab, jobPagination.current, appPagination.current, interviewPagination.current, talentPagination.current]);

  // 加载基础数据
  const loadBaseData = async () => {
    try {
      const [deptRes, posRes, factRes, empRes] = await Promise.all([
        baseDataAPI.getDepartments(),
        baseDataAPI.getPositions(),
        baseDataAPI.getFactories(),
        employeeAPI.getAll({ per_page: 1000 }),
      ]);
      setDepartments(deptRes.data || []);
      setPositions(posRes.data || []);
      setFactories(factRes.data || []);
      setEmployees(empRes.data?.employees || empRes.data || []);
    } catch (error) {
      console.error('加载基础数据失败:', error);
    }
  };

  // 加载统计数据
  const loadStats = async () => {
    try {
      const res = await recruitmentAPI.getStats();
      if (res.success) {
        setStats(res.data);
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  // ==================== 职位管理 ====================

  const loadJobs = async () => {
    setLoading(true);
    try {
      const res = await recruitmentAPI.getJobs({
        page: jobPagination.current,
        per_page: jobPagination.pageSize,
        ...jobFilters,
      });
      if (res.success) {
        setJobs(res.data.items || []);
        setJobPagination(prev => ({ ...prev, total: res.data.total }));
      }
    } catch (error) {
      message.error('加载职位列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleJobSubmit = async () => {
    try {
      const values = await jobForm.validateFields();

      if (values.publish_date) {
        values.publish_date = values.publish_date.format('YYYY-MM-DD');
      }
      if (values.expire_date) {
        values.expire_date = values.expire_date.format('YYYY-MM-DD');
      }

      if (editingJob) {
        await recruitmentAPI.updateJob(editingJob.id, values);
        message.success('职位更新成功');
      } else {
        await recruitmentAPI.createJob(values);
        message.success('职位创建成功');
      }
      setJobModalVisible(false);
      jobForm.resetFields();
      setEditingJob(null);
      loadJobs();
      loadStats();
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.message || error.message));
    }
  };

  const handlePublishJob = async (job) => {
    try {
      await recruitmentAPI.publishJob(job.id);
      message.success('职位已发布');
      loadJobs();
      loadStats();
    } catch (error) {
      message.error('发布失败');
    }
  };

  const handleCloseJob = async (job) => {
    try {
      await recruitmentAPI.closeJob(job.id);
      message.success('职位已关闭');
      loadJobs();
      loadStats();
    } catch (error) {
      message.error('关闭失败');
    }
  };

  const handleDeleteJob = async (job) => {
    try {
      await recruitmentAPI.deleteJob(job.id);
      message.success('职位已删除');
      loadJobs();
      loadStats();
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.message || error.message));
    }
  };

  // ==================== 应聘申请管理 ====================

  const loadApplications = async () => {
    setLoading(true);
    try {
      const res = await recruitmentAPI.getApplications({
        page: appPagination.current,
        per_page: appPagination.pageSize,
        ...appFilters,
      });
      if (res.success) {
        setApplications(res.data.items || []);
        setAppPagination(prev => ({ ...prev, total: res.data.total }));
      }
    } catch (error) {
      message.error('加载申请列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleApplicationSubmit = async () => {
    try {
      const values = await applicationForm.validateFields();

      if (values.birth_date) {
        values.birth_date = values.birth_date.format('YYYY-MM-DD');
      }
      if (values.graduation_date) {
        values.graduation_date = values.graduation_date.format('YYYY-MM-DD');
      }
      if (values.available_date) {
        values.available_date = values.available_date.format('YYYY-MM-DD');
      }

      await recruitmentAPI.createApplication(values);
      message.success('申请提交成功');
      setApplicationModalVisible(false);
      applicationForm.resetFields();
      loadApplications();
      loadStats();
    } catch (error) {
      message.error('提交失败: ' + (error.response?.data?.message || error.message));
    }
  };

  const handleUpdateApplicationStatus = async (app, newStatus, extraData = {}) => {
    try {
      await recruitmentAPI.updateApplicationStatus(app.id, { status: newStatus, ...extraData });
      message.success('状态更新成功');
      loadApplications();
      loadStats();
      if (selectedApplication?.id === app.id) {
        const res = await recruitmentAPI.getApplication(app.id);
        if (res.success) {
          setSelectedApplication(res.data);
        }
      }
    } catch (error) {
      message.error('更新失败');
    }
  };

  const handleAddToTalentPool = async (app) => {
    try {
      await recruitmentAPI.addToTalentPoolFromApplication(app.id);
      message.success('已添加到人才库');
      loadTalentPool();
    } catch (error) {
      message.error('添加失败: ' + (error.response?.data?.message || error.message));
    }
  };

  // ==================== 面试管理 ====================

  const loadInterviews = async () => {
    setLoading(true);
    try {
      const res = await recruitmentAPI.getInterviews({
        page: interviewPagination.current,
        per_page: interviewPagination.pageSize,
      });
      if (res.success) {
        setInterviews(res.data.items || []);
        setInterviewPagination(prev => ({ ...prev, total: res.data.total }));
      }
    } catch (error) {
      message.error('加载面试列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleInterviewSubmit = async () => {
    try {
      const values = await interviewForm.validateFields();

      if (values.scheduled_time) {
        values.scheduled_time = values.scheduled_time.format('YYYY-MM-DD HH:mm:ss');
      }

      await recruitmentAPI.createInterview(values);
      message.success('面试安排成功');
      setInterviewModalVisible(false);
      interviewForm.resetFields();
      loadInterviews();
      loadStats();
    } catch (error) {
      message.error('安排失败: ' + (error.response?.data?.message || error.message));
    }
  };

  const handleCancelInterview = async (interview, reason) => {
    try {
      await recruitmentAPI.cancelInterview(interview.id, { reason });
      message.success('面试已取消');
      loadInterviews();
      loadStats();
    } catch (error) {
      message.error('取消失败');
    }
  };

  const handleEvaluationSubmit = async () => {
    try {
      const values = await evaluationForm.validateFields();
      await recruitmentAPI.createEvaluation(selectedInterview.id, values);
      message.success('评价提交成功');
      setEvaluationModalVisible(false);
      evaluationForm.resetFields();
      loadInterviews();
    } catch (error) {
      message.error('提交失败: ' + (error.response?.data?.message || error.message));
    }
  };

  // ==================== 人才库 ====================

  const loadTalentPool = async () => {
    setLoading(true);
    try {
      const res = await recruitmentAPI.getTalentPool({
        page: talentPagination.current,
        per_page: talentPagination.pageSize,
      });
      if (res.success) {
        setTalentPool(res.data.items || []);
        setTalentPagination(prev => ({ ...prev, total: res.data.total }));
      }
    } catch (error) {
      message.error('加载人才库失败');
    } finally {
      setLoading(false);
    }
  };

  // ==================== 列定义 ====================

  const jobColumns = [
    { title: '职位编码', dataIndex: 'job_code', key: 'job_code', width: 140 },
    { title: '职位名称', dataIndex: 'title', key: 'title', width: 180 },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 120,
    },
    {
      title: '工作地点',
      dataIndex: 'factory_name',
      key: 'factory_name',
      width: 100,
    },
    {
      title: '招聘人数',
      key: 'headcount',
      width: 100,
      render: (_, r) => `${r.hired_count || 0}/${r.headcount}`,
    },
    {
      title: '紧急程度',
      dataIndex: 'urgency',
      key: 'urgency',
      width: 100,
      render: (v) => (
        <Tag color={v === 'urgent' ? 'red' : v === 'normal' ? 'blue' : 'gray'}>
          {v === 'urgent' ? '紧急' : v === 'normal' ? '普通' : '低'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={jobStatusColors[status]}>{jobStatusLabels[status]}</Tag>
      ),
    },
    {
      title: '申请数',
      dataIndex: 'apply_count',
      key: 'apply_count',
      width: 80,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                setEditingJob(record);
                jobForm.setFieldsValue({
                  ...record,
                  publish_date: record.publish_date ? dayjs(record.publish_date) : null,
                  expire_date: record.expire_date ? dayjs(record.expire_date) : null,
                });
                setJobModalVisible(true);
              }}
            />
          </Tooltip>
          {record.status === 'draft' && (
            <Tooltip title="发布">
              <Button
                type="link"
                size="small"
                icon={<SendOutlined />}
                onClick={() => handlePublishJob(record)}
              />
            </Tooltip>
          )}
          {record.status === 'open' && (
            <Tooltip title="关闭">
              <Button
                type="link"
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleCloseJob(record)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="确定删除此职位?"
            onConfirm={() => handleDeleteJob(record)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const applicationColumns = [
    { title: '申请编号', dataIndex: 'application_no', key: 'application_no', width: 160 },
    { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
    { title: '手机', dataIndex: 'phone', key: 'phone', width: 130 },
    {
      title: '申请职位',
      key: 'job_title',
      width: 150,
      render: (_, r) => r.job_posting?.title,
    },
    { title: '学历', dataIndex: 'education', key: 'education', width: 80 },
    {
      title: '工作年限',
      dataIndex: 'work_experience_years',
      key: 'work_experience_years',
      width: 90,
      render: (v) => v ? `${v}年` : '-',
    },
    {
      title: '期望薪资',
      dataIndex: 'expected_salary',
      key: 'expected_salary',
      width: 100,
      render: (v) => v ? `${v}元` : '面议',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={applicationStatusColors[status]}>{applicationStatusLabels[status]}</Tag>
      ),
    },
    {
      title: '综合评分',
      dataIndex: 'overall_score',
      key: 'overall_score',
      width: 100,
      render: (v) => v ? <Progress percent={v} size="small" /> : '-',
    },
    {
      title: '申请时间',
      dataIndex: 'applied_at',
      key: 'applied_at',
      width: 160,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={async () => {
                const res = await recruitmentAPI.getApplication(record.id);
                if (res.success) {
                  setSelectedApplication(res.data);
                  setApplicationDetailVisible(true);
                }
              }}
            />
          </Tooltip>
          {record.status === 'pending' && (
            <>
              <Tooltip title="进入筛选">
                <Button
                  type="link"
                  size="small"
                  onClick={() => handleUpdateApplicationStatus(record, 'screening')}
                >
                  筛选
                </Button>
              </Tooltip>
              <Tooltip title="拒绝">
                <Button
                  type="link"
                  size="small"
                  danger
                  onClick={() => handleUpdateApplicationStatus(record, 'rejected', { rejection_reason: '不符合要求' })}
                >
                  拒绝
                </Button>
              </Tooltip>
            </>
          )}
          {(record.status === 'screening' || record.status === 'interview') && (
            <Tooltip title="安排面试">
              <Button
                type="link"
                size="small"
                icon={<CalendarOutlined />}
                onClick={() => {
                  interviewForm.setFieldsValue({ application_id: record.id });
                  setInterviewModalVisible(true);
                }}
              />
            </Tooltip>
          )}
          {record.status !== 'hired' && record.status !== 'rejected' && (
            <Tooltip title="加入人才库">
              <Button
                type="link"
                size="small"
                icon={<DatabaseOutlined />}
                onClick={() => handleAddToTalentPool(record)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  const interviewColumns = [
    {
      title: '候选人',
      key: 'candidate',
      width: 100,
      render: (_, r) => r.application?.name,
    },
    {
      title: '申请职位',
      key: 'job_title',
      width: 150,
      render: (_, r) => r.application?.job_posting?.title,
    },
    {
      title: '面试轮次',
      dataIndex: 'interview_round',
      key: 'interview_round',
      width: 90,
      render: (v) => `第${v}轮`,
    },
    {
      title: '面试类型',
      dataIndex: 'interview_type',
      key: 'interview_type',
      width: 100,
      render: (v) => {
        const types = { phone: '电话', video: '视频', onsite: '现场', technical: '技术', hr: 'HR', final: '终面' };
        return types[v] || v;
      },
    },
    {
      title: '预约时间',
      dataIndex: 'scheduled_time',
      key: 'scheduled_time',
      width: 160,
    },
    { title: '地点/链接', dataIndex: 'location', key: 'location', width: 150, ellipsis: true },
    { title: '面试官', dataIndex: 'interviewer_names', key: 'interviewer_names', width: 120 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={interviewStatusColors[status]}>{interviewStatusLabels[status]}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'scheduled' && (
            <Tooltip title="取消">
              <Popconfirm
                title="确定取消面试?"
                onConfirm={() => handleCancelInterview(record, '主动取消')}
              >
                <Button type="link" size="small" danger>取消</Button>
              </Popconfirm>
            </Tooltip>
          )}
          {(record.status === 'scheduled' || record.status === 'confirmed' || record.status === 'in_progress') && (
            <Tooltip title="提交评价">
              <Button
                type="link"
                size="small"
                icon={<StarOutlined />}
                onClick={() => {
                  setSelectedInterview(record);
                  setEvaluationModalVisible(true);
                }}
              >
                评价
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  const talentColumns = [
    { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
    { title: '手机', dataIndex: 'phone', key: 'phone', width: 130 },
    { title: '学历', dataIndex: 'education', key: 'education', width: 80 },
    {
      title: '工作年限',
      dataIndex: 'work_experience_years',
      key: 'work_experience_years',
      width: 90,
      render: (v) => v ? `${v}年` : '-',
    },
    {
      title: '人才等级',
      dataIndex: 'talent_level',
      key: 'talent_level',
      width: 100,
      render: (v) => (
        <Tag color={v === 'excellent' ? 'gold' : v === 'good' ? 'green' : 'default'}>
          {v === 'excellent' ? '优秀' : v === 'good' ? '良好' : '普通'}
        </Tag>
      ),
    },
    {
      title: '是否可联系',
      dataIndex: 'is_available',
      key: 'is_available',
      width: 100,
      render: (v) => v ? <Badge status="success" text="可联系" /> : <Badge status="default" text="暂不可" />,
    },
    {
      title: '最近联系',
      dataIndex: 'last_contact_date',
      key: 'last_contact_date',
      width: 120,
    },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
    {
      title: '加入时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="招聘中职位"
                value={stats.jobs?.open || 0}
                suffix={`/ ${stats.jobs?.total || 0}`}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="待处理申请"
                value={stats.applications?.pending || 0}
                suffix={`/ ${stats.applications?.total || 0}`}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="待面试"
                value={stats.interviews?.scheduled || 0}
                suffix={`/ ${stats.interviews?.total || 0}`}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="已录用"
                value={stats.applications?.hired || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 职位发布 Tab */}
          <TabPane tab={<span><TeamOutlined />职位发布</span>} key="jobs">
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setEditingJob(null);
                  jobForm.resetFields();
                  setJobModalVisible(true);
                }}
              >
                新增职位
              </Button>
              <Select
                style={{ width: 120 }}
                placeholder="状态筛选"
                allowClear
                value={jobFilters.status || undefined}
                onChange={(v) => setJobFilters({ ...jobFilters, status: v || '' })}
              >
                <Select.Option value="open">招聘中</Select.Option>
                <Select.Option value="draft">草稿</Select.Option>
                <Select.Option value="closed">已关闭</Select.Option>
                <Select.Option value="filled">已招满</Select.Option>
              </Select>
              <Input.Search
                placeholder="搜索职位"
                style={{ width: 200 }}
                onSearch={(v) => setJobFilters({ ...jobFilters, search: v })}
                allowClear
              />
              <Button icon={<ReloadOutlined />} onClick={loadJobs}>刷新</Button>
            </Space>
            <Table
              columns={jobColumns}
              dataSource={jobs}
              rowKey="id"
              loading={loading}
              pagination={{
                ...jobPagination,
                onChange: (page, pageSize) => setJobPagination({ ...jobPagination, current: page, pageSize }),
              }}
              scroll={{ x: 1400 }}
            />
          </TabPane>

          {/* 应聘申请 Tab */}
          <TabPane tab={<span><UserAddOutlined />应聘申请</span>} key="applications">
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  applicationForm.resetFields();
                  setApplicationModalVisible(true);
                }}
              >
                新增申请
              </Button>
              <Select
                style={{ width: 200 }}
                placeholder="职位筛选"
                allowClear
                showSearch
                optionFilterProp="children"
                value={appFilters.job_id || undefined}
                onChange={(v) => setAppFilters({ ...appFilters, job_id: v || '' })}
              >
                {jobs.filter(j => j.status === 'open').map(j => (
                  <Select.Option key={j.id} value={j.id}>{j.title}</Select.Option>
                ))}
              </Select>
              <Select
                style={{ width: 120 }}
                placeholder="状态筛选"
                allowClear
                value={appFilters.status || undefined}
                onChange={(v) => setAppFilters({ ...appFilters, status: v || '' })}
              >
                {Object.entries(applicationStatusLabels).map(([k, v]) => (
                  <Select.Option key={k} value={k}>{v}</Select.Option>
                ))}
              </Select>
              <Input.Search
                placeholder="搜索姓名/手机"
                style={{ width: 200 }}
                onSearch={(v) => setAppFilters({ ...appFilters, search: v })}
                allowClear
              />
              <Button icon={<ReloadOutlined />} onClick={loadApplications}>刷新</Button>
            </Space>
            <Table
              columns={applicationColumns}
              dataSource={applications}
              rowKey="id"
              loading={loading}
              pagination={{
                ...appPagination,
                onChange: (page, pageSize) => setAppPagination({ ...appPagination, current: page, pageSize }),
              }}
              scroll={{ x: 1600 }}
            />
          </TabPane>

          {/* 面试安排 Tab */}
          <TabPane tab={<span><CalendarOutlined />面试安排</span>} key="interviews">
            <Space style={{ marginBottom: 16 }}>
              <Button icon={<ReloadOutlined />} onClick={loadInterviews}>刷新</Button>
            </Space>
            <Table
              columns={interviewColumns}
              dataSource={interviews}
              rowKey="id"
              loading={loading}
              pagination={{
                ...interviewPagination,
                onChange: (page, pageSize) => setInterviewPagination({ ...interviewPagination, current: page, pageSize }),
              }}
              scroll={{ x: 1300 }}
            />
          </TabPane>

          {/* 人才库 Tab */}
          <TabPane tab={<span><DatabaseOutlined />人才库</span>} key="talent">
            <Space style={{ marginBottom: 16 }}>
              <Button icon={<ReloadOutlined />} onClick={loadTalentPool}>刷新</Button>
            </Space>
            <Table
              columns={talentColumns}
              dataSource={talentPool}
              rowKey="id"
              loading={loading}
              pagination={{
                ...talentPagination,
                onChange: (page, pageSize) => setTalentPagination({ ...talentPagination, current: page, pageSize }),
              }}
              scroll={{ x: 1100 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 职位编辑 Modal */}
      <Modal
        title={editingJob ? '编辑职位' : '新增职位'}
        open={jobModalVisible}
        onOk={handleJobSubmit}
        onCancel={() => { setJobModalVisible(false); setEditingJob(null); }}
        width={800}
      >
        <Form form={jobForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="title" label="职位名称" rules={[{ required: true }]}>
                <Input placeholder="请输入职位名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="department_id" label="所属部门">
                <Select placeholder="选择部门" allowClear showSearch optionFilterProp="children">
                  {departments.map(d => (
                    <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="factory_id" label="工作地点">
                <Select placeholder="选择工厂" allowClear>
                  {factories.map(f => (
                    <Select.Option key={f.id} value={f.id}>{f.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="headcount" label="招聘人数" initialValue={1}>
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="urgency" label="紧急程度" initialValue="normal">
                <Select>
                  <Select.Option value="urgent">紧急</Select.Option>
                  <Select.Option value="normal">普通</Select.Option>
                  <Select.Option value="low">低</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="education_requirement" label="学历要求">
                <Select placeholder="选择学历" allowClear>
                  <Select.Option value="初中">初中</Select.Option>
                  <Select.Option value="高中">高中</Select.Option>
                  <Select.Option value="大专">大专</Select.Option>
                  <Select.Option value="本科">本科</Select.Option>
                  <Select.Option value="硕士">硕士</Select.Option>
                  <Select.Option value="博士">博士</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="experience_years" label="经验要求(年)">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="不限则留空" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="job_type" label="工作类型" initialValue="full_time">
                <Select>
                  <Select.Option value="full_time">全职</Select.Option>
                  <Select.Option value="part_time">兼职</Select.Option>
                  <Select.Option value="intern">实习</Select.Option>
                  <Select.Option value="contract">合同工</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="salary_min" label="薪资下限">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="元" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="salary_max" label="薪资上限">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="元" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="salary_negotiable" label="薪资面议" valuePropName="checked" initialValue={true}>
                <Select>
                  <Select.Option value={true}>是</Select.Option>
                  <Select.Option value={false}>否</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="职位描述">
            <TextArea rows={3} placeholder="请输入职位描述" />
          </Form.Item>
          <Form.Item name="requirements" label="任职要求">
            <TextArea rows={3} placeholder="请输入任职要求" />
          </Form.Item>
          <Form.Item name="benefits" label="福利待遇">
            <TextArea rows={2} placeholder="请输入福利待遇" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="publish_date" label="发布日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expire_date" label="截止日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 应聘申请 Modal */}
      <Modal
        title="新增应聘申请"
        open={applicationModalVisible}
        onOk={handleApplicationSubmit}
        onCancel={() => setApplicationModalVisible(false)}
        width={700}
      >
        <Form form={applicationForm} layout="vertical">
          <Form.Item name="job_posting_id" label="应聘职位" rules={[{ required: true }]}>
            <Select placeholder="选择职位" showSearch optionFilterProp="children">
              {jobs.filter(j => j.status === 'open').map(j => (
                <Select.Option key={j.id} value={j.id}>{j.title}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
                <Input placeholder="请输入姓名" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="phone" label="手机号码" rules={[{ required: true }]}>
                <Input placeholder="请输入手机号码" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="gender" label="性别">
                <Select placeholder="选择性别" allowClear>
                  <Select.Option value="男">男</Select.Option>
                  <Select.Option value="女">女</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="education" label="学历">
                <Select placeholder="选择学历" allowClear>
                  <Select.Option value="初中">初中</Select.Option>
                  <Select.Option value="高中">高中</Select.Option>
                  <Select.Option value="大专">大专</Select.Option>
                  <Select.Option value="本科">本科</Select.Option>
                  <Select.Option value="硕士">硕士</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="work_experience_years" label="工作年限">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="年" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="expected_salary" label="期望薪资">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="元" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="email" label="邮箱">
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="available_date" label="可入职日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="source" label="来源" initialValue="direct">
            <Select>
              <Select.Option value="direct">直接申请</Select.Option>
              <Select.Option value="referral">内部推荐</Select.Option>
              <Select.Option value="job_site">招聘网站</Select.Option>
              <Select.Option value="campus">校园招聘</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 面试安排 Modal */}
      <Modal
        title="安排面试"
        open={interviewModalVisible}
        onOk={handleInterviewSubmit}
        onCancel={() => setInterviewModalVisible(false)}
        width={600}
      >
        <Form form={interviewForm} layout="vertical">
          <Form.Item name="application_id" label="申请ID" rules={[{ required: true }]}>
            <InputNumber disabled style={{ width: '100%' }} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="interview_type" label="面试类型" initialValue="onsite" rules={[{ required: true }]}>
                <Select>
                  <Select.Option value="phone">电话面试</Select.Option>
                  <Select.Option value="video">视频面试</Select.Option>
                  <Select.Option value="onsite">现场面试</Select.Option>
                  <Select.Option value="technical">技术面试</Select.Option>
                  <Select.Option value="hr">HR面试</Select.Option>
                  <Select.Option value="final">终面</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="duration_minutes" label="预计时长(分钟)" initialValue={60}>
                <InputNumber min={15} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="scheduled_time" label="预约时间" rules={[{ required: true }]}>
            <DatePicker showTime format="YYYY-MM-DD HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="location" label="面试地点">
            <Input placeholder="请输入面试地点" />
          </Form.Item>
          <Form.Item name="meeting_link" label="视频会议链接">
            <Input placeholder="如为视频面试，请输入会议链接" />
          </Form.Item>
          <Form.Item name="interviewer_names" label="面试官">
            <Input placeholder="请输入面试官姓名，多人用逗号分隔" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={2} placeholder="面试备注" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 面试评价 Modal */}
      <Modal
        title="面试评价"
        open={evaluationModalVisible}
        onOk={handleEvaluationSubmit}
        onCancel={() => { setEvaluationModalVisible(false); setSelectedInterview(null); }}
        width={600}
      >
        <Form form={evaluationForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="technical_score" label="技术能力">
                <Rate count={5} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="communication_score" label="沟通能力">
                <Rate count={5} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="teamwork_score" label="团队协作">
                <Rate count={5} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="problem_solving_score" label="问题解决">
                <Rate count={5} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="culture_fit_score" label="文化匹配">
                <Rate count={5} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="overall_score" label="综合评分" rules={[{ required: true }]}>
                <Rate count={5} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="strengths" label="优点">
            <TextArea rows={2} placeholder="候选人的优点" />
          </Form.Item>
          <Form.Item name="weaknesses" label="不足">
            <TextArea rows={2} placeholder="候选人的不足" />
          </Form.Item>
          <Form.Item name="recommendation" label="推荐意见" rules={[{ required: true }]}>
            <Select placeholder="选择推荐意见">
              <Select.Option value="strong_yes">强烈推荐</Select.Option>
              <Select.Option value="yes">推荐</Select.Option>
              <Select.Option value="neutral">中立</Select.Option>
              <Select.Option value="no">不推荐</Select.Option>
              <Select.Option value="strong_no">强烈不推荐</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="recommendation_reason" label="推荐理由">
            <TextArea rows={2} placeholder="请说明推荐/不推荐的理由" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 申请详情 Modal */}
      <Modal
        title="申请详情"
        open={applicationDetailVisible}
        onCancel={() => { setApplicationDetailVisible(false); setSelectedApplication(null); }}
        footer={null}
        width={800}
      >
        {selectedApplication && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="申请编号">{selectedApplication.application_no}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={applicationStatusColors[selectedApplication.status]}>
                  {applicationStatusLabels[selectedApplication.status]}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="姓名">{selectedApplication.name}</Descriptions.Item>
              <Descriptions.Item label="手机">{selectedApplication.phone}</Descriptions.Item>
              <Descriptions.Item label="邮箱">{selectedApplication.email}</Descriptions.Item>
              <Descriptions.Item label="性别">{selectedApplication.gender}</Descriptions.Item>
              <Descriptions.Item label="学历">{selectedApplication.education}</Descriptions.Item>
              <Descriptions.Item label="专业">{selectedApplication.major}</Descriptions.Item>
              <Descriptions.Item label="毕业院校">{selectedApplication.school}</Descriptions.Item>
              <Descriptions.Item label="工作年限">{selectedApplication.work_experience_years}年</Descriptions.Item>
              <Descriptions.Item label="当前公司">{selectedApplication.current_company}</Descriptions.Item>
              <Descriptions.Item label="当前职位">{selectedApplication.current_position}</Descriptions.Item>
              <Descriptions.Item label="期望薪资">{selectedApplication.expected_salary}元</Descriptions.Item>
              <Descriptions.Item label="可入职日期">{selectedApplication.available_date}</Descriptions.Item>
              <Descriptions.Item label="来源">{selectedApplication.source}</Descriptions.Item>
              <Descriptions.Item label="申请时间">{selectedApplication.applied_at}</Descriptions.Item>
              <Descriptions.Item label="综合评分" span={2}>
                {selectedApplication.overall_score ? (
                  <Progress percent={selectedApplication.overall_score} style={{ width: 200 }} />
                ) : '-'}
              </Descriptions.Item>
            </Descriptions>

            <Divider>面试记录</Divider>
            {selectedApplication.interviews?.length > 0 ? (
              <Table
                dataSource={selectedApplication.interviews}
                rowKey="id"
                size="small"
                columns={[
                  { title: '轮次', dataIndex: 'interview_round', render: v => `第${v}轮` },
                  { title: '类型', dataIndex: 'interview_type' },
                  { title: '时间', dataIndex: 'scheduled_time' },
                  { title: '状态', dataIndex: 'status', render: s => <Tag color={interviewStatusColors[s]}>{interviewStatusLabels[s]}</Tag> },
                ]}
                pagination={false}
              />
            ) : (
              <Text type="secondary">暂无面试记录</Text>
            )}

            <Divider />
            <Space>
              {selectedApplication.status === 'interview' && (
                <Button
                  type="primary"
                  onClick={() => {
                    Modal.confirm({
                      title: '发送Offer',
                      content: (
                        <Form id="offerForm" layout="vertical">
                          <Form.Item label="Offer薪资" name="offer_salary">
                            <InputNumber min={0} style={{ width: '100%' }} />
                          </Form.Item>
                        </Form>
                      ),
                      onOk: () => handleUpdateApplicationStatus(selectedApplication, 'offer'),
                    });
                  }}
                >
                  发送Offer
                </Button>
              )}
              {selectedApplication.status === 'offer' && (
                <Button
                  type="primary"
                  onClick={() => handleUpdateApplicationStatus(selectedApplication, 'hired')}
                >
                  确认录用
                </Button>
              )}
              {selectedApplication.status !== 'hired' && selectedApplication.status !== 'rejected' && (
                <Button
                  danger
                  onClick={() => handleUpdateApplicationStatus(selectedApplication, 'rejected', { rejection_reason: '不符合要求' })}
                >
                  拒绝
                </Button>
              )}
            </Space>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RecruitmentManagement;
