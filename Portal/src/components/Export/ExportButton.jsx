/**
 * 导出按钮组件
 * 支持导出项目列表、项目报告、任务列表等
 */
import { useState } from 'react'
import { Button, Dropdown, message, Tooltip } from 'antd'
import {
  DownloadOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  LoadingOutlined
} from '@ant-design/icons'
import { exportAPI } from '../../services/api'

// 下载 blob 文件的工具函数
const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// 从响应头获取文件名
const getFilenameFromResponse = (response, defaultName) => {
  const contentDisposition = response.headers['content-disposition']
  if (contentDisposition) {
    // 尝试解析 filename*= (RFC 5987) 或 filename=
    const filenameMatch = contentDisposition.match(/filename\*?=['"]?(?:UTF-8'')?([^;\n"']+)['"]?/i)
    if (filenameMatch) {
      return decodeURIComponent(filenameMatch[1])
    }
  }
  return defaultName
}

/**
 * 项目列表导出按钮
 */
export function ProjectListExportButton({ filters = {}, style }) {
  const [loading, setLoading] = useState(null) // 'excel' | 'pdf' | null

  const handleExport = async (type) => {
    setLoading(type)
    try {
      const response = type === 'excel'
        ? await exportAPI.exportProjectsExcel(filters)
        : await exportAPI.exportProjectsPdf(filters)

      const filename = getFilenameFromResponse(
        response,
        type === 'excel' ? '项目列表.xlsx' : '项目汇总报告.pdf'
      )
      downloadBlob(response.data, filename)
      message.success(`${type === 'excel' ? 'Excel' : 'PDF'} 导出成功`)
    } catch (error) {
      console.error('导出失败:', error)
      message.error('导出失败: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(null)
    }
  }

  const menuItems = [
    {
      key: 'excel',
      icon: loading === 'excel' ? <LoadingOutlined /> : <FileExcelOutlined style={{ color: '#217346' }} />,
      label: '导出 Excel',
      onClick: () => handleExport('excel'),
      disabled: loading !== null,
    },
    {
      key: 'pdf',
      icon: loading === 'pdf' ? <LoadingOutlined /> : <FilePdfOutlined style={{ color: '#ff4d4f' }} />,
      label: '导出 PDF 报告',
      onClick: () => handleExport('pdf'),
      disabled: loading !== null,
    },
  ]

  return (
    <Dropdown menu={{ items: menuItems }} trigger={['click']}>
      <Button
        icon={loading ? <LoadingOutlined /> : <DownloadOutlined />}
        style={style}
      >
        导出
      </Button>
    </Dropdown>
  )
}

/**
 * 单项目导出按钮
 */
export function ProjectExportButton({ projectId, projectNo, style }) {
  const [loading, setLoading] = useState(null)

  const handleExport = async (type) => {
    setLoading(type)
    try {
      let response, filename
      if (type === 'pdf') {
        response = await exportAPI.exportProjectReportPdf(projectId)
        filename = getFilenameFromResponse(response, `项目报告_${projectNo}.pdf`)
      } else {
        response = await exportAPI.exportProjectTasksExcel(projectId)
        filename = getFilenameFromResponse(response, `任务列表_${projectNo}.xlsx`)
      }
      downloadBlob(response.data, filename)
      message.success('导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      message.error('导出失败: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(null)
    }
  }

  const menuItems = [
    {
      key: 'pdf',
      icon: loading === 'pdf' ? <LoadingOutlined /> : <FilePdfOutlined style={{ color: '#ff4d4f' }} />,
      label: '导出项目报告 (PDF)',
      onClick: () => handleExport('pdf'),
      disabled: loading !== null,
    },
    {
      key: 'excel',
      icon: loading === 'excel' ? <LoadingOutlined /> : <FileExcelOutlined style={{ color: '#217346' }} />,
      label: '导出任务列表 (Excel)',
      onClick: () => handleExport('excel'),
      disabled: loading !== null,
    },
  ]

  return (
    <Dropdown menu={{ items: menuItems }} trigger={['click']}>
      <Tooltip title="导出">
        <Button
          icon={loading ? <LoadingOutlined /> : <DownloadOutlined />}
          style={style}
        />
      </Tooltip>
    </Dropdown>
  )
}

/**
 * 部件番号页面导出按钮
 */
export function PartNumberExportButton({ partNumber, style }) {
  const [loading, setLoading] = useState(false)

  const handleExport = async () => {
    setLoading(true)
    try {
      const response = await exportAPI.exportPartNumberPdf(partNumber)
      const filename = getFilenameFromResponse(response, `部件番号报告_${partNumber}.pdf`)
      downloadBlob(response.data, filename)
      message.success('PDF 导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      message.error('导出失败: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Tooltip title="导出 PDF 报告">
      <Button
        icon={loading ? <LoadingOutlined /> : <FilePdfOutlined />}
        onClick={handleExport}
        loading={loading}
        style={style}
      >
        导出 PDF
      </Button>
    </Tooltip>
  )
}

export default {
  ProjectListExportButton,
  ProjectExportButton,
  PartNumberExportButton,
}
