// Strapi Admin 自定义配置
export default {
  config: {
    // 翻译 (不设置 locales，避免与 CKEditor 冲突)
    translations: {
      zh: {
        'app.components.LeftMenu.navbrand.title': '文件发布器',
        'content-manager.containers.edit.information': '文档信息',
      },
      en: {
        'app.components.LeftMenu.navbrand.title': 'DocPublisher',
      },
      ja: {
        'app.components.LeftMenu.navbrand.title': 'ドキュメント発行',
      },
    },
  },
  bootstrap() {
    // 注入预览按钮脚本
    injectPreviewButton();
  },
};

// 注入预览按钮到文档编辑页面
function injectPreviewButton() {
  // 等待 DOM 加载完成后注入
  const checkAndInject = () => {
    // 检查是否在文档编辑页面
    const url = window.location.href;
    if (url.includes('/content-manager/collection-types/api::document.document/')) {
      // 获取文档 ID
      const match = url.match(/api::document\.document\/([^?/]+)/);
      if (match) {
        const documentId = match[1];
        addPreviewButton(documentId);
      }
    }
  };

  // 监听 URL 变化
  let lastUrl = location.href;
  new MutationObserver(() => {
    const currentUrl = location.href;
    if (currentUrl !== lastUrl) {
      lastUrl = currentUrl;
      setTimeout(checkAndInject, 500);
    }
  }).observe(document, { subtree: true, childList: true });

  // 初始检查
  setTimeout(checkAndInject, 1000);
}

// 添加预览按钮
function addPreviewButton(documentId) {
  // 避免重复添加
  if (document.getElementById('custom-preview-btn')) return;

  // 创建预览按钮
  const btn = document.createElement('button');
  btn.id = 'custom-preview-btn';
  btn.innerHTML = '👁 预览文档';
  btn.style.cssText = `
    position: fixed;
    top: 12px;
    right: 200px;
    background: #4945ff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    z-index: 1000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    display: flex;
    align-items: center;
    gap: 6px;
  `;
  btn.onmouseover = () => btn.style.background = '#3b38cc';
  btn.onmouseout = () => btn.style.background = '#4945ff';
  btn.onclick = () => openPreviewModal(documentId);

  // 直接添加到 body
  document.body.appendChild(btn);
}

// 打开预览模态框
function openPreviewModal(documentId) {
  // 移除已存在的模态框
  const existing = document.getElementById('preview-modal');
  if (existing) existing.remove();

  // 获取 slug (从页面中读取)
  const slugInput = document.querySelector('input[name="slug"]');
  const slug = slugInput ? slugInput.value : documentId;
  const previewUrl = `http://localhost:6200/docs/view/${slug}`;

  // 创建模态框容器
  const modal = document.createElement('div');
  modal.id = 'preview-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 10000;
    display: flex;
    justify-content: center;
    align-items: center;
  `;

  // 创建内容容器
  const content = document.createElement('div');
  content.style.cssText = `
    background: white;
    width: 90%;
    height: 90%;
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  `;

  // 创建头部
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 12px 16px;
    background: #f0f0f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #ddd;
  `;

  const title = document.createElement('span');
  title.style.fontWeight = 'bold';
  title.textContent = '📄 文档预览';

  const btnGroup = document.createElement('div');

  const openBtn = document.createElement('button');
  openBtn.textContent = '在新窗口打开';
  openBtn.style.cssText = `
    background: #4945ff;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 8px;
  `;
  openBtn.addEventListener('click', () => window.open(previewUrl, '_blank'));

  const closeBtn = document.createElement('button');
  closeBtn.textContent = '关闭';
  closeBtn.style.cssText = `
    background: #ddd;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
  `;
  closeBtn.addEventListener('click', () => modal.remove());

  btnGroup.appendChild(openBtn);
  btnGroup.appendChild(closeBtn);
  header.appendChild(title);
  header.appendChild(btnGroup);

  // 创建 iframe
  const iframe = document.createElement('iframe');
  iframe.src = previewUrl;
  iframe.style.cssText = 'flex: 1; border: none; width: 100%;';

  // 组装
  content.appendChild(header);
  content.appendChild(iframe);
  modal.appendChild(content);

  // 点击背景关闭
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
  content.addEventListener('click', (e) => e.stopPropagation());

  document.body.appendChild(modal);
}
