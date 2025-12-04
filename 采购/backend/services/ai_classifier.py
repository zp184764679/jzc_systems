# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
import math
import os
import json
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 导入知识库服务（延迟导入，避免循环依赖）
_knowledge_service = None

def get_knowledge_service():
    """延迟加载知识库服务"""
    global _knowledge_service
    if _knowledge_service is None:
        try:
            from services.material_knowledge import get_knowledge_service as _get_service
            _knowledge_service = _get_service()
        except Exception as e:
            logger.warning(f"无法加载知识库服务: {e}")
            _knowledge_service = False  # 标记为不可用
    return _knowledge_service if _knowledge_service is not False else None


class EmbeddingBackend:
    """可替换后端：默认用简单 bag-of-words 向量（无依赖）"""
    def embed(self, texts: List[str]) -> List[Dict[str, float]]:
        """使用Bag-of-Words方式生成向量"""
        vecs = []
        for t in texts:
            t = (t or "").lower()
            counts = {}
            for tok in t.replace("／"," ").replace("/"," ").replace("，"," ").replace(","," ").split():
                counts[tok] = counts.get(tok, 0) + 1.0
            # L2 归一化
            norm = math.sqrt(sum(v*v for v in counts.values())) or 1.0
            for k in counts: 
                counts[k] /= norm
            vecs.append(counts)
        return vecs


