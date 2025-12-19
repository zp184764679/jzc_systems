import { useState, useEffect } from 'react'
import { Card, Space, Typography } from 'antd'
import { ProjectOutlined } from '@ant-design/icons'
import { projectAPI } from '../../services/api'
import ProjectsTimeline from '../../components/Timeline/ProjectsTimeline'

const { Title } = Typography

export default function TimelinePage() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const response = await projectAPI.getProjects({ page_size: 1000 })
      setProjects(response.data.projects || [])
    } catch (error) {
      console.error('Failed to fetch projects:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 页面标题 */}
      <Card
        style={{
          marginBottom: 16,
          background: '#ffffff',
          borderRadius: 12,
          border: '1px solid #e5e5e7'
        }}
        styles={{ body: { padding: '16px 24px' } }}
      >
        <Space align="center">
          <ProjectOutlined style={{ fontSize: 24, color: '#007aff' }} />
          <Title level={4} style={{ margin: 0, color: '#1d1d1f' }}>
            统一时间轴
          </Title>
          <span style={{ color: '#86868b', marginLeft: 16 }}>
            按品番号分组查看所有项目的任务进度
          </span>
        </Space>
      </Card>

      {/* 时间轴组件 */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <ProjectsTimeline projects={projects} loading={loading} />
      </div>
    </div>
  )
}
