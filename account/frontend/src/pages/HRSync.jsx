import React, { useState } from 'react';
import {
  Card,
  Button,
  Table,
  Modal,
  message,
  Typography,
  Space,
  Tag,
  Alert,
  Statistic,
  Row,
  Col,
  Checkbox,
  Input,
  Divider,
  Spin,
  Result,
} from 'antd';
import {
  SyncOutlined,
  CloudDownloadOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { hrSyncAPI } from '../services/api';

const { Title, Text } = Typography;

const HRSync = () => {
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [selectedEmpNos, setSelectedEmpNos] = useState([]);
  const [defaultPassword, setDefaultPassword] = useState('jzc123456');
  const [syncResult, setSyncResult] = useState(null);

  // 加载预览数据
  const loadPreview = async () => {
    setLoading(true);
    try {
      const data = await hrSyncAPI.previewSync();
      setPreviewData(data);
      setPreviewModalVisible(true);
    } catch (error) {
      message.error(error.message || '加载预览失败');
    } finally {
      setLoading(false);
    }
  };

  // 执行同步
  const executeSync = async () => {
    setLoading(true);
    try {
      const result = await hrSyncAPI.executeSync({ update_name: true });
      setSyncResult(result);
      message.success(result.message);
      setPreviewModalVisible(false);
    } catch (error) {
      message.error(error.message || '同步失败');
    } finally {
      setLoading(false);
    }
  };

  // 批量创建用户
  const batchCreate = async () => {
    if (selectedEmpNos.length === 0) {
      message.warning('请选择要创建的员工');
      return;
    }

    setLoading(true);
    try {
      const result = await hrSyncAPI.batchCreateUsers(selectedEmpNos, defaultPassword, []);
      setSyncResult(result);
      message.success(result.message);
      setCreateModalVisible(false);
      setSelectedEmpNos([]);
    } catch (error) {
      message.error(error.message || '批量创建失败');
    } finally {
      setLoading(false);
    }
  };

  // 匹配用户的表格列
  const matchedColumns = [
    {
      title: '用户名',
      dataIndex: 'username',
      width: 100,
    },
    {
      title: '工号',
      dataIndex: 'emp_no',
      width: 100,
    },
    {
      title: '当前姓名',
      dataIndex: 'current_name',
      width: 100,
    },
    {
      title: 'HR姓名',
      dataIndex: 'hr_name',
      width: 100,
    },
    {
      title: 'HR部门',
      dataIndex: 'hr_department',
      width: 120,
    },
    {
      title: 'HR岗位',
      dataIndex: 'hr_position',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'needs_update',
      width: 80,
      render: (needs) => (
        <Tag color={needs ? 'orange' : 'green'}>
          {needs ? '需更新' : '已同步'}
        </Tag>
      ),
    },
    {
      title: '变更内容',
      dataIndex: 'changes',
      render: (changes) => (
        <Space direction="vertical" size={0}>
          {changes?.map((c, i) => (
            <Text key={i} type="secondary" style={{ fontSize: 12 }}>{c}</Text>
          ))}
          {(!changes || changes.length === 0) && <Text type="secondary">无变更</Text>}
        </Space>
      ),
    },
  ];

  // 未匹配员工的表格列
  const unmatchedColumns = [
    {
      title: '',
      dataIndex: 'empNo',
      width: 50,
      render: (empNo) => (
        <Checkbox
          checked={selectedEmpNos.includes(empNo)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedEmpNos([...selectedEmpNos, empNo]);
            } else {
              setSelectedEmpNos(selectedEmpNos.filter(n => n !== empNo));
            }
          }}
        />
      ),
    },
    {
      title: '工号',
      dataIndex: 'empNo',
      width: 100,
    },
  ];

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Title level={4} style={{ margin: 0 }}>HR数据同步</Title>
      <Text type="secondary">从HR系统同步在职员工信息到账户系统，自动匹配工号更新部门、岗位、团队等信息</Text>

      <Row gutter={16}>
        <Col span={12}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Title level={5}>
                <SyncOutlined /> 同步现有用户
              </Title>
              <Text type="secondary">
                根据工号匹配，自动更新用户的部门、岗位、团队信息
              </Text>
              <Button
                type="primary"
                icon={<CloudDownloadOutlined />}
                onClick={loadPreview}
                loading={loading}
                size="large"
                block
              >
                预览同步
              </Button>
            </Space>
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Title level={5}>
                <UserAddOutlined /> 批量创建用户
              </Title>
              <Text type="secondary">
                为HR系统中尚未注册的在职员工批量创建账户
              </Text>
              <Button
                icon={<UserAddOutlined />}
                onClick={() => {
                  loadPreview();
                  setCreateModalVisible(true);
                }}
                loading={loading}
                size="large"
                block
              >
                选择员工创建
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 同步结果展示 */}
      {syncResult && (
        <Card>
          <Result
            status="success"
            title={syncResult.message}
            subTitle={
              syncResult.created_count !== undefined
                ? `成功创建 ${syncResult.created_count} 个用户，默认密码: ${syncResult.default_password}`
                : `更新了 ${syncResult.updated_count} 个用户`
            }
            extra={
              <Button onClick={() => setSyncResult(null)}>关闭</Button>
            }
          />
          {syncResult.updated_users?.length > 0 && (
            <>
              <Divider>更新详情</Divider>
              <Table
                dataSource={syncResult.updated_users}
                columns={[
                  { title: '用户名', dataIndex: 'username', width: 120 },
                  { title: '工号', dataIndex: 'emp_no', width: 100 },
                  { title: '变更', dataIndex: 'changes', render: (c) => c?.join('; ') },
                ]}
                rowKey="user_id"
                size="small"
                pagination={false}
              />
            </>
          )}
          {syncResult.created_users?.length > 0 && (
            <>
              <Divider>创建详情</Divider>
              <Table
                dataSource={syncResult.created_users}
                columns={[
                  { title: '用户名', dataIndex: 'username', width: 120 },
                  { title: '工号', dataIndex: 'emp_no', width: 100 },
                  { title: '姓名', dataIndex: 'full_name', width: 100 },
                  { title: '部门', dataIndex: 'department' },
                ]}
                rowKey="user_id"
                size="small"
                pagination={false}
              />
            </>
          )}
          {syncResult.errors?.length > 0 && (
            <>
              <Divider>错误信息</Divider>
              {syncResult.errors.map((err, i) => (
                <Alert key={i} message={`${err.emp_no || err.username}: ${err.error}`} type="error" style={{ marginBottom: 8 }} />
              ))}
            </>
          )}
        </Card>
      )}

      {/* 预览同步弹窗 */}
      <Modal
        title="同步预览"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        width={1000}
        footer={[
          <Button key="cancel" onClick={() => setPreviewModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="sync"
            type="primary"
            icon={<SyncOutlined />}
            onClick={executeSync}
            loading={loading}
            disabled={!previewData?.summary?.needs_update}
          >
            执行同步 ({previewData?.summary?.needs_update || 0} 个用户)
          </Button>,
        ]}
      >
        {loading && !previewData ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>正在加载HR数据...</div>
          </div>
        ) : previewData ? (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={4}>
                <Statistic title="HR在职员工" value={previewData.summary?.total_hr_employees} />
              </Col>
              <Col span={4}>
                <Statistic title="系统用户" value={previewData.summary?.total_users} />
              </Col>
              <Col span={4}>
                <Statistic
                  title="已匹配"
                  value={previewData.summary?.matched}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="需更新"
                  value={previewData.summary?.needs_update}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="未匹配用户"
                  value={previewData.summary?.unmatched_users}
                  valueStyle={{ color: '#999' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="未注册员工"
                  value={previewData.summary?.unmatched_employees}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
            </Row>

            <Divider>匹配用户详情</Divider>
            <Table
              dataSource={previewData.matched}
              columns={matchedColumns}
              rowKey="user_id"
              size="small"
              pagination={{ pageSize: 10 }}
              scroll={{ y: 300 }}
            />
          </>
        ) : null}
      </Modal>

      {/* 批量创建弹窗 */}
      <Modal
        title="批量创建用户"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          setSelectedEmpNos([]);
        }}
        width={600}
        footer={[
          <Button key="cancel" onClick={() => {
            setCreateModalVisible(false);
            setSelectedEmpNos([]);
          }}>
            取消
          </Button>,
          <Button
            key="create"
            type="primary"
            icon={<UserAddOutlined />}
            onClick={batchCreate}
            loading={loading}
            disabled={selectedEmpNos.length === 0}
          >
            创建选中用户 ({selectedEmpNos.length})
          </Button>,
        ]}
      >
        {previewData ? (
          <>
            <Alert
              message="以下员工在HR系统中存在但尚未在账户系统注册"
              type="info"
              style={{ marginBottom: 16 }}
            />

            <Space style={{ marginBottom: 16 }}>
              <Text>默认密码:</Text>
              <Input
                value={defaultPassword}
                onChange={(e) => setDefaultPassword(e.target.value)}
                style={{ width: 150 }}
              />
              <Button
                size="small"
                onClick={() => {
                  setSelectedEmpNos(previewData.unmatched_employees || []);
                }}
              >
                全选
              </Button>
              <Button size="small" onClick={() => setSelectedEmpNos([])}>
                清空
              </Button>
            </Space>

            <div style={{ maxHeight: 400, overflow: 'auto' }}>
              {(previewData.unmatched_employees || []).map(empNo => (
                <div key={empNo} style={{ padding: '4px 0' }}>
                  <Checkbox
                    checked={selectedEmpNos.includes(empNo)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEmpNos([...selectedEmpNos, empNo]);
                      } else {
                        setSelectedEmpNos(selectedEmpNos.filter(n => n !== empNo));
                      }
                    }}
                  >
                    {empNo}
                  </Checkbox>
                </div>
              ))}
              {(!previewData.unmatched_employees || previewData.unmatched_employees.length === 0) && (
                <Text type="secondary">所有HR员工都已注册</Text>
              )}
            </div>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin />
            <div style={{ marginTop: 16 }}>正在加载...</div>
          </div>
        )}
      </Modal>
    </Space>
  );
};

export default HRSync;
