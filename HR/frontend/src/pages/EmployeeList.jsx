import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  message,
  Card,
  Popconfirm,
  Tabs,
  DatePicker,
  Select,
  InputNumber,
  Row,
  Col,
  Layout,
  Menu,
  Drawer,
  Segmented,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  UserOutlined,
  UserDeleteOutlined,
  StopOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { employeeAPI, baseDataAPI } from '../services/api';

const { Search } = Input;
const { Sider, Content } = Layout;

const EmployeeList = () => {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 'all' or position name
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch employees with pagination - 默认只查在职员工
  const { data: employeesData, isLoading } = useQuery({
    queryKey: ['employees', searchKeyword, selectedDepartment, currentPage, pageSize],
    queryFn: () => employeeAPI.getEmployees({
      search: searchKeyword,
      department: selectedDepartment,
      page: currentPage,
      per_page: pageSize,
      employment_status: 'Active', // 只查在职员工
    }),
  });
  const allEmployees = employeesData?.data || [];
  const pagination = employeesData?.pagination || { total: 0, page: 1, pages: 1 };

  // Get unique departments from employees for filter (from current page data)
  const uniqueDepartments = [...new Set(allEmployees.map(emp => emp.department).filter(Boolean))].sort();

  // Get unique positions (titles) from employees
  const uniquePositions = [...new Set(allEmployees.map(emp => emp.title).filter(Boolean))].sort();

  // Filter employees based on active tab (by position) - 后端已筛选在职员工
  const employees = activeTab === 'all'
    ? allEmployees.filter(emp => !emp.is_blacklisted)
    : allEmployees.filter(emp => !emp.is_blacklisted && emp.title === activeTab);

  // 重置页码当搜索条件变化时
  useEffect(() => {
    setCurrentPage(1);
  }, [searchKeyword, selectedDepartment]);

  // Fetch departments for dropdown
  const { data: departmentsData } = useQuery({
    queryKey: ['departments'],
    queryFn: () => baseDataAPI.getDepartments('', true),
  });
  const departments = departmentsData?.data || [];

  // Fetch positions for dropdown
  const { data: positionsData } = useQuery({
    queryKey: ['positions'],
    queryFn: () => baseDataAPI.getPositions('', true),
  });
  const positions = positionsData?.data || [];

  // Fetch teams for dropdown
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: () => baseDataAPI.getTeams('', true),
  });
  const teams = teamsData?.data || [];

  // Fetch factories for dropdown
  const { data: factoriesData } = useQuery({
    queryKey: ['factories'],
    queryFn: () => baseDataAPI.getFactories('', true),
  });
  const factoriesList = factoriesData?.data || [];

  // Create employee mutation
  const createMutation = useMutation({
    mutationFn: (data) => employeeAPI.createEmployee(data),
    onSuccess: () => {
      message.success('员工创建成功');
      queryClient.invalidateQueries(['employees']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.message || '创建失败');
    },
  });

  // Update employee mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => employeeAPI.updateEmployee(id, data),
    onSuccess: () => {
      message.success('员工信息更新成功');
      queryClient.invalidateQueries(['employees']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // Delete employee mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => employeeAPI.deleteEmployee(id),
    onSuccess: () => {
      message.success('员工删除成功');
      queryClient.invalidateQueries(['employees']);
    },
    onError: (error) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // Handle create new employee
  const handleCreate = () => {
    setEditingEmployee(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  // Handle edit employee
  const handleEdit = (record) => {
    setEditingEmployee(record);

    // Format date fields for the form
    const formData = {
      ...record,
      birth_date: record.birth_date ? dayjs(record.birth_date) : null,
      hire_date: record.hire_date ? dayjs(record.hire_date) : null,
      resignation_date: record.resignation_date ? dayjs(record.resignation_date) : null,
      contract_start_date: record.contract_start_date ? dayjs(record.contract_start_date) : null,
      contract_end_date: record.contract_end_date ? dayjs(record.contract_end_date) : null,
    };

    form.setFieldsValue(formData);
    setIsModalOpen(true);
  };

  // Handle delete employee
  const handleDelete = (id) => {
    deleteMutation.mutate(id);
  };

  // Handle modal close
  const handleModalClose = () => {
    setIsModalOpen(false);
    setEditingEmployee(null);
    form.resetFields();
  };

  // Handle form submit
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      // Format date fields to YYYY-MM-DD
      const formattedData = {
        ...values,
        birth_date: values.birth_date ? dayjs(values.birth_date).format('YYYY-MM-DD') : null,
        hire_date: values.hire_date ? dayjs(values.hire_date).format('YYYY-MM-DD') : null,
        resignation_date: values.resignation_date ? dayjs(values.resignation_date).format('YYYY-MM-DD') : null,
        contract_start_date: values.contract_start_date ? dayjs(values.contract_start_date).format('YYYY-MM-DD') : null,
        contract_end_date: values.contract_end_date ? dayjs(values.contract_end_date).format('YYYY-MM-DD') : null,
      };

      if (editingEmployee) {
        updateMutation.mutate({ id: editingEmployee.id, data: formattedData });
      } else {
        createMutation.mutate(formattedData);
      }
    } catch (error) {
      console.error('Validation failed:', error);
      message.error('表单验证失败，请检查填写的内容');
    }
  };

  // Table columns
  const columns = [
    {
      title: '工号',
      dataIndex: 'empNo',
      key: 'empNo',
      width: 120,
      fixed: 'left',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 100,
      fixed: 'left',
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 120,
    },
    {
      title: '职位',
      dataIndex: 'title',
      key: 'title',
      width: 120,
    },
    {
      title: '团队',
      dataIndex: 'team',
      key: 'team',
      width: 120,
    },
    {
      title: '电话',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
    },
    {
      title: '入职日期',
      dataIndex: 'hire_date',
      key: 'hire_date',
      width: 120,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '在职状态',
      dataIndex: 'employment_status',
      key: 'employment_status',
      width: 100,
      render: (status) => {
        const statusMap = {
          'Active': { color: '#52c41a', text: '在职' },
          'Resigned': { color: '#ff4d4f', text: '离职' },
          'Probation': { color: '#1890ff', text: '试用期' },
        };
        const config = statusMap[status] || { color: '#d9d9d9', text: status || '-' };
        return <span style={{ color: config.color, fontWeight: 'bold' }}>{config.text}</span>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除该员工吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Form items for each tab
  const basicInfoItems = (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          label="工号"
          name="empNo"
          rules={[{ required: true, message: '请输入工号' }]}
        >
          <Input placeholder="请输入工号" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="姓名"
          name="name"
          rules={[{ required: true, message: '请输入姓名' }]}
        >
          <Input placeholder="请输入姓名" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="性别"
          name="gender"
        >
          <Select placeholder="请选择性别" allowClear>
            <Select.Option value="男">男</Select.Option>
            <Select.Option value="女">女</Select.Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="出生日期"
          name="birth_date"
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择出生日期" />
        </Form.Item>
      </Col>
      <Col span={24}>
        <Form.Item
          label="身份证号"
          name="id_card"
        >
          <Input placeholder="请输入身份证号" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="电话"
          name="phone"
        >
          <Input placeholder="请输入电话号码" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="邮箱"
          name="email"
        >
          <Input placeholder="请输入邮箱" />
        </Form.Item>
      </Col>
    </Row>
  );

  const workInfoItems = (
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          label="工厂"
          name="factory_id"
        >
          <Select
            placeholder="请选择工厂"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {factoriesList.map(factory => (
              <Select.Option key={factory.id} value={factory.id}>
                {factory.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="部门"
          name="department_id"
        >
          <Select
            placeholder="请选择部门"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {departments.map(dept => (
              <Select.Option key={dept.id} value={dept.id}>
                {dept.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="职位"
          name="position_id"
        >
          <Select
            placeholder="请选择职位"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {positions.map(pos => (
              <Select.Option key={pos.id} value={pos.id}>
                {pos.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="团队"
          name="team_id"
        >
          <Select
            placeholder="请选择团队"
            allowClear
            showSearch
            optionFilterProp="children"
          >
            {teams.map(team => (
              <Select.Option key={team.id} value={team.id}>
                {team.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="入职日期"
          name="hire_date"
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择入职日期" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="在职状态"
          name="employment_status"
        >
          <Select placeholder="请选择在职状态" allowClear>
            <Select.Option value="Active">在职</Select.Option>
            <Select.Option value="Resigned">离职</Select.Option>
            <Select.Option value="Probation">试用期</Select.Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="离职日期"
          name="resignation_date"
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择离职日期" />
        </Form.Item>
      </Col>
    </Row>
  );

  const contractInfoItems = (
    <Row gutter={16}>
      <Col span={24}>
        <Form.Item
          label="合同类型"
          name="contract_type"
        >
          <Select placeholder="请选择合同类型">
            <Select.Option value="全职">全职</Select.Option>
            <Select.Option value="兼职">兼职</Select.Option>
            <Select.Option value="合同工">合同工</Select.Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="合同开始日期"
          name="contract_start_date"
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择合同开始日期" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="合同结束日期"
          name="contract_end_date"
        >
          <DatePicker style={{ width: '100%' }} placeholder="请选择合同结束日期" />
        </Form.Item>
      </Col>
    </Row>
  );

  const salaryInfoItems = (
    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          label="基本工资"
          name="base_salary"
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入基本工资"
            min={0}
            precision={2}
            formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={value => value.replace(/¥\s?|(,*)/g, '')}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="绩效工资"
          name="performance_salary"
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入绩效工资"
            min={0}
            precision={2}
            formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={value => value.replace(/¥\s?|(,*)/g, '')}
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          label="总工资"
          name="total_salary"
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入总工资"
            min={0}
            precision={2}
            formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={value => value.replace(/¥\s?|(,*)/g, '')}
          />
        </Form.Item>
      </Col>
    </Row>
  );

  const contactInfoItems = (
    <Row gutter={16}>
      <Col span={24}>
        <Form.Item
          label="家庭住址"
          name="home_address"
        >
          <Input.TextArea rows={3} placeholder="请输入家庭住址" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="紧急联系人"
          name="emergency_contact"
        >
          <Input placeholder="请输入紧急联系人" />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          label="紧急联系电话"
          name="emergency_phone"
        >
          <Input placeholder="请输入紧急联系电话" />
        </Form.Item>
      </Col>
    </Row>
  );

  const otherInfoItems = (
    <Row gutter={16}>
      <Col span={24}>
        <Form.Item
          label="备注"
          name="remark"
        >
          <Input.TextArea rows={4} placeholder="请输入备注信息" />
        </Form.Item>
      </Col>
    </Row>
  );

  const tabItems = [
    {
      key: '1',
      label: '基本信息',
      children: basicInfoItems,
    },
    {
      key: '2',
      label: '工作信息',
      children: workInfoItems,
    },
    {
      key: '3',
      label: '合同信息',
      children: contractInfoItems,
    },
    {
      key: '4',
      label: '薪资信息',
      children: salaryInfoItems,
    },
    {
      key: '5',
      label: '联系信息',
      children: contactInfoItems,
    },
    {
      key: '6',
      label: '其他',
      children: otherInfoItems,
    },
  ];

  // Menu items for positions (岗位)
  const menuItems = [
    {
      key: 'all',
      icon: <UserOutlined />,
      label: `全部在职 (${pagination.total})`,
    },
    ...uniquePositions.map(pos => ({
      key: pos,
      icon: <UserOutlined />,
      label: `${pos} (${allEmployees.filter(e => e.title === pos && !e.is_blacklisted).length})`,
    })),
  ];

  // Mobile columns - simplified for small screens
  const mobileColumns = [
    {
      title: '员工信息',
      key: 'info',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
            {record.name} ({record.empNo})
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.department} - {record.title}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.phone}
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确认删除"
            description="确定要删除该员工吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Category options for mobile segmented control (显示岗位)
  const categoryOptions = [
    { label: `全部(${pagination.total})`, value: 'all' },
    ...uniquePositions.slice(0, 4).map(pos => ({  // 移动端只显示前4个岗位
      label: `${pos.length > 4 ? pos.slice(0, 4) : pos}(${allEmployees.filter(e => e.title === pos && !e.is_blacklisted).length})`,
      value: pos,
    })),
  ];

  return (
    <Card bodyStyle={{ padding: isMobile ? 12 : 24 }}>
      <Space direction="vertical" style={{ width: '100%' }} size={isMobile ? "middle" : "large"}>
        {/* Search and Action Bar */}
        <div style={{
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          justifyContent: 'space-between',
          gap: isMobile ? '12px' : '16px'
        }}>
          <div style={{
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            gap: isMobile ? '8px' : '12px',
            flex: 1
          }}>
            <Search
              placeholder={isMobile ? "搜索员工" : "搜索员工（工号、姓名、部门、职位等）"}
              allowClear
              enterButton={<SearchOutlined />}
              style={{ width: isMobile ? '100%' : 400 }}
              onSearch={setSearchKeyword}
              onChange={(e) => {
                if (!e.target.value) {
                  setSearchKeyword('');
                }
              }}
            />
            {!isMobile && (
              <Select
                placeholder="选择部门"
                allowClear
                showSearch
                style={{ width: 200 }}
                value={selectedDepartment || undefined}
                onChange={setSelectedDepartment}
                optionFilterProp="children"
              >
                {uniqueDepartments.map(dept => (
                  <Select.Option key={dept} value={dept}>
                    {dept}
                  </Select.Option>
                ))}
              </Select>
            )}
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
            style={{ width: isMobile ? '100%' : 'auto' }}
          >
            新增员工
          </Button>
        </div>

        {/* Mobile: Category Segmented Control */}
        {isMobile && (
          <Segmented
            options={categoryOptions}
            value={activeTab}
            onChange={setActiveTab}
            block
            size="small"
          />
        )}

        {/* Employee List with Sidebar Navigation */}
        <Layout style={{ background: '#fff', minHeight: isMobile ? '400px' : '600px' }}>
          {!isMobile && (
            <Sider
              width={200}
              style={{
                background: '#fff',
                borderRight: '1px solid #f0f0f0',
                maxHeight: '600px',
                overflowY: 'auto',
              }}
            >
              <Menu
                mode="inline"
                selectedKeys={[activeTab]}
                onClick={({ key }) => setActiveTab(key)}
                items={menuItems}
                style={{ borderRight: 0 }}
              />
            </Sider>
          )}
          <Content style={{ padding: isMobile ? '0' : '0 24px', minHeight: 280 }}>
            <Table
              columns={isMobile ? mobileColumns : columns}
              dataSource={employees}
              rowKey="id"
              loading={isLoading}
              scroll={isMobile ? undefined : { x: 1800 }}
              size={isMobile ? "small" : "middle"}
              pagination={{
                current: currentPage,
                pageSize: pageSize,
                total: pagination.total,
                showSizeChanger: !isMobile,
                showTotal: isMobile ? undefined : (total) => `共 ${total} 条记录`,
                pageSizeOptions: ['10', '20', '50', '100'],
                size: isMobile ? 'small' : 'default',
                onChange: (page, size) => {
                  setCurrentPage(page);
                  setPageSize(size);
                },
              }}
            />
          </Content>
        </Layout>

        {/* Create/Edit Modal */}
        <Modal
          title={editingEmployee ? '编辑员工' : '新增员工'}
          open={isModalOpen}
          onOk={handleSubmit}
          onCancel={handleModalClose}
          width={isMobile ? '100%' : 800}
          style={isMobile ? { top: 20, maxWidth: '100vw', margin: '0 8px' } : undefined}
          confirmLoading={createMutation.isPending || updateMutation.isPending}
          okText="保存"
          cancelText="取消"
        >
          <Form
            form={form}
            layout="vertical"
            autoComplete="off"
          >
            <Tabs items={tabItems} size={isMobile ? 'small' : 'middle'} />
          </Form>
        </Modal>
      </Space>
    </Card>
  );
};

export default EmployeeList;
