import React from 'react';

/**
 * Badge 徽章组件
 * 用于显示状态、标签等
 */
export const Badge = ({
  variant = 'default',
  size = 'md',
  children,
  className = ''
}) => {
  // 变体样式
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    error: 'bg-red-100 text-red-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
    primary: 'bg-blue-500 text-white',
  };

  // 尺寸样式
  const sizes = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const variantClass = variants[variant] || variants.default;
  const sizeClass = sizes[size] || sizes.md;

  return (
    <span className={}>
      {children}
    </span>
  );
};

/**
 * 状态徽章（语义化快捷方式）
 */
export const StatusBadge = ({ status, children, className = '' }) => {
  const statusMap = {
    pending: { variant: 'warning', text: '待处理' },
    approved: { variant: 'success', text: '已批准' },
    rejected: { variant: 'danger', text: '已拒绝' },
  };

  const config = statusMap[status];

  if (!config) {
    return <Badge className={className}>{children || status}</Badge>;
  }

  return (
    <Badge variant={config.variant} className={className}>
      {children || config.text}
    </Badge>
  );
};

export default Badge;
