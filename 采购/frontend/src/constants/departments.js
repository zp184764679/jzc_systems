// src/constants/departments.js
export const DEPARTMENTS = [
{ name: "生产部", children: ["走心机", "磨床", "加工中心"] },
{ name: "采购部" },
{ name: "仓库" },
{ name: "品质" },
{ name: "财务" },
{ name: "行政" },
{ name: "研发" },
{ name: "销售" },
];


// 一维枚举（给后端）
export const DEPARTMENT_ENUM = [
"生产部/走心机", "生产部/磨床", "生产部/加工中心",
"采购部", "仓库", "品质", "财务", "行政", "研发", "销售",
];