// src/components/ManualQuoteModal.jsx
// 手动报价Modal组件
import React, { useState, useEffect } from 'react';
import { api } from '../api/http';

export default function ManualQuoteModal({ rfq, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 按品类分组物料
  const [categoryGroups, setCategoryGroups] = useState({});

  // 报价表单
  const [quoteForm, setQuoteForm] = useState({
    lead_time: 7,
    payment_terms: 90,
    notes: '手动录入',
    supplier_name: ''  // 可选的供应商名称
  });

  // 物料报价数据（按品类分组）
  const [itemPrices, setItemPrices] = useState({});

  useEffect(() => {
    // 按品类分组物料
    if (rfq && rfq.items) {
      const groups = {};
      rfq.items.forEach(item => {
        const category = item.category || '未分类';
        if (!groups[category]) {
          groups[category] = [];
        }
        groups[category].push(item);
      });
      setCategoryGroups(groups);

      // 初始化物料价格
      const prices = {};
      rfq.items.forEach(item => {
        prices[item.id] = {
          item_name: item.item_name,
          item_description: item.item_spec || '',
          quantity_requested: item.quantity,
          unit: item.unit || '个',
          unit_price: 0,
          subtotal: 0,
          category: item.category || '未分类'
        };
      });
      setItemPrices(prices);
    }
  }, [rfq]);

  // 更新物料单价
  const updateItemPrice = (itemId, unitPrice) => {
    const price = parseFloat(unitPrice) || 0;
    const item = itemPrices[itemId];
    setItemPrices(prev => ({
      ...prev,
      [itemId]: {
        ...item,
        unit_price: price,
        subtotal: price * item.quantity_requested
      }
    }));
  };

  // 计算总价
  const calculateTotal = () => {
    return Object.values(itemPrices).reduce((sum, item) => sum + (item.subtotal || 0), 0);
  };

  // 提交手动报价
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 验证每个物料都有单价
    const invalidItems = Object.values(itemPrices).filter(item => !item.unit_price || item.unit_price <= 0);
    if (invalidItems.length > 0) {
      setError('请为所有物料填写单价');
      return;
    }

    const totalPrice = calculateTotal();
    if (totalPrice <= 0) {
      setError('总价必须大于0');
      return;
    }

    try {
      setLoading(true);

      // 按品类分组报价数据
      const categoryQuotes = {};
      Object.values(itemPrices).forEach(item => {
        const category = item.category;
        if (!categoryQuotes[category]) {
          categoryQuotes[category] = {
            category: category,
            items: [],
            total_price: 0,
            lead_time: parseInt(quoteForm.lead_time),
            payment_terms: parseInt(quoteForm.payment_terms),
            notes: quoteForm.notes || '手动录入',
            supplier_name: quoteForm.supplier_name || '手动采购'
          };
        }
        categoryQuotes[category].items.push({
          item_name: item.item_name,
          item_description: item.item_description,
          quantity_requested: item.quantity_requested,
          unit: item.unit,
          unit_price: item.unit_price,
          subtotal: item.subtotal
        });
        categoryQuotes[category].total_price += item.subtotal;
      });

      // 提交报价（后端会自动创建PO）
      const response = await api.post(`/api/v1/rfqs/${rfq.id}/manual-quote`, {
        quotes: Object.values(categoryQuotes)
      });

      if (onSuccess) {
        onSuccess(response);
      }
      onClose();
    } catch (err) {
      setError(err.message || '手动报价失败');
    } finally {
      setLoading(false);
    }
  };

  const totalPrice = calculateTotal();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        {/* 头部 */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900">手动报价</h2>
            <p className="text-sm text-gray-600 mt-1">
              RFQ-{rfq?.id} | 物料数量：{rfq?.items?.length || 0} 项
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            关闭
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 错误提示 */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-300 rounded-lg flex items-start gap-3">
              <svg className="w-5 h-5 text-red-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="flex-1 text-red-700">{error}</div>
            </div>
          )}

          {/* 供应商名称（可选） */}
          <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
            <label className="block text-sm font-bold text-blue-900 mb-3">
              供应商名称（可选）
            </label>
            <input
              type="text"
              value={quoteForm.supplier_name}
              onChange={(e) => setQuoteForm({ ...quoteForm, supplier_name: e.target.value })}
              className="w-full px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-400"
              placeholder="如果有供应商名称可填写，默认为'手动采购'"
              disabled={loading}
            />
            <div className="mt-2 text-xs text-blue-700">
              💡 手动报价无需选择供应商，提交后将直接生成采购订单，等待发票上传
            </div>
          </div>

          {/* 按品类显示物料并录入价格 */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              物料报价明细
            </h3>

            <div className="space-y-4">
              {Object.entries(categoryGroups).map(([category, items]) => {
                // 获取第一个物料名称作为代表
                const firstItemName = items.length > 0 ? items[0].item_name : '';

                return (
                  <div key={category} className="border-2 border-gray-200 rounded-lg overflow-hidden">
                    {/* 品类标题 - 显示物料名称 */}
                    <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-3">
                      <h4 className="text-white font-bold flex items-center gap-2 flex-wrap">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        <span className="text-lg">{firstItemName}</span>
                        <span className="text-white/80">-</span>
                        <span className="text-sm text-white/90">{category}</span>
                        <span className="ml-auto px-2 py-1 bg-white/20 rounded text-sm">
                          {items.length} 项
                        </span>
                      </h4>
                    </div>

                  {/* 物料列表 */}
                  <div className="p-4 space-y-3">
                    {items.map(item => {
                      const priceData = itemPrices[item.id] || {};
                      return (
                        <div key={item.id} className="p-3 bg-white rounded-lg border-2 border-gray-300">
                          {/* 物料信息行 - 更清晰的格式 */}
                          <div className="mb-3 pb-3 border-b border-gray-200">
                            <div className="flex items-center gap-2 flex-wrap text-sm">
                              <span className="font-bold text-gray-900 text-base">{item.item_name}</span>
                              {item.item_spec && (
                                <>
                                  <span className="text-gray-400">|</span>
                                  <span className="text-gray-600">规格：<span className="font-medium">{item.item_spec}</span></span>
                                </>
                              )}
                              <span className="text-gray-400">|</span>
                              <span className="text-gray-600">需求数量：<span className="font-semibold text-blue-600">{item.quantity} {item.unit || '个'}</span></span>
                            </div>
                          </div>

                          {/* 报价输入区 - 紧凑布局 */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                单价（元/{item.unit || '个'}）*
                              </label>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={priceData.unit_price || ''}
                                onChange={(e) => updateItemPrice(item.id, e.target.value)}
                                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-blue-400 text-base"
                                placeholder="请输入单价"
                                required
                                disabled={loading}
                              />
                            </div>

                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                小计金额
                              </label>
                              <div className="w-full px-3 py-2 bg-green-50 border-2 border-green-300 rounded-lg font-bold text-green-700 text-base flex items-center">
                                ¥{(priceData.subtotal || 0).toFixed(2)}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
              })}
            </div>
          </div>

          {/* 总价显示 */}
          <div className="p-5 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold text-gray-900">报价总额：</span>
              <span className="text-3xl font-bold text-green-600">¥{totalPrice.toFixed(2)}</span>
            </div>
          </div>

          {/* 交期和付款周期 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                交期（天）*
              </label>
              <input
                type="number"
                min="1"
                value={quoteForm.lead_time}
                onChange={(e) => setQuoteForm({ ...quoteForm, lead_time: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400"
                required
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                付款周期（天）*
              </label>
              <input
                type="number"
                min="1"
                value={quoteForm.payment_terms}
                onChange={(e) => setQuoteForm({ ...quoteForm, payment_terms: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400"
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* 备注 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              备注说明
            </label>
            <textarea
              value={quoteForm.notes}
              onChange={(e) => setQuoteForm({ ...quoteForm, notes: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-400"
              rows={3}
              disabled={loading}
            />
          </div>

          {/* 申请人信息 */}
          {rfq?.pr_detail && (
            <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <h4 className="text-sm font-bold text-blue-900">申请信息</h4>
              </div>
              <div className="flex items-center gap-6 text-sm text-blue-800">
                <span className="flex items-center gap-1">
                  <span className="text-blue-600">申请人：</span>
                  <span className="font-semibold">{rfq.pr_detail.owner_name || '未知'}</span>
                </span>
                <span className="text-blue-400">|</span>
                <span className="flex items-center gap-1">
                  <span className="text-blue-600">申请部门：</span>
                  <span className="font-semibold">{rfq.pr_detail.owner_department || '未知'}</span>
                </span>
              </div>
            </div>
          )}

          {/* 提交按钮 */}
          <div className="flex gap-3 pt-2 border-t">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-blue-400 font-semibold text-lg"
            >
              {loading ? '提交中...' : `提交手动报价并生成订单（¥${totalPrice.toFixed(2)}）`}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
