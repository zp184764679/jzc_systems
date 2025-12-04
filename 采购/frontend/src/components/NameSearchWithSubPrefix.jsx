import React, { useMemo, useRef, useState, useEffect } from "react";

/**
 * 目标：简化原有组件，只保留物料名称的搜索和选择功能
 * - 录入时自动给出候选项，格式如：铣刀 Φ10 硬质合金
 * - 选择某个候选项时：输入框填入物料名称
 * - 支持键盘上下选择、Enter确认；支持中文/英文模糊匹配（不依赖外部库）
 */

// ======== 示例数据：物料名称 ========
const MATERIAL_DATA = [
  "铣刀 Φ10 硬质合金",
  "钻头 Φ12 钨钢",
  "丝攻 M10 进口",
  "螺纹规/环规/针规 规格：M6",
  "刀粒 CVD 硬质",
  "刀柄 BT40 标准型",
  "送料头/导套/料尾夹 适用于CN机器",
  "夹爪/飞机片 高强度",
  "导轮 进口型号",
];

function normalize(str) {
  return (str || "")
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[\-_/]/g, "");
}

function fuzzyMatch(kw, text) {
  if (!kw) return true;
  const a = normalize(kw);
  const b = normalize(text);
  let i = 0;
  for (let c of a) {
    i = b.indexOf(c, i);
    if (i === -1) return false;
    i++;
  }
  return true;
}

export default function NameSearchWithSubPrefix({
  value,
  onChange,
  data = MATERIAL_DATA,
  placeholder = "输入物料名称，如：铣刀 Φ10 硬质合金",
}) {
  const [input, setInput] = useState(value || "");
  const [open, setOpen] = useState(false);
  const [cursor, setCursor] = useState(0);
  const listRef = useRef(null);

  const allOptions = useMemo(() => data, [data]);
  const filtered = useMemo(() => {
    const kw = input.trim();
    const arr = allOptions.filter((o) =>
      fuzzyMatch(kw, o) // 只根据物料名称匹配
    );
    return arr.slice(0, 20); // 最多展示20条
  }, [allOptions, input]);

  useEffect(() => {
    if (open && listRef.current) {
      listRef.current.scrollTo({ top: 0 });
    }
  }, [open]);

  function commit(option) {
    const text = option || input;
    setInput(text);
    setOpen(false);
    if (onChange) {
      onChange(text); // 只返回物料名称
    }
  }

  function onKeyDown(e) {
    if (!open && ["ArrowDown", "ArrowUp"].includes(e.key)) {
      setOpen(true);
      return;
    }
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      commit(filtered[cursor]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="relative w-full">
      <input
        className="w-full rounded-2xl border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        placeholder={placeholder}
        value={input}
        onChange={(e) => {
          setInput(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />

      {open && filtered.length > 0 && (
        <div
          ref={listRef}
          className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-2xl border border-gray-200 bg-white shadow-xl"
        >
          {filtered.map((opt, idx) => (
            <div
              key={opt + idx}
              onMouseDown={(e) => {
                e.preventDefault();
                commit(opt);
              }}
              className={
                "cursor-pointer px-4 py-2 hover:bg-indigo-50 " +
                (idx === cursor ? "bg-indigo-50" : "")
              }
            >
              <div className="text-sm font-medium">{opt}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
