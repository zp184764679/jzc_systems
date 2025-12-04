import React from "react";

/**
 * StatisticsCard - 统计卡片组件
 * 展示审批统计数据
 */
export default function StatisticsCard({ stats, onStatusClick }) {
  const cards = [
    { 
      label: "共计", 
      value: stats.total, 
      icon: "📊", 
      color: "bg-blue-50 border-blue-200",
      statusCode: null
    },
    { 
      label: "待审批", 
      value: stats.pending, 
      icon: "⏳", 
      color: "bg-yellow-50 border-yellow-200",
      statusCode: "submitted"
    },
    { 
      label: "已批准", 
      value: stats.approved, 
      icon: "✅", 
      color: "bg-green-50 border-green-200",
      statusCode: "approved"
    },
    { 
      label: "已驳回", 
      value: stats.rejected, 
      icon: "❌", 
      color: "bg-red-50 border-red-200",
      statusCode: "rejected"
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className={`border rounded-lg p-4 cursor-pointer transition hover:shadow-md ${card.color}`}
          onClick={() => card.statusCode && onStatusClick(card.statusCode)}
          title={card.statusCode ? "点击筛选此状态" : ""}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">{card.label}</div>
              <div className="text-2xl font-bold mt-1">{card.value}</div>
            </div>
            <div className="text-3xl">{card.icon}</div>
          </div>
        </div>
      ))}
    </div>
  );
}