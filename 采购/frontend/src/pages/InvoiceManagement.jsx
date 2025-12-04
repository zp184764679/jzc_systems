// pages/InvoiceManagement.jsx
// 发票管理页面 - 与采购订单集成

import { useState, useEffect, useMemo } from "react";
import { api } from "../api/http";
import { useAuth } from "../auth/AuthContext";

export default function InvoiceManagement() {
  const { user } = useAuth();

  // 视图模式
  const [viewMode, setViewMode] = useState("pos"); // pos | invoices

  // 数据
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);

  // 筛选条件 - PO列表
  const [poFilters, setPoFilters] = useState({
    search: "",
    supplier_id: "",
    status: "", // all | pending_invoice | has_invoice
    date_from: "",
    date_to: "",
  });

  // 筛选条件 - 发票列表
  const [invFilters, setInvFilters] = useState({
    search: "",
    supplier_id: "",
    status: "", // pending | approved | rejected
    settlement_type: "", // per_order | monthly
    date_from: "",
    date_to: "",
  });

  // 显示筛选面板
  const [showFilters, setShowFilters] = useState(false);

  // UI状态
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // 上传弹窗
  const [uploadModal, setUploadModal] = useState({ open: false, po: null, pos: [] });
  const [uploadForm, setUploadForm] = useState({
    settlement_type: "per_order",
    invoice_number: "",
    invoice_code: "",
    invoice_date: new Date().toISOString().slice(0, 10),
    buyer_name: "",
    buyer_tax_id: "",
    seller_name: "",
    seller_tax_id: "",
    amount_before_tax: "",
    tax_amount: "",
    total_amount: "",
    tax_rate: "",
    drawer: "",
    remark: "",
    file: null,
  });

  // 详情弹窗
  const [detailModal, setDetailModal] = useState({ open: false, invoice: null });

  // OCR识别状态
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState("");

  // 勾选的PO（用于批量上传）
  const [selectedPOs, setSelectedPOs] = useState([]); // [{id, supplier_id, po_number, total_price, supplier_name}]

  // 初始加载
  useEffect(() => {
    loadSuppliers();
  }, []);

  useEffect(() => {
    if (viewMode === "pos") {
      loadPurchaseOrders();
    } else {
      loadInvoices();
    }
  }, [viewMode]);

  // 加载供应商列表（用于筛选）
  const loadSuppliers = async () => {
    try {
      const res = await api.get("/api/v1/suppliers/admin/list?status=approved&per_page=200");
      setSuppliers(res.suppliers || res.items || []);
    } catch (err) {
      console.error("加载供应商失败:", err);
    }
  };

  // 加载采购订单列表
  const loadPurchaseOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (poFilters.supplier_id) params.append("supplier_id", poFilters.supplier_id);
      if (poFilters.search) params.append("search", poFilters.search);
      // 只加载可以上传发票的PO（confirmed/received/completed）
      params.append("status_in", "confirmed,received,completed");
      params.append("per_page", "100");

      const res = await api.get(`/api/v1/purchase-orders?${params.toString()}`);
      setPurchaseOrders(res.items || []);
    } catch (err) {
      setError("加载采购订单失败");
    } finally {
      setLoading(false);
    }
  };

  // 加载发票列表
  const loadInvoices = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (invFilters.supplier_id) params.append("supplier_id", invFilters.supplier_id);
      if (invFilters.status) params.append("status", invFilters.status);
      if (invFilters.settlement_type) params.append("settlement_type", invFilters.settlement_type);

      const res = await api.get(`/api/v1/invoices?${params.toString()}`);
      setInvoices(res.invoices || []);
    } catch (err) {
      setError("加载发票列表失败");
    } finally {
      setLoading(false);
    }
  };

  // 筛选后的PO列表
  const filteredPOs = useMemo(() => {
    let result = purchaseOrders;

    // 搜索
    if (poFilters.search) {
      const s = poFilters.search.toLowerCase();
      result = result.filter(po =>
        po.po_number?.toLowerCase().includes(s) ||
        po.supplier_name?.toLowerCase().includes(s)
      );
    }

    // 发票状态筛选
    if (poFilters.status === "pending_invoice") {
      result = result.filter(po => !po.invoice_uploaded);
    } else if (poFilters.status === "has_invoice") {
      result = result.filter(po => po.invoice_uploaded);
    }

    // 日期筛选
    if (poFilters.date_from) {
      result = result.filter(po => po.created_at >= poFilters.date_from);
    }
    if (poFilters.date_to) {
      result = result.filter(po => po.created_at <= poFilters.date_to + "T23:59:59");
    }

    return result;
  }, [purchaseOrders, poFilters]);

  // 筛选后的发票列表
  const filteredInvoices = useMemo(() => {
    let result = invoices;

    // 搜索
    if (invFilters.search) {
      const s = invFilters.search.toLowerCase();
      result = result.filter(inv =>
        inv.invoice_number?.toLowerCase().includes(s) ||
        inv.supplier_name?.toLowerCase().includes(s) ||
        inv.po_number?.toLowerCase().includes(s)
      );
    }

    // 日期筛选
    if (invFilters.date_from) {
      result = result.filter(inv => inv.invoice_date >= invFilters.date_from);
    }
    if (invFilters.date_to) {
      result = result.filter(inv => inv.invoice_date <= invFilters.date_to);
    }

    return result;
  }, [invoices, invFilters]);

  // 统计
  const stats = useMemo(() => {
    const pendingInvoice = purchaseOrders.filter(po => !po.invoice_uploaded).length;
    const hasInvoice = purchaseOrders.filter(po => po.invoice_uploaded).length;
    const perOrder = invoices.filter(inv => inv.settlement_type === "per_order").length;
    const monthly = invoices.filter(inv => inv.settlement_type === "monthly").length;

    return { pendingInvoice, hasInvoice, perOrder, monthly, totalPO: purchaseOrders.length, totalInvoice: invoices.length };
  }, [purchaseOrders, invoices]);

  // 打开上传弹窗
  const openUploadModal = (po) => {
    setUploadModal({ open: true, po, pos: [po] });
    setOcrError("");
    setUploadForm({
      settlement_type: "per_order",
      invoice_number: "",
      invoice_code: "",
      invoice_date: new Date().toISOString().slice(0, 10),
      buyer_name: "",
      buyer_tax_id: "",
      seller_name: po?.supplier_name || "",
      seller_tax_id: "",
      amount_before_tax: "",
      tax_amount: "",
      total_amount: po?.total_price?.toString() || "",
      tax_rate: "",
      drawer: "",
      remark: "",
      file: null,
    });
  };

  // 勾选/取消勾选PO
  const toggleSelectPO = (po) => {
    setSelectedPOs(prev => {
      const exists = prev.find(p => p.id === po.id);
      if (exists) {
        return prev.filter(p => p.id !== po.id);
      } else {
        return [...prev, po];
      }
    });
  };

  // 全选/取消全选某个供应商的所有PO
  const toggleSelectAllSupplier = (supplierPOs) => {
    if (supplierPOs.length === 0) return;

    const supplierId = supplierPOs[0].supplier_id;
    const supplierPoIds = supplierPOs.map(p => p.id);
    const allSelected = supplierPOs.every(po => selectedPOs.find(p => p.id === po.id));

    // 如果已选中其他供应商的PO，先清空再选择当前供应商
    const hasOtherSupplier = selectedPOs.length > 0 && selectedPOs[0].supplier_id !== supplierId;

    if (allSelected) {
      // 取消全选
      setSelectedPOs(prev => prev.filter(p => !supplierPoIds.includes(p.id)));
    } else {
      // 全选（如果有其他供应商的选择，先清空）
      if (hasOtherSupplier) {
        setSelectedPOs([...supplierPOs]);
      } else {
        setSelectedPOs(prev => {
          const newSelected = [...prev];
          supplierPOs.forEach(po => {
            if (!newSelected.find(p => p.id === po.id)) {
              newSelected.push(po);
            }
          });
          return newSelected;
        });
      }
    }
  };

  // 获取已选中的PO（按供应商分组）
  const selectedBySupplier = useMemo(() => {
    if (selectedPOs.length === 0) return null;
    const supplierId = selectedPOs[0].supplier_id;
    // 检查是否所有选中的PO都是同一个供应商
    const allSameSupplier = selectedPOs.every(po => po.supplier_id === supplierId);
    if (!allSameSupplier) return null;
    return {
      supplier_id: supplierId,
      supplier_name: selectedPOs[0].supplier_name,
      pos: selectedPOs,
      total: selectedPOs.reduce((sum, po) => sum + (parseFloat(po.total_price) || 0), 0),
    };
  }, [selectedPOs]);

  // 批量上传（月结）- 使用已选中的PO
  const openBatchUploadModal = () => {
    if (!selectedBySupplier || selectedBySupplier.pos.length < 1) {
      setError("请先勾选要合并的采购订单");
      return;
    }
    const totalAmount = selectedBySupplier.total;
    setUploadModal({ open: true, po: null, pos: selectedBySupplier.pos });
    setOcrError("");
    setUploadForm({
      settlement_type: selectedBySupplier.pos.length > 1 ? "monthly" : "per_order",
      invoice_number: "",
      invoice_code: "",
      invoice_date: new Date().toISOString().slice(0, 10),
      buyer_name: "",
      buyer_tax_id: "",
      seller_name: selectedBySupplier.supplier_name || "",
      seller_tax_id: "",
      amount_before_tax: "",
      tax_amount: "",
      total_amount: totalAmount.toFixed(2),
      tax_rate: "",
      drawer: "",
      remark: "",
      file: null,
    });
  };

  // 文件选择
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
      if (!allowedTypes.includes(file.type)) {
        setError("只支持 PDF、JPG、PNG 格式");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError("文件大小不能超过 10MB");
        return;
      }
      setUploadForm({ ...uploadForm, file });
    }
  };

  // OCR识别发票
  const handleOcrRecognize = async () => {
    if (!uploadForm.file) {
      setOcrError("请先选择发票图片");
      return;
    }

    // 检查文件类型（只支持图片）
    if (uploadForm.file.type === "application/pdf") {
      setOcrError("OCR暂不支持PDF，请上传JPG或PNG图片");
      return;
    }

    setOcrLoading(true);
    setOcrError("");

    try {
      const formData = new FormData();
      formData.append("file", uploadForm.file);

      const res = await api.post("/api/v1/invoices/ocr", formData);

      if (res.success && res.data) {
        const data = res.data;
        // 自动填充表单
        setUploadForm(prev => ({
          ...prev,
          invoice_number: data.invoice_number || prev.invoice_number,
          invoice_code: data.invoice_code || prev.invoice_code,
          invoice_date: data.invoice_date || prev.invoice_date,
          buyer_name: data.buyer_name || prev.buyer_name,
          buyer_tax_id: data.buyer_tax_id || prev.buyer_tax_id,
          seller_name: data.seller_name || prev.seller_name,
          seller_tax_id: data.seller_tax_id || prev.seller_tax_id,
          amount_before_tax: data.amount_before_tax?.toString() || prev.amount_before_tax,
          tax_amount: data.tax_amount?.toString() || prev.tax_amount,
          total_amount: data.total_amount?.toString() || prev.total_amount,
          tax_rate: data.tax_rate || prev.tax_rate,
          drawer: data.drawer || prev.drawer,
          remark: data.remark || prev.remark,
        }));
        setSuccess("发票识别成功，信息已自动填充");
      } else {
        setOcrError(res.error || "识别失败，请手动输入");
      }
    } catch (err) {
      setOcrError(err.message || "识别失败，请手动输入");
    } finally {
      setOcrLoading(false);
    }
  };

  // 提交上传
  const handleUpload = async () => {
    setError("");

    if (!uploadForm.invoice_number) {
      setError("请输入发票号码");
      return;
    }
    if (!uploadForm.total_amount) {
      setError("请输入发票金额");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("invoice_number", uploadForm.invoice_number);
      formData.append("invoice_code", uploadForm.invoice_code || "");
      formData.append("invoice_date", uploadForm.invoice_date);
      formData.append("buyer_name", uploadForm.buyer_name || "");
      formData.append("buyer_tax_id", uploadForm.buyer_tax_id || "");
      formData.append("seller_name", uploadForm.seller_name || "");
      formData.append("seller_tax_id", uploadForm.seller_tax_id || "");
      formData.append("amount_before_tax", uploadForm.amount_before_tax || "0");
      formData.append("tax_amount", uploadForm.tax_amount || "0");
      formData.append("total_amount", uploadForm.total_amount);
      formData.append("tax_rate", uploadForm.tax_rate || "");
      formData.append("drawer", uploadForm.drawer || "");
      formData.append("remark", uploadForm.remark || "");

      if (uploadForm.file) {
        formData.append("file", uploadForm.file);
      }

      if (uploadForm.settlement_type === "per_order" && uploadModal.po) {
        formData.append("po_id", uploadModal.po.id);
        await api.post("/api/v1/invoices/upload", formData);
      } else {
        formData.append("supplier_id", uploadModal.pos[0]?.supplier_id);
        formData.append("po_ids", JSON.stringify(uploadModal.pos.map(p => p.id)));
        formData.append("period", new Date().toISOString().slice(0, 7));
        await api.post("/api/v1/invoices/upload/monthly", formData);
      }

      setSuccess("发票上传成功");
      setUploadModal({ open: false, po: null, pos: [] });
      setSelectedPOs([]); // 清空选中
      loadPurchaseOrders();
    } catch (err) {
      setError(err.message || "上传失败");
    } finally {
      setLoading(false);
    }
  };

  // 查看发票详情
  const viewInvoiceDetail = (invoice) => {
    setDetailModal({ open: true, invoice });
  };

  // 删除发票
  const handleDeleteInvoice = async (invoice) => {
    if (!confirm("确定要删除这张发票吗？删除后对应的PO将恢复为待上传状态。")) return;

    setLoading(true);
    try {
      await api.delete(`/api/v1/invoices/${invoice.id}`);
      setSuccess("发票已删除");
      loadInvoices();
      loadPurchaseOrders();
    } catch (err) {
      setError(err.message || "删除失败");
    } finally {
      setLoading(false);
    }
  };

  // 状态标签
  const StatusBadge = ({ status, type = "invoice" }) => {
    const configs = {
      invoice: {
        pending: { bg: "bg-green-100", text: "text-green-800", label: "已记录" },
        approved: { bg: "bg-green-100", text: "text-green-800", label: "已记录" },
        rejected: { bg: "bg-red-100", text: "text-red-800", label: "已作废" },
      },
      po: {
        confirmed: { bg: "bg-blue-100", text: "text-blue-800", label: "已确认" },
        received: { bg: "bg-purple-100", text: "text-purple-800", label: "已收货" },
        completed: { bg: "bg-green-100", text: "text-green-800", label: "已完成" },
      },
    };
    const config = configs[type]?.[status] || { bg: "bg-gray-100", text: "text-gray-800", label: status };
    return (
      <span className={`px-2 py-1 rounded text-xs ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  // 按供应商分组PO
  const groupedPOs = useMemo(() => {
    const groups = {};
    filteredPOs.filter(po => !po.invoice_uploaded).forEach(po => {
      const sid = po.supplier_id;
      if (!groups[sid]) {
        groups[sid] = {
          supplier_id: sid,
          supplier_name: po.supplier_name,
          pos: [],
          total: 0,
        };
      }
      groups[sid].pos.push(po);
      groups[sid].total += parseFloat(po.total_price) || 0;
    });
    return Object.values(groups);
  }, [filteredPOs]);

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* 标题和统计 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">发票管理</h1>

        {/* 统计卡片 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-orange-600">{stats.pendingInvoice}</div>
            <div className="text-sm text-gray-500">待上传发票的PO</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-green-600">{stats.hasInvoice}</div>
            <div className="text-sm text-gray-500">已上传发票的PO</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-blue-600">{stats.perOrder}</div>
            <div className="text-sm text-gray-500">单次结算发票</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-purple-600">{stats.monthly}</div>
            <div className="text-sm text-gray-500">月结发票</div>
          </div>
        </div>
      </div>

      {/* 提示信息 */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError("")}>&times;</button>
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded flex justify-between">
          <span>{success}</span>
          <button onClick={() => setSuccess("")}>&times;</button>
        </div>
      )}

      {/* Tab 切换 */}
      <div className="flex border-b mb-4">
        <button
          onClick={() => setViewMode("pos")}
          className={`px-4 py-2 -mb-px font-medium ${viewMode === "pos" ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-500 hover:text-gray-700"}`}
        >
          采购订单 ({stats.totalPO})
        </button>
        <button
          onClick={() => setViewMode("invoices")}
          className={`px-4 py-2 -mb-px font-medium ${viewMode === "invoices" ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-500 hover:text-gray-700"}`}
        >
          发票列表 ({invoices.length})
        </button>
      </div>

      {/* 筛选栏 */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex flex-wrap gap-3 items-center">
          {/* 搜索框 */}
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder={viewMode === "pos" ? "搜索PO编号、供应商..." : "搜索发票号、PO号、供应商..."}
              className="w-full border rounded px-3 py-2"
              value={viewMode === "pos" ? poFilters.search : invFilters.search}
              onChange={(e) => {
                if (viewMode === "pos") {
                  setPoFilters({ ...poFilters, search: e.target.value });
                } else {
                  setInvFilters({ ...invFilters, search: e.target.value });
                }
              }}
            />
          </div>

          {/* 供应商筛选 */}
          <select
            className="border rounded px-3 py-2"
            value={viewMode === "pos" ? poFilters.supplier_id : invFilters.supplier_id}
            onChange={(e) => {
              if (viewMode === "pos") {
                setPoFilters({ ...poFilters, supplier_id: e.target.value });
              } else {
                setInvFilters({ ...invFilters, supplier_id: e.target.value });
              }
            }}
          >
            <option value="">全部供应商</option>
            {suppliers.map(s => (
              <option key={s.id} value={s.id}>{s.company_name || s.name}</option>
            ))}
          </select>

          {/* PO视图 - 发票状态筛选 */}
          {viewMode === "pos" && (
            <select
              className="border rounded px-3 py-2"
              value={poFilters.status}
              onChange={(e) => setPoFilters({ ...poFilters, status: e.target.value })}
            >
              <option value="">全部状态</option>
              <option value="pending_invoice">待上传发票</option>
              <option value="has_invoice">已上传发票</option>
            </select>
          )}

          {/* 发票视图 - 结算类型筛选 */}
          {viewMode === "invoices" && (
            <select
              className="border rounded px-3 py-2"
              value={invFilters.settlement_type}
              onChange={(e) => setInvFilters({ ...invFilters, settlement_type: e.target.value })}
            >
              <option value="">全部类型</option>
              <option value="per_order">单次结算</option>
              <option value="monthly">月结</option>
            </select>
          )}

          {/* 更多筛选 */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-3 py-2 border rounded text-gray-600 hover:bg-gray-50"
          >
            {showFilters ? "收起" : "更多筛选"}
          </button>

          {/* 刷新 */}
          <button
            onClick={() => viewMode === "pos" ? loadPurchaseOrders() : loadInvoices()}
            className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            刷新
          </button>
        </div>

        {/* 展开的筛选条件 */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t flex flex-wrap gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">开始日期</label>
              <input
                type="date"
                className="border rounded px-3 py-2"
                value={viewMode === "pos" ? poFilters.date_from : invFilters.date_from}
                onChange={(e) => {
                  if (viewMode === "pos") {
                    setPoFilters({ ...poFilters, date_from: e.target.value });
                  } else {
                    setInvFilters({ ...invFilters, date_from: e.target.value });
                  }
                }}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">结束日期</label>
              <input
                type="date"
                className="border rounded px-3 py-2"
                value={viewMode === "pos" ? poFilters.date_to : invFilters.date_to}
                onChange={(e) => {
                  if (viewMode === "pos") {
                    setPoFilters({ ...poFilters, date_to: e.target.value });
                  } else {
                    setInvFilters({ ...invFilters, date_to: e.target.value });
                  }
                }}
              />
            </div>
            <button
              onClick={() => {
                if (viewMode === "pos") {
                  setPoFilters({ search: "", supplier_id: "", status: "", date_from: "", date_to: "" });
                } else {
                  setInvFilters({ search: "", supplier_id: "", status: "", settlement_type: "", date_from: "", date_to: "" });
                }
              }}
              className="self-end px-3 py-2 text-gray-500 hover:text-gray-700"
            >
              清除筛选
            </button>
          </div>
        )}
      </div>

      {loading && <div className="text-center py-8 text-gray-500">加载中...</div>}

      {/* 采购订单视图 */}
      {viewMode === "pos" && !loading && (
        <div className="space-y-6">
          {/* 按供应商分组显示待上传的PO - 支持勾选合并上传 */}
          {groupedPOs.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold text-orange-800">待上传发票的采购订单（按供应商分组）</h3>
                {selectedPOs.length > 0 && (
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-600">
                      已选 {selectedPOs.length} 个PO，合计 ¥{selectedPOs.reduce((sum, po) => sum + (parseFloat(po.total_price) || 0), 0).toFixed(2)}
                    </span>
                    <button
                      onClick={() => setSelectedPOs([])}
                      className="text-gray-500 hover:text-gray-700 text-sm"
                    >
                      清空
                    </button>
                    <button
                      onClick={openBatchUploadModal}
                      className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
                    >
                      合并上传
                    </button>
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-500 mb-3">勾选同一供应商的多个PO，可合并为一张月结发票</p>
              {groupedPOs.map(group => {
                const groupSelected = group.pos.filter(po => selectedPOs.find(p => p.id === po.id));
                const allSelected = group.pos.length > 0 && group.pos.every(po => selectedPOs.find(p => p.id === po.id));
                const someSelected = groupSelected.length > 0 && !allSelected;

                return (
                  <div key={group.supplier_id} className="bg-white rounded-lg p-4 mb-3 last:mb-0">
                    <div className="flex justify-between items-center mb-2 pb-2 border-b">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={allSelected}
                          ref={el => { if (el) el.indeterminate = someSelected; }}
                          onChange={() => toggleSelectAllSupplier(group.pos)}
                          className="w-4 h-4 text-orange-500 rounded"
                        />
                        <span className="font-medium">{group.supplier_name}</span>
                        <span className="text-sm text-gray-500">
                          {group.pos.length} 个PO | 总金额: ¥{group.total.toFixed(2)}
                        </span>
                      </label>
                    </div>
                    <div className="text-sm text-gray-600">
                      {group.pos.map(po => {
                        const isSelected = selectedPOs.find(p => p.id === po.id);
                        // 如果已选中其他供应商的PO，则禁用当前供应商的选择
                        const otherSupplierSelected = selectedPOs.length > 0 && selectedPOs[0].supplier_id !== po.supplier_id;

                        return (
                          <div key={po.id} className={`flex justify-between items-center py-2 border-b last:border-0 ${isSelected ? 'bg-orange-50' : ''}`}>
                            <label className={`flex items-center gap-2 ${otherSupplierSelected ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                              <input
                                type="checkbox"
                                checked={!!isSelected}
                                disabled={otherSupplierSelected}
                                onChange={() => toggleSelectPO(po)}
                                className="w-4 h-4 text-orange-500 rounded"
                              />
                              <span>{po.po_number}</span>
                            </label>
                            <div className="flex items-center gap-3">
                              <span>¥{parseFloat(po.total_price || 0).toFixed(2)}</span>
                              <button
                                onClick={() => openUploadModal(po)}
                                className="text-blue-500 hover:text-blue-700"
                              >
                                单独上传
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* 完整PO列表 */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3 text-sm font-medium text-gray-600">PO编号</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-600">供应商</th>
                  <th className="text-right p-3 text-sm font-medium text-gray-600">金额</th>
                  <th className="text-center p-3 text-sm font-medium text-gray-600">PO状态</th>
                  <th className="text-center p-3 text-sm font-medium text-gray-600">发票状态</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-600">创建时间</th>
                  <th className="text-center p-3 text-sm font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredPOs.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="text-center py-8 text-gray-500">
                      暂无采购订单
                    </td>
                  </tr>
                ) : (
                  filteredPOs.map(po => (
                    <tr key={po.id} className="border-t hover:bg-gray-50">
                      <td className="p-3 font-mono text-sm">{po.po_number}</td>
                      <td className="p-3">{po.supplier_name}</td>
                      <td className="p-3 text-right">¥{parseFloat(po.total_price || 0).toFixed(2)}</td>
                      <td className="p-3 text-center">
                        <StatusBadge status={po.status} type="po" />
                      </td>
                      <td className="p-3 text-center">
                        {po.invoice_uploaded ? (
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">已上传</span>
                        ) : (
                          <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">待上传</span>
                        )}
                      </td>
                      <td className="p-3 text-sm text-gray-500">{po.created_at?.slice(0, 10)}</td>
                      <td className="p-3 text-center">
                        {!po.invoice_uploaded && (
                          <button
                            onClick={() => openUploadModal(po)}
                            className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                          >
                            上传发票
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 发票列表视图 */}
      {viewMode === "invoices" && !loading && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600">发票号</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">供应商</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">关联PO</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600">金额</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">类型</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">状态</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600">发票日期</th>
                <th className="text-center p-3 text-sm font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-gray-500">
                    暂无发票记录
                  </td>
                </tr>
              ) : (
                filteredInvoices.map(inv => (
                  <tr key={inv.id} className="border-t hover:bg-gray-50">
                    <td className="p-3 font-mono text-sm">{inv.invoice_number}</td>
                    <td className="p-3">{inv.supplier_name}</td>
                    <td className="p-3 text-sm">
                      {inv.settlement_type === "monthly" ? (
                        <span className="text-gray-500">{inv.po_count || 0} 个PO</span>
                      ) : (
                        inv.po_number || "-"
                      )}
                    </td>
                    <td className="p-3 text-right">¥{parseFloat(inv.total_amount || 0).toFixed(2)}</td>
                    <td className="p-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs ${inv.settlement_type === "monthly" ? "bg-purple-100 text-purple-800" : "bg-gray-100 text-gray-800"}`}>
                        {inv.settlement_type === "monthly" ? "月结" : "单次"}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <StatusBadge status={inv.status} type="invoice" />
                    </td>
                    <td className="p-3 text-sm text-gray-500">{inv.invoice_date?.slice(0, 10)}</td>
                    <td className="p-3 text-center space-x-2">
                      <button
                        onClick={() => viewInvoiceDetail(inv)}
                        className="text-blue-500 hover:text-blue-700 text-sm"
                      >
                        详情
                      </button>
                      <button
                        onClick={() => handleDeleteInvoice(inv)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* 上传发票弹窗 */}
      {uploadModal.open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-bold">上传发票</h3>
              <button onClick={() => setUploadModal({ open: false, po: null, pos: [] })} className="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
            </div>
            <div className="p-4 space-y-4">
              {/* 关联信息 */}
              <div className="bg-gray-50 rounded p-3">
                {uploadForm.settlement_type === "per_order" ? (
                  <div>
                    <div className="text-sm text-gray-500">关联采购订单</div>
                    <div className="font-medium">{uploadModal.po?.po_number}</div>
                    <div className="text-sm text-gray-500">{uploadModal.po?.supplier_name}</div>
                  </div>
                ) : (
                  <div>
                    <div className="text-sm text-gray-500">月结发票 - {uploadModal.pos.length} 个PO</div>
                    <div className="font-medium">{uploadModal.pos[0]?.supplier_name}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {uploadModal.pos.map(p => p.po_number).join(", ")}
                    </div>
                  </div>
                )}
              </div>

              {/* 发票文件上传 - 放在最前面 */}
              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <label className="block text-sm font-medium mb-2 text-blue-800">第一步：上传发票图片</label>
                <div className="flex gap-2">
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="flex-1 border rounded px-3 py-2 bg-white"
                    onChange={handleFileChange}
                  />
                  <button
                    type="button"
                    onClick={handleOcrRecognize}
                    disabled={!uploadForm.file || ocrLoading}
                    className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {ocrLoading ? "识别中..." : "AI识别"}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">支持 JPG、PNG 图片，上传后点击"AI识别"自动填充发票信息</p>
                {ocrError && <p className="text-xs text-red-500 mt-1">{ocrError}</p>}
              </div>

              {/* 发票基本信息 */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">发票基本信息</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">发票号码 *</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={uploadForm.invoice_number}
                      onChange={(e) => setUploadForm({ ...uploadForm, invoice_number: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">发票代码</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={uploadForm.invoice_code}
                      onChange={(e) => setUploadForm({ ...uploadForm, invoice_code: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">开票日期</label>
                    <input
                      type="date"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={uploadForm.invoice_date}
                      onChange={(e) => setUploadForm({ ...uploadForm, invoice_date: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* 购买方信息 */}
              <div className="bg-green-50 rounded p-3">
                <h4 className="text-sm font-medium text-green-800 mb-2">购买方信息</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">名称</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm bg-white"
                      value={uploadForm.buyer_name}
                      onChange={(e) => setUploadForm({ ...uploadForm, buyer_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">税号</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm bg-white font-mono"
                      value={uploadForm.buyer_tax_id}
                      onChange={(e) => setUploadForm({ ...uploadForm, buyer_tax_id: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* 销售方信息 */}
              <div className="bg-orange-50 rounded p-3">
                <h4 className="text-sm font-medium text-orange-800 mb-2">销售方信息</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">名称</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm bg-white"
                      value={uploadForm.seller_name}
                      onChange={(e) => setUploadForm({ ...uploadForm, seller_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">税号</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm bg-white font-mono"
                      value={uploadForm.seller_tax_id}
                      onChange={(e) => setUploadForm({ ...uploadForm, seller_tax_id: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* 金额信息 */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">金额信息</h4>
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">不含税金额</label>
                    <input
                      type="number"
                      step="0.01"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={uploadForm.amount_before_tax}
                      onChange={(e) => setUploadForm({ ...uploadForm, amount_before_tax: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">税率(%)</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={uploadForm.tax_rate}
                      onChange={(e) => setUploadForm({ ...uploadForm, tax_rate: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">税额</label>
                    <input
                      type="number"
                      step="0.01"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={uploadForm.tax_amount}
                      onChange={(e) => setUploadForm({ ...uploadForm, tax_amount: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">价税合计 *</label>
                    <input
                      type="number"
                      step="0.01"
                      className="w-full border rounded px-3 py-2 text-sm font-medium"
                      value={uploadForm.total_amount}
                      onChange={(e) => setUploadForm({ ...uploadForm, total_amount: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* 其他信息 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">开票人</label>
                  <input
                    type="text"
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={uploadForm.drawer}
                    onChange={(e) => setUploadForm({ ...uploadForm, drawer: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">备注</label>
                  <input
                    type="text"
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={uploadForm.remark}
                    onChange={(e) => setUploadForm({ ...uploadForm, remark: e.target.value })}
                  />
                </div>
              </div>
            </div>
            <div className="p-4 border-t flex justify-end gap-3">
              <button
                onClick={() => setUploadModal({ open: false, po: null, pos: [] })}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleUpload}
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? "上传中..." : "确认上传"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 发票详情弹窗 */}
      {detailModal.open && detailModal.invoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-bold">发票详情</h3>
              <button onClick={() => setDetailModal({ open: false, invoice: null })} className="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500">发票号码</span>
                <span className="font-medium">{detailModal.invoice.invoice_number}</span>
              </div>
              {detailModal.invoice.invoice_code && (
                <div className="flex justify-between">
                  <span className="text-gray-500">发票代码</span>
                  <span>{detailModal.invoice.invoice_code}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-500">供应商</span>
                <span>{detailModal.invoice.supplier_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">结算类型</span>
                <span>{detailModal.invoice.settlement_type === "monthly" ? "月结" : "单次结算"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">关联PO</span>
                <span>{detailModal.invoice.po_number || `${detailModal.invoice.po_count || 0} 个PO`}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">发票日期</span>
                <span>{detailModal.invoice.invoice_date?.slice(0, 10)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">不含税金额</span>
                <span>¥{parseFloat(detailModal.invoice.amount_before_tax || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">税额</span>
                <span>¥{parseFloat(detailModal.invoice.tax_amount || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">含税金额</span>
                <span className="font-bold text-lg">¥{parseFloat(detailModal.invoice.total_amount || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">记录状态</span>
                <span className="text-green-600 font-medium">已记录</span>
              </div>
              {detailModal.invoice.remark && (
                <div>
                  <span className="text-gray-500 block mb-1">备注</span>
                  <span className="text-sm">{detailModal.invoice.remark}</span>
                </div>
              )}
              {detailModal.invoice.file_path && (
                <div className="pt-2">
                  <a
                    href={detailModal.invoice.file_url || detailModal.invoice.file_path}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:text-blue-700"
                  >
                    查看发票文件
                  </a>
                </div>
              )}
            </div>
            <div className="p-4 border-t flex justify-end">
              <button
                onClick={() => setDetailModal({ open: false, invoice: null })}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
