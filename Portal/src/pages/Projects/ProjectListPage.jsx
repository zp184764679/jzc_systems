import { useState } from 'react'
import { Button, Space, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import AllTasksTimeline from '../../components/Timeline/AllTasksTimeline'
import ProjectFormModal from '../../components/Projects/ProjectFormModal'

const { Title } = Typography

export default function ProjectListPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleProjectCreated = () => {
    // 触发 AllTasksTimeline 刷新
    setRefreshKey(prev => prev + 1)
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        marginBottom: 16,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Title level={3} style={{ margin: 0 }}>项目管理</Title>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => setShowCreateModal(true)}
            style={{ borderRadius: 8 }}
          >
            新建项目
          </Button>
        </Space>
      </div>

      {/* 任务时间轴 - 核心视图 */}
      <AllTasksTimeline key={refreshKey} />

      {/* Create Modal */}
      <ProjectFormModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleProjectCreated}
      />
    </div>
  )
}
