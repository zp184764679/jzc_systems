// 角色常量定义
//
// 采购审批流程角色：
// - user (员工): 只能提交申请
// - supervisor (主管): 提交申请 + 审批 + 填写价格
// - factory_manager (厂长): 审批价格（原admin）
// - general_manager (总经理): 超额审批（金额>2000或价格偏差>5%）
// - super_admin (超级管理员): 最高权限

export const ROLES = {
  USER: 'user',
  SUPERVISOR: 'supervisor',
  FACTORY_MANAGER: 'factory_manager',  // 厂长（原admin）
  GENERAL_MANAGER: 'general_manager',  // 总经理（原super_admin审批功能）
  ADMIN: 'admin',  // 保留兼容
  SUPER_ADMIN: 'super_admin',  // 超级管理员
};

export const ROLE_LABELS = {
  [ROLES.USER]: '员工',
  [ROLES.SUPERVISOR]: '主管',
  [ROLES.FACTORY_MANAGER]: '厂长',
  [ROLES.GENERAL_MANAGER]: '总经理',
  [ROLES.ADMIN]: '管理员',  // 兼容旧数据
  [ROLES.SUPER_ADMIN]: '超级管理员',
};

export const ROLE_LEVELS = {
  [ROLES.USER]: 0,
  [ROLES.SUPERVISOR]: 1,
  [ROLES.FACTORY_MANAGER]: 2,
  [ROLES.GENERAL_MANAGER]: 3,
  [ROLES.ADMIN]: 2,  // 兼容，等同于厂长
  [ROLES.SUPER_ADMIN]: 4,
};

// 采购订单状态常量
export const PO_STATUS = {
  CREATED: 'created',
  PENDING_ADMIN_CONFIRMATION: 'pending_admin_confirmation',
  PENDING_SUPER_ADMIN_CONFIRMATION: 'pending_super_admin_confirmation',
  CONFIRMED: 'confirmed',
  RECEIVED: 'received',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
};

export const PO_STATUS_LABELS = {
  [PO_STATUS.CREATED]: '已创建',
  [PO_STATUS.PENDING_ADMIN_CONFIRMATION]: '待管理员确认',
  [PO_STATUS.PENDING_SUPER_ADMIN_CONFIRMATION]: '待超管确认',
  [PO_STATUS.CONFIRMED]: '已确认',
  [PO_STATUS.RECEIVED]: '已收货',
  [PO_STATUS.COMPLETED]: '已完成',
  [PO_STATUS.CANCELLED]: '已取消',
};

// 状态颜色配置
export const PO_STATUS_COLORS = {
  [PO_STATUS.CREATED]: 'bg-gray-100 text-gray-800',
  [PO_STATUS.PENDING_ADMIN_CONFIRMATION]: 'bg-yellow-100 text-yellow-800',
  [PO_STATUS.PENDING_SUPER_ADMIN_CONFIRMATION]: 'bg-orange-100 text-orange-800',
  [PO_STATUS.CONFIRMED]: 'bg-green-100 text-green-800',
  [PO_STATUS.RECEIVED]: 'bg-blue-100 text-blue-800',
  [PO_STATUS.COMPLETED]: 'bg-purple-100 text-purple-800',
  [PO_STATUS.CANCELLED]: 'bg-red-100 text-red-800',
};
