/**
 * 格式化工具函数集
 * 统一管理日期、货币、数字等格式化逻辑
 */

/**
 * 格式化日期时间
 */
export const formatDate = (dateString, options = {}) => {
  if (!dateString) return '-';

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';

    const defaultOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    };

    return date.toLocaleString('zh-CN', { ...defaultOptions, ...options });
  } catch (error) {
    console.error('日期格式化错误:', error);
    return '-';
  }
};

/**
 * 格式化简单货币（用于显示金额）
 */
export const formatSimpleCurrency = (amount) => {
  if (amount === null || amount === undefined || amount === '') return '-';

  try {
    const num = Number(amount);
    if (isNaN(num)) return '-';

    return ;
  } catch (error) {
    console.error('货币格式化错误:', error);
    return '-';
  }
};

/**
 * 格式化货币（完整格式）
 */
export const formatCurrency = (amount, currency = '¥') => {
  if (amount === null || amount === undefined || amount === '') return '-';

  try {
    const num = Number(amount);
    if (isNaN(num)) return '-';

    return ;
  } catch (error) {
    console.error('货币格式化错误:', error);
    return '-';
  }
};

/**
 * 格式化数字（带千分位）
 */
export const formatNumber = (number, decimals = 2) => {
  if (number === null || number === undefined || number === '') return '-';

  try {
    const num = Number(number);
    if (isNaN(num)) return '-';

    return num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  } catch (error) {
    console.error('数字格式化错误:', error);
    return '-';
  }
};

export default {
  formatDate,
  formatSimpleCurrency,
  formatCurrency,
  formatNumber,
};