class OllamaBackend:
    """
    Ollama 后端：调用本地大模型进行分类
    依赖：Ollama 服务运行在 LLM_BASE（默认 http://localhost:11434）
    """
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("LLM_BASE", "http://localhost:11434")
        self.model = model or os.getenv("LLM_MODEL", "qwen2.5:7b")
        self.api_endpoint = f"{self.base_url}/api/generate"
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"✅ Ollama 后端初始化成功: {self.base_url} (模型: {self.model})")
        else:
            logger.warning(f"⚠️  Ollama 服务不可用 ({self.base_url})，将使用备用方案")

    def _check_availability(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 健康检查失败: {e}")
            return False

    def classify_with_llm(self, text: str, categories: List[str]) -> Dict[str, float]:
        """
        使用大模型分类物料
        
        Args:
            text: 物料文本 (名称 + 规格 + 备注)
            categories: 分类列表
        
        Returns:
            {"category_name": confidence_score, ...}
        """
        if not self.available:
            return {}
        
        try:
            prompt = self._build_prompt(text, categories)
            
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API 错误: {response.status_code}")
                return {}
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            scores = self._parse_llm_response(response_text, categories)
            return scores
        
        except requests.Timeout:
            logger.error(f"Ollama 请求超时 (30s)")
            return {}
        except Exception as e:
            logger.error(f"Ollama 分类错误: {e}")
            return {}

    def _build_prompt(self, text: str, categories: List[str]) -> str:
        """构建分类提示词"""
        cat_list = "\n".join([f"{i+1}. {cat}" for i, cat in enumerate(categories)])
        
        prompt = f"""请根据以下物料信息，判断它属于哪个分类。

物料信息：{text}

可选分类：
{cat_list}

请你返回一个 JSON 格式的结果，包含每个分类的置信度（0-1）。
例如：{{"机械零部件/传动": 0.9, "五金劳保": 0.1}}

只返回 JSON，不要其他说明。"""
        
        return prompt

    def _parse_llm_response(self, response_text: str, categories: List[str]) -> Dict[str, float]:
        """
        解析大模型返回的分类结果
        
        Args:
            response_text: 大模型返回的文本
            categories: 分类列表
        
        Returns:
            {"category": score, ...} 格式的字典
        """
        try:
            # 移除 markdown 代码块标记
            if "```" in response_text:
                json_str = response_text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                json_str = json_str.strip()
            else:
                json_str = response_text.strip()
            
            # 解析 JSON
            scores = json.loads(json_str)
            
            # 归一化并过滤非法的分类
            valid_scores = {}
            total = 0
            for cat, score in scores.items():
                if cat in categories:
                    try:
                        s = float(score)
                        valid_scores[cat] = max(0, min(1, s))  # 限制在 [0, 1]
                        total += valid_scores[cat]
                    except (ValueError, TypeError):
                        pass
            
            # 如果总分为 0，返回空
            if total == 0:
                return {}
            
            # 重新归一化，使总分为 1
            for cat in valid_scores:
                valid_scores[cat] = valid_scores[cat] / total
            
            return valid_scores
        
        except Exception as e:
            logger.warning(f"无法解析大模型响应: {e}")
            return {}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """计算余弦相似度"""
    if not a or not b: 
        return 0.0
    if len(a) > len(b): 
        a, b = b, a
    return sum(a[k]*b.get(k, 0.0) for k in a)


class LocalClassifier:
    """
    物料分类器：结合知识库、规则、向量和大模型
    优先级：缓存 > 规则 > 知识库 > 大模型 > 向量备用

    改进版：支持提取大类和子类，添加知识库索引层
    """
    def __init__(self, embedding: Optional[EmbeddingBackend] = None, use_ollama: bool = True, use_knowledge: bool = True):
        self.embedding = embedding or EmbeddingBackend()

        # 从constants加载品类配置
        self._load_categories()

        # 知识库服务
        self.knowledge_service = None
        if use_knowledge:
            self.knowledge_service = get_knowledge_service()
            if self.knowledge_service:
                logger.info("✅ 知识库服务已启用")
            else:
                logger.warning("⚠️  知识库服务不可用，跳过知识库查询层")

        # 规则层：包含所有支持的分类和关键词
        self.rules = {
            "刀具/车削刀具": ["车削刀具", "车刀", "车削"],
            "刀具/铣削刀具": ["铣削刀具", "铣刀", "铣削"],
            "刀具/钻削刀具": ["钻削刀具", "钻头", "钻孔"],
            "刀具/丝锥铰刀镗刀": ["丝锥", "铰刀", "镗刀"],
            "测量工具/卡尺": ["卡尺", "游标卡尺"],
            "测量工具/千分尺": ["千分尺", "螺旋测微器"],
            "测量工具/高度尺": ["高度尺", "高度规"],
            "测量工具/塞规环规": ["塞规", "环规"],
            "测量工具/量块": ["量块", "规尺块"],
            "测量工具/粗糙度仪": ["粗糙度仪", "表面粗糙度"],
            "机床附件/夹具治具": ["夹具", "治具"],
            "机床附件/刀柄夹头": ["刀柄", "夹头"],
            "机床附件/卡盘": ["卡盘"],
            "机床附件/顶尖": ["顶尖"],
            "机床附件/拉钉": ["拉钉"],
            "机床附件/V形块": ["V形块"],
            "五金劳保/紧固件": ["螺栓", "螺母", "垫圈", "紧固件", "螺丝", "销钉"],
            "五金劳保/工具类": ["扳手", "钳子", "锤子", "工具", "起子", "批头"],
            "五金劳保/劳保防护": ["手套", "口罩", "防护", "劳保", "安全帽", "护目镜"],
            "五金劳保/金属制品": ["铁丝", "铁丝网", "铁线", "钢丝", "钢丝绳", "网片", "护栏网", "围栏"],
            "五金劳保/管材管件": ["钢管", "铁管", "管件", "弯头", "三通", "法兰"],
            "五金劳保/板材": ["钢板", "铁板", "铝板", "板材"],
            "包装印刷/包装箱": ["包装箱", "纸箱", "木箱"],
            "包装印刷/缓冲材料": ["珍珠棉", "缓冲材料", "气泡膜", "泡沫"],
            "包装印刷/标签不干胶": ["标签", "不干胶", "贴纸"],
            "包装印刷/说明书": ["说明书", "手册"],
            "化工辅料/切削液": ["切削液", "冷却液"],
            "化工辅料/防锈剂": ["防锈剂", "防锈油"],
            "化工辅料/脱模剂": ["脱模剂", "脱模"],
            "化工辅料/清洗剂": ["清洗剂", "清洁剂", "洗涤"],
            "化工辅料/润滑油脂": ["润滑油", "润滑脂", "黄油", "机油"],
            "电器气动/继电器": ["继电器"],
            "电器气动/接触器": ["接触器"],
            "电器气动/传感器": ["传感器", "探测器"],
            "电器气动/电机": ["电机", "马达", "电动机"],
            "电器气动/气缸": ["气缸", "油缸"],
            "电器气动/气管接头": ["气管", "接头", "快插"],
            "电器气动/开关电源": ["开关", "电源", "变压器", "适配器"],
            "电器气动/线缆": ["电缆", "线缆", "导线", "电线"],
            "磨具磨料/砂轮": ["砂轮", "磨轮"],
            "磨具磨料/砂纸": ["砂纸", "砂布"],
            "磨具磨料/油石": ["油石", "磨石"],
            "磨具磨料/百叶轮": ["百叶轮", "千页轮"],
            "磨具磨料/砂带": ["砂带"],
            "机械零部件/轴承": ["轴承", "滚珠", "滚针"],
            "机械零部件/齿轮": ["齿轮", "蜗轮", "蜗杆"],
            "机械零部件/联轴器": ["联轴器", "联轴"],
            "机械零部件/传动带": ["皮带", "同步带", "传动带", "三角带"],
            "机械零部件/链条": ["链条", "链轮"],
            "原材料/金属材料": ["铝棒", "钢材", "铜材", "铝材", "棒材", "原材料"],
        }
        
        # 初始化 Ollama 后端
        self.ollama = None
        if use_ollama:
            try:
                self.ollama = OllamaBackend()
            except Exception as e:
                logger.warning(f"初始化 Ollama 失败: {e}")
                self.ollama = None
        
        # 向量层原型（作为备用）
        self.prototype_text = {cat: " ".join(words) for cat, words in self.rules.items()}
        self.prototype_vecs = self.embedding.embed(list(self.prototype_text.values()))
        self.prototype_index = list(self.prototype_text.keys())
        
        logger.info("✅ LocalClassifier 初始化完成")

    def _load_categories(self):
        """加载品类配置"""
        try:
            from constants.categories import CATEGORIES, CATEGORY_HIERARCHY
            self.categories = CATEGORIES
            self.category_hierarchy = CATEGORY_HIERARCHY
        except ImportError:
            logger.warning("无法加载品类配置，使用默认品类")
            self.categories = []
            self.category_hierarchy = {}

    def rule_match(self, text: str) -> Optional[str]:
        """规则匹配：优先级最高"""
        t = (text or "").lower()
        for cat, kws in self.rules.items():
            for kw in kws:
                if kw.lower() in t:
                    return cat
        return None

    def embed_match(self, text: str) -> Dict[str, float]:
        """向量匹配：作为大模型的备用方案"""
        try:
            text_vec = self.embedding.embed([text])[0]
            scores = {}
            
            for idx, proto_vec in enumerate(self.prototype_vecs):
                sim = cosine(text_vec, proto_vec)
                scores[self.prototype_index[idx]] = sim
            
            # 只返回 top-5
            top_5 = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5])
            return top_5
        except Exception as e:
            logger.error(f"向量匹配错误: {e}")
            return {}

    def _extract_major_category(self, full_category: str) -> str:
        """从"大类/子类"提取大类"""
        if not full_category:
            return ""
        if "/" in full_category:
            return full_category.split("/")[0].strip()
        return full_category.strip()

    def _extract_minor_category(self, full_category: str) -> str:
        """从"大类/子类"提取子类"""
        if not full_category:
            return ""
        if "/" in full_category:
            parts = full_category.split("/")
            return parts[1].strip() if len(parts) > 1 else ""
        return ""

    def extract_major_category(self, full_category: str) -> str:
        """公共方法：提取大类"""
        return self._extract_major_category(full_category)

    def extract_minor_category(self, full_category: str) -> str:
        """公共方法：提取子类"""
        return self._extract_minor_category(full_category)

    def classify(self, name: str, spec: str = "", remark: str = "") -> Dict:
        """
        分类物料

        改进版：返回category + major_category + minor_category
        新增：添加知识库索引层查询

        Args:
            name: 物料名称
            spec: 规格
            remark: 备注

        Returns:
            {
                "category": "刀具/铣削刀具",
                "major_category": "刀具",
                "minor_category": "铣削刀具",
                "scores": {top-N 评分},
                "source": "cache|rule|knowledge|llm|vector",
                "text": "完整文本"
            }
        """
        text = " ".join([name or "", spec or "", remark or ""]).strip()

        if not text:
            return {
                "category": "未分类",
                "major_category": "",
                "minor_category": "",
                "scores": {},
                "source": "empty",
                "text": text
            }

        # ===== 策略 1：规则匹配（速度快，优先级高）=====
        rule_result = self.rule_match(text)
        if rule_result:
            major = self._extract_major_category(rule_result)
            minor = self._extract_minor_category(rule_result)
            # 如果规则匹配成功，也添加到知识库缓存
            if self.knowledge_service:
                try:
                    self.knowledge_service.add_to_cache(text, rule_result, None, 1.0, "rule")
                except Exception as e:
                    logger.warning(f"添加规则匹配结果到缓存失败: {e}")
            return {
                "category": rule_result,
                "major_category": major,
                "minor_category": minor,
                "scores": {rule_result: 1.0},
                "source": "rule",
                "text": text
            }

        # ===== 策略 2：知识库查询（基于历史数据和专家知识）=====
        if self.knowledge_service:
            try:
                kb_result = self.knowledge_service.search(name, spec)
                if kb_result and kb_result.get("score", 0) >= 0.6:  # 只接受置信度 >= 0.6 的结果
                    category = kb_result["category"]
                    major = self._extract_major_category(category)
                    minor = self._extract_minor_category(category)
                    logger.info(f"✅ 知识库匹配: {name} -> {category} (方法: {kb_result['method']}, 得分: {kb_result['score']:.2f})")
                    return {
                        "category": category,
                        "major_category": major,
                        "minor_category": minor,
                        "scores": {category: kb_result["score"]},
                        "source": f"knowledge_{kb_result['method']}",
                        "text": text
                    }
            except Exception as e:
                logger.error(f"知识库查询失败: {e}")

        # ===== 策略 3：大模型分类（准确度高，需要网络）=====
        if self.ollama and self.ollama.available:
            try:
                categories = self.categories if self.categories else list(self.rules.keys())
                llm_scores = self.ollama.classify_with_llm(text, categories)

                if llm_scores:
                    top_cat = max(llm_scores, key=llm_scores.get)
                    top_score = llm_scores[top_cat]
                    major = self._extract_major_category(top_cat)
                    minor = self._extract_minor_category(top_cat)
                    # 添加到知识库缓存
                    if self.knowledge_service and top_score >= 0.6:
                        try:
                            self.knowledge_service.add_to_cache(text, top_cat, None, top_score, "llm")
                        except Exception as e:
                            logger.warning(f"添加LLM结果到缓存失败: {e}")
                    # 只返回 top-5
                    top_5 = dict(sorted(llm_scores.items(), key=lambda x: x[1], reverse=True)[:5])
                    return {
                        "category": top_cat,
                        "major_category": major,
                        "minor_category": minor,
                        "scores": top_5,
                        "source": "ollama",
                        "text": text
                    }
            except Exception as e:
                logger.error(f"大模型分类失败，降级到向量: {e}")

        # ===== 策略 4：向量匹配（备用方案）=====
        vector_scores = self.embed_match(text)
        if vector_scores:
            top_cat = max(vector_scores, key=vector_scores.get)
            top_score = vector_scores[top_cat]
            major = self._extract_major_category(top_cat)
            minor = self._extract_minor_category(top_cat)
            # 添加到知识库缓存（向量匹配的置信度较低，仅作为备用）
            if self.knowledge_service and top_score >= 0.5:
                try:
                    self.knowledge_service.add_to_cache(text, top_cat, None, top_score, "vector")
                except Exception as e:
                    logger.warning(f"添加向量结果到缓存失败: {e}")
            return {
                "category": top_cat,
                "major_category": major,
                "minor_category": minor,
                "scores": vector_scores,
                "source": "vector",
                "text": text
            }
        
        # ===== 默认：未分类 =====
        return {
            "category": "未分类",
            "major_category": "",
            "minor_category": "",
            "scores": {},
            "source": "default",
            "text": text
        }