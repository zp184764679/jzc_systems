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
  Switch,
  InputNumber,
  Select,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { baseDataAPI } from '../services/api';

const { Search } = Input;

const BaseDataManagement = () => {
  const [activeTab, setActiveTab] = useState('factories');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch departments
  const { data: departmentsData, isLoading: loadingDepts } = useQuery({
    queryKey: ['departments', searchKeyword],
    queryFn: () => baseDataAPI.getDepartments(searchKeyword, false),
    enabled: activeTab === 'departments',
  });
  const departments = departmentsData?.data || [];

  // Fetch positions
  const { data: positionsData, isLoading: loadingPositions } = useQuery({
    queryKey: ['positions', searchKeyword],
    queryFn: () => baseDataAPI.getPositions(searchKeyword, false),
    enabled: activeTab === 'positions',
  });
  const positions = positionsData?.data || [];

  // Fetch teams
  const { data: teamsData, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams', searchKeyword],
    queryFn: () => baseDataAPI.getTeams(searchKeyword, false),
    enabled: activeTab === 'teams',
  });
  const teams = teamsData?.data || [];

  // Fetch factories
  const { data: factoriesData, isLoading: loadingFactories } = useQuery({
    queryKey: ['factories', searchKeyword],
    queryFn: () => baseDataAPI.getFactories(searchKeyword, false),
    enabled: activeTab === 'factories',
  });
  const factories = factoriesData?.data || [];

  // Fetch position categories
  const { data: categoriesData } = useQuery({
    queryKey: ['positionCategories'],
    queryFn: () => baseDataAPI.getPositionCategories(),
  });
  const categories = categoriesData?.data || [];

  // Mutations for departments
  const createDeptMutation = useMutation({
    mutationFn: (data) => baseDataAPI.createDepartment(data),
    onSuccess: () => {
      message.success('部门创建成功');
      queryClient.invalidateQueries(['departments']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '创建失败');
    },
  });

  const updateDeptMutation = useMutation({
    mutationFn: ({ id, data }) => baseDataAPI.updateDepartment(id, data),
    onSuccess: () => {
      message.success('部门更新成功');
      queryClient.invalidateQueries(['departments']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '更新失败');
    },
  });

  const deleteDeptMutation = useMutation({
    mutationFn: (id) => baseDataAPI.deleteDepartment(id),
    onSuccess: () => {
      message.success('部门已禁用');
      queryClient.invalidateQueries(['departments']);
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '删除失败');
    },
  });

  // Mutations for positions
  const createPosMutation = useMutation({
    mutationFn: (data) => baseDataAPI.createPosition(data),
    onSuccess: () => {
      message.success('职位创建成功');
      queryClient.invalidateQueries(['positions']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '创建失败');
    },
  });

  const updatePosMutation = useMutation({
    mutationFn: ({ id, data }) => baseDataAPI.updatePosition(id, data),
    onSuccess: () => {
      message.success('职位更新成功');
      queryClient.invalidateQueries(['positions']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '更新失败');
    },
  });

  const deletePosMutation = useMutation({
    mutationFn: (id) => baseDataAPI.deletePosition(id),
    onSuccess: () => {
      message.success('职位已禁用');
      queryClient.invalidateQueries(['positions']);
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '删除失败');
    },
  });

  // Mutations for teams
  const createTeamMutation = useMutation({
    mutationFn: (data) => baseDataAPI.createTeam(data),
    onSuccess: () => {
      message.success('团队创建成功');
      queryClient.invalidateQueries(['teams']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '创建失败');
    },
  });

  const updateTeamMutation = useMutation({
    mutationFn: ({ id, data }) => baseDataAPI.updateTeam(id, data),
    onSuccess: () => {
      message.success('团队更新成功');
      queryClient.invalidateQueries(['teams']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '更新失败');
    },
  });

  const deleteTeamMutation = useMutation({
    mutationFn: (id) => baseDataAPI.deleteTeam(id),
    onSuccess: () => {
      message.success('团队已禁用');
      queryClient.invalidateQueries(['teams']);
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '删除失败');
    },
  });

  // Mutations for factories
  const createFactoryMutation = useMutation({
    mutationFn: (data) => baseDataAPI.createFactory(data),
    onSuccess: () => {
      message.success('工厂创建成功');
      queryClient.invalidateQueries(['factories']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '创建失败');
    },
  });

  const updateFactoryMutation = useMutation({
    mutationFn: ({ id, data }) => baseDataAPI.updateFactory(id, data),
    onSuccess: () => {
      message.success('工厂更新成功');
      queryClient.invalidateQueries(['factories']);
      handleModalClose();
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '更新失败');
    },
  });

  const deleteFactoryMutation = useMutation({
    mutationFn: (id) => baseDataAPI.deleteFactory(id),
    onSuccess: () => {
      message.success('工厂已禁用');
      queryClient.invalidateQueries(['factories']);
    },
    onError: (error) => {
      message.error(error.response?.data?.error || '删除失败');
    },
  });

  const handleCreate = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true, sort_order: 0 });
    setIsModalOpen(true);
  };

  const handleEdit = (record) => {
    setEditingItem(record);
    form.setFieldsValue(record);
    setIsModalOpen(true);
  };

  const handleDelete = (id) => {
    if (activeTab === 'departments') {
      deleteDeptMutation.mutate(id);
    } else if (activeTab === 'positions') {
      deletePosMutation.mutate(id);
    } else if (activeTab === 'teams') {
      deleteTeamMutation.mutate(id);
    } else if (activeTab === 'factories') {
      deleteFactoryMutation.mutate(id);
    }
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setEditingItem(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (activeTab === 'departments') {
        if (editingItem) {
          updateDeptMutation.mutate({ id: editingItem.id, data: values });
        } else {
          createDeptMutation.mutate(values);
        }
      } else if (activeTab === 'positions') {
        if (editingItem) {
          updatePosMutation.mutate({ id: editingItem.id, data: values });
        } else {
          createPosMutation.mutate(values);
        }
      } else if (activeTab === 'teams') {
        if (editingItem) {
          updateTeamMutation.mutate({ id: editingItem.id, data: values });
        } else {
          createTeamMutation.mutate(values);
        }
      } else if (activeTab === 'factories') {
        if (editingItem) {
          updateFactoryMutation.mutate({ id: editingItem.id, data: values });
        } else {
          createFactoryMutation.mutate(values);
        }
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Department columns
  const deptColumns = [
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => (
        <span style={{ color: active ? '#52c41a' : '#ff4d4f' }}>
          {active ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认禁用"
            description="确定要禁用该部门吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              禁用
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Position columns
  const posColumns = [
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (cat) => {
        const found = categories.find(c => c.value === cat);
        return found ? found.label : cat;
      },
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => (
        <span style={{ color: active ? '#52c41a' : '#ff4d4f' }}>
          {active ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认禁用"
            description="确定要禁用该职位吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              禁用
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Team columns
  const teamColumns = [
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '所属部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 150,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => (
        <span style={{ color: active ? '#52c41a' : '#ff4d4f' }}>
          {active ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认禁用"
            description="确定要禁用该团队吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              禁用
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Department form
  const deptForm = (
    <>
      <Form.Item
        label="部门编码"
        name="code"
        rules={[{ required: true, message: '请输入部门编码' }]}
      >
        <Input placeholder="请输入部门编码" />
      </Form.Item>
      <Form.Item
        label="部门名称"
        name="name"
        rules={[{ required: true, message: '请输入部门名称' }]}
      >
        <Input placeholder="请输入部门名称" />
      </Form.Item>
      <Form.Item label="描述" name="description">
        <Input.TextArea rows={3} placeholder="请输入描述" />
      </Form.Item>
      <Form.Item label="排序" name="sort_order">
        <InputNumber min={0} placeholder="排序号" style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="状态" name="is_active" valuePropName="checked">
        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
      </Form.Item>
    </>
  );

  // Position form
  const posForm = (
    <>
      <Form.Item
        label="职位编码"
        name="code"
        rules={[{ required: true, message: '请输入职位编码' }]}
      >
        <Input placeholder="请输入职位编码" />
      </Form.Item>
      <Form.Item
        label="职位名称"
        name="name"
        rules={[{ required: true, message: '请输入职位名称' }]}
      >
        <Input placeholder="请输入职位名称" />
      </Form.Item>
      <Form.Item label="类别" name="category">
        <Select placeholder="请选择类别" allowClear>
          {categories.map(cat => (
            <Select.Option key={cat.value} value={cat.value}>
              {cat.label}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item label="级别" name="level">
        <InputNumber min={1} max={20} placeholder="职位级别" style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="描述" name="description">
        <Input.TextArea rows={3} placeholder="请输入描述" />
      </Form.Item>
      <Form.Item label="排序" name="sort_order">
        <InputNumber min={0} placeholder="排序号" style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="状态" name="is_active" valuePropName="checked">
        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
      </Form.Item>
    </>
  );

  // Team form
  const teamForm = (
    <>
      <Form.Item
        label="团队编码"
        name="code"
        rules={[{ required: true, message: '请输入团队编码' }]}
      >
        <Input placeholder="请输入团队编码" />
      </Form.Item>
      <Form.Item
        label="团队名称"
        name="name"
        rules={[{ required: true, message: '请输入团队名称' }]}
      >
        <Input placeholder="请输入团队名称" />
      </Form.Item>
      <Form.Item label="所属部门" name="department_id">
        <Select placeholder="请选择所属部门" allowClear showSearch optionFilterProp="children">
          {departments.map(dept => (
            <Select.Option key={dept.id} value={dept.id}>
              {dept.name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>
      <Form.Item label="描述" name="description">
        <Input.TextArea rows={3} placeholder="请输入描述" />
      </Form.Item>
      <Form.Item label="排序" name="sort_order">
        <InputNumber min={0} placeholder="排序号" style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="状态" name="is_active" valuePropName="checked">
        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
      </Form.Item>
    </>
  );

  // Factory columns
  const factoryColumns = [
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 120,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '城市',
      dataIndex: 'city',
      key: 'city',
      width: 100,
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
      ellipsis: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => (
        <span style={{ color: active ? '#52c41a' : '#ff4d4f' }}>
          {active ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认禁用"
            description="确定要禁用该工厂吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              禁用
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Factory form
  const factoryForm = (
    <>
      <Form.Item
        label="工厂编码"
        name="code"
        rules={[{ required: true, message: '请输入工厂编码' }]}
      >
        <Input placeholder="请输入工厂编码" />
      </Form.Item>
      <Form.Item
        label="工厂名称"
        name="name"
        rules={[{ required: true, message: '请输入工厂名称' }]}
      >
        <Input placeholder="请输入工厂名称" />
      </Form.Item>
      <Form.Item label="城市" name="city">
        <Input placeholder="请输入所在城市" />
      </Form.Item>
      <Form.Item label="地址" name="address">
        <Input placeholder="请输入详细地址" />
      </Form.Item>
      <Form.Item label="描述" name="description">
        <Input.TextArea rows={3} placeholder="请输入描述" />
      </Form.Item>
      <Form.Item label="排序" name="sort_order">
        <InputNumber min={0} placeholder="排序号" style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="状态" name="is_active" valuePropName="checked">
        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
      </Form.Item>
    </>
  );

  const getModalTitle = () => {
    const action = editingItem ? '编辑' : '新增';
    if (activeTab === 'departments') return `${action}部门`;
    if (activeTab === 'positions') return `${action}职位`;
    if (activeTab === 'teams') return `${action}团队`;
    if (activeTab === 'factories') return `${action}工厂`;
    return action;
  };

  const getFormContent = () => {
    if (activeTab === 'departments') return deptForm;
    if (activeTab === 'positions') return posForm;
    if (activeTab === 'teams') return teamForm;
    if (activeTab === 'factories') return factoryForm;
    return null;
  };

  const getTableData = () => {
    if (activeTab === 'departments') return departments;
    if (activeTab === 'positions') return positions;
    if (activeTab === 'teams') return teams;
    if (activeTab === 'factories') return factories;
    return [];
  };

  const getTableColumns = () => {
    if (activeTab === 'departments') return deptColumns;
    if (activeTab === 'positions') return posColumns;
    if (activeTab === 'teams') return teamColumns;
    if (activeTab === 'factories') return factoryColumns;
    return [];
  };

  const getLoading = () => {
    if (activeTab === 'departments') return loadingDepts;
    if (activeTab === 'positions') return loadingPositions;
    if (activeTab === 'teams') return loadingTeams;
    if (activeTab === 'factories') return loadingFactories;
    return false;
  };

  const isPending = () => {
    return (
      createDeptMutation.isPending ||
      updateDeptMutation.isPending ||
      createPosMutation.isPending ||
      updatePosMutation.isPending ||
      createTeamMutation.isPending ||
      updateTeamMutation.isPending ||
      createFactoryMutation.isPending ||
      updateFactoryMutation.isPending
    );
  };

  const tabItems = [
    {
      key: 'factories',
      label: '工厂管理',
    },
    {
      key: 'departments',
      label: '部门管理',
    },
    {
      key: 'positions',
      label: '职位管理',
    },
    {
      key: 'teams',
      label: '团队管理',
    },
  ];

  // Mobile-friendly columns
  const getMobileColumns = () => {
    return [
      {
        title: '信息',
        key: 'info',
        render: (_, record) => (
          <div>
            <div style={{ fontWeight: 'bold' }}>{record.name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>{record.code}</div>
            {record.description && (
              <div style={{ fontSize: '12px', color: '#999', marginTop: 4 }}>
                {record.description.length > 30 ? record.description.slice(0, 30) + '...' : record.description}
              </div>
            )}
          </div>
        ),
      },
      {
        title: '状态',
        dataIndex: 'is_active',
        key: 'is_active',
        width: 60,
        render: (active) => (
          <span style={{ color: active ? '#52c41a' : '#ff4d4f', fontSize: '12px' }}>
            {active ? '启用' : '禁用'}
          </span>
        ),
      },
      {
        title: '操作',
        key: 'action',
        width: 70,
        render: (_, record) => (
          <Space direction="vertical" size={0}>
            <Button type="link" size="small" onClick={() => handleEdit(record)}>
              编辑
            </Button>
            <Popconfirm
              title="确认禁用"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" danger>
                禁用
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ];
  };

  return (
    <Card bodyStyle={{ padding: isMobile ? 12 : 24 }}>
      <Space direction="vertical" style={{ width: '100%' }} size={isMobile ? "middle" : "large"}>
        <Tabs
          activeKey={activeTab}
          items={tabItems}
          size={isMobile ? 'small' : 'middle'}
          onChange={(key) => {
            setActiveTab(key);
            setSearchKeyword('');
          }}
        />

        <div style={{
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          justifyContent: 'space-between',
          gap: isMobile ? '12px' : '16px'
        }}>
          <Search
            placeholder="搜索编码或名称"
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
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
            style={{ width: isMobile ? '100%' : 'auto' }}
          >
            新增
          </Button>
        </div>

        <Table
          columns={isMobile ? getMobileColumns() : getTableColumns()}
          dataSource={getTableData()}
          rowKey="id"
          loading={getLoading()}
          size={isMobile ? 'small' : 'middle'}
          pagination={{
            defaultPageSize: 10,
            showSizeChanger: !isMobile,
            showTotal: isMobile ? undefined : (total) => `共 ${total} 条记录`,
            pageSizeOptions: ['10', '20', '50'],
            size: isMobile ? 'small' : 'default',
          }}
        />

        <Modal
          title={getModalTitle()}
          open={isModalOpen}
          onOk={handleSubmit}
          onCancel={handleModalClose}
          width={isMobile ? '100%' : 600}
          style={isMobile ? { top: 20, maxWidth: '100vw', margin: '0 8px' } : undefined}
          confirmLoading={isPending()}
          okText="保存"
          cancelText="取消"
        >
          <Form form={form} layout="vertical" autoComplete="off">
            {getFormContent()}
          </Form>
        </Modal>
      </Space>
    </Card>
  );
};

export default BaseDataManagement;
