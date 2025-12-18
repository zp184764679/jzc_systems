import { Select } from 'antd';
import { useTranslation } from 'react-i18next';
import { GlobalOutlined } from '@ant-design/icons';

const langOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' }
];

export default function LanguageSwitcher({ style }) {
  const { i18n } = useTranslation();

  const handleChange = (lang) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('docs-lang', lang);
    // 触发语言切换事件，让其他组件重新加载数据
    window.dispatchEvent(new CustomEvent('langChange', { detail: lang }));
  };

  return (
    <Select
      value={i18n.language}
      onChange={handleChange}
      options={langOptions}
      style={{ width: 100, ...style }}
      suffixIcon={<GlobalOutlined />}
      variant="borderless"
    />
  );
}
