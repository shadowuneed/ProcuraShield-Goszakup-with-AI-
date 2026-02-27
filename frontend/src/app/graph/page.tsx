'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiSearch, FiZoomIn, FiZoomOut, FiMaximize, FiX, FiAlertTriangle,
  FiUsers, FiTarget, FiCrosshair, FiFilter, FiInfo
} from 'react-icons/fi';

/* ══════════════ Типы ══════════════ */
interface GraphNode {
  id: string;
  label: string;
  type: 'company' | 'person' | 'tender' | 'organization';
  risk_score?: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  details?: Record<string, string>;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
  weight: number;
  type: 'ownership' | 'participation' | 'family' | 'address' | 'financial';
}

/* ══════════════ Конфигурация ══════════════ */
const NODE_CONFIG: Record<string, { color: string; glow: string; icon: string; labelRu: string }> = {
  company:      { color: '#3b82f6', glow: 'rgba(59,130,246,0.3)',  icon: '🏢', labelRu: 'Компания' },
  person:       { color: '#a855f7', glow: 'rgba(168,85,247,0.3)',  icon: '👤', labelRu: 'Физ. лицо' },
  tender:       { color: '#22c55e', glow: 'rgba(34,197,94,0.3)',   icon: '📋', labelRu: 'Тендер' },
  organization: { color: '#f59e0b', glow: 'rgba(245,158,11,0.3)', icon: '🏛️', labelRu: 'Госорган' },
};

const EDGE_COLORS: Record<string, string> = {
  ownership:     'rgba(168,85,247,0.5)',
  participation: 'rgba(59,130,246,0.4)',
  family:        'rgba(239,68,68,0.5)',
  address:       'rgba(245,158,11,0.4)',
  financial:     'rgba(34,197,94,0.4)',
};

/* ══════════════ Демо-данные ══════════════ */
function createDemoData(): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [
    { id: 'c1', label: 'ТОО "СтройИнвест"',  type: 'company', risk_score: 85, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИНН': '770312345678', 'Дата рег.': '12.03.2019', 'Директор': 'Иванов И.И.', 'Адрес': 'г. Астана, ул. Мира 15', 'Уст. капитал': '500 000 ₸' } },
    { id: 'c2', label: 'ТОО "МегаСтрой"',     type: 'company', risk_score: 72, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИНН': '770387654321', 'Дата рег.': '05.07.2020', 'Директор': 'Иванов И.И.', 'Адрес': 'г. Астана, ул. Мира 15', 'Уст. капитал': '100 000 ₸' } },
    { id: 'c3', label: 'ТОО "АльфаТрейд"',    type: 'company', risk_score: 65, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИНН': '770398765432', 'Дата рег.': '22.01.2018', 'Директор': 'Петров П.П.', 'Адрес': 'г. Алматы, пр. Абая 42' } },
    { id: 'c4', label: 'ТОО "БетаСервис"',     type: 'company', risk_score: 45, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИНН': '770301234567', 'Дата рег.': '14.11.2021', 'Директор': 'Сидоров С.С.', 'Адрес': 'г. Шымкент, ул. Тауке хана 8' } },
    { id: 'c5', label: 'ТОО "ДельтаПлюс"',     type: 'company', risk_score: 91, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИНН': '770305678901', 'Дата рег.': '03.09.2022', 'Директор': 'Иванов А.И.', 'Адрес': 'г. Астана, ул. Мира 15' } },
    { id: 'p1', label: 'Иванов И.И.',          type: 'person',  risk_score: 90, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИИН': '850315300280', 'Должности': '3 компании', 'ПДЛ': 'Нет', 'Санкции': 'Нет' } },
    { id: 'p2', label: 'Петров П.П.',          type: 'person',  risk_score: 30, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИИН': '900722400185', 'Должности': '1 компания', 'ПДЛ': 'Нет', 'Санкции': 'Нет' } },
    { id: 'p3', label: 'Сидоров С.С.',         type: 'person',  risk_score: 25, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИИН': '880910500390', 'Должности': '1 компания' } },
    { id: 'p4', label: 'Иванов А.И.',          type: 'person',  risk_score: 78, x: 0, y: 0, vx: 0, vy: 0, details: { 'ИИН': '010503600470', 'Должности': '1 компания', 'Отношение': 'Сын Иванова И.И.' } },
    { id: 't1', label: 'Тендер #2024-1234',    type: 'tender',  risk_score: 78, x: 0, y: 0, vx: 0, vy: 0, details: { 'Сумма': '45 200 000 ₸', 'Статус': 'Завершён', 'Категория': 'Строительство', 'Регион': 'Астана' } },
    { id: 't2', label: 'Тендер #2024-5678',    type: 'tender',  risk_score: 55, x: 0, y: 0, vx: 0, vy: 0, details: { 'Сумма': '12 800 000 ₸', 'Статус': 'Активный', 'Категория': 'IT-услуги', 'Регион': 'Алматы' } },
    { id: 't3', label: 'Тендер #2024-9012',    type: 'tender',  risk_score: 88, x: 0, y: 0, vx: 0, vy: 0, details: { 'Сумма': '89 500 000 ₸', 'Статус': 'Завершён', 'Категория': 'Строительство', 'Регион': 'Астана' } },
    { id: 'o1', label: 'Акимат г. Астана',      type: 'organization', x: 0, y: 0, vx: 0, vy: 0, details: { 'Тип': 'Заказчик', 'Тендеров': '156' } },
  ];

  const edges: GraphEdge[] = [
    { source: 'p1', target: 'c1', label: 'Директор',          weight: 1.0,  type: 'ownership' },
    { source: 'p1', target: 'c2', label: 'Учредитель',        weight: 0.9,  type: 'ownership' },
    { source: 'p4', target: 'c5', label: 'Директор',          weight: 1.0,  type: 'ownership' },
    { source: 'p2', target: 'c3', label: 'Директор',          weight: 1.0,  type: 'ownership' },
    { source: 'p3', target: 'c4', label: 'Директор',          weight: 1.0,  type: 'ownership' },
    { source: 'p1', target: 'p4', label: 'Отец-сын',          weight: 0.95, type: 'family' },
    { source: 'p1', target: 'p2', label: 'Бывш. коллеги',     weight: 0.4,  type: 'family' },
    { source: 'c1', target: 'c2', label: 'Один адрес',        weight: 0.7,  type: 'address' },
    { source: 'c1', target: 'c5', label: 'Один адрес',        weight: 0.7,  type: 'address' },
    { source: 'c2', target: 'c5', label: 'Один адрес',        weight: 0.7,  type: 'address' },
    { source: 'c1', target: 't1', label: 'Победитель',        weight: 0.8,  type: 'participation' },
    { source: 'c2', target: 't1', label: 'Участник',          weight: 0.5,  type: 'participation' },
    { source: 'c5', target: 't1', label: 'Участник',          weight: 0.5,  type: 'participation' },
    { source: 'c3', target: 't2', label: 'Победитель',        weight: 0.8,  type: 'participation' },
    { source: 'c1', target: 't3', label: 'Победитель',        weight: 0.8,  type: 'participation' },
    { source: 'c5', target: 't3', label: 'Участник',          weight: 0.5,  type: 'participation' },
    { source: 'o1', target: 't1', label: 'Заказчик',          weight: 0.6,  type: 'participation' },
    { source: 'o1', target: 't3', label: 'Заказчик',          weight: 0.6,  type: 'participation' },
    { source: 'c1', target: 'c3', label: 'Субподряд',         weight: 0.5,  type: 'financial' },
  ];

  return { nodes, edges };
}

/* ══════════════ Force-directed layout ══════════════ */
function useForceLayout(
  nodesRef: React.MutableRefObject<GraphNode[]>,
  edges: GraphEdge[],
  canvasSize: { w: number; h: number },
) {
  const frameRef = useRef<number>(0);

  const tick = useCallback(() => {
    const nodes = nodesRef.current;
    const k = 0.005;  // охлаждение
    const repulsion = 8000;
    const attraction = 0.004;
    const damping = 0.85;
    const cx = canvasSize.w / 2;
    const cy = canvasSize.h / 2;

    // Отталкивание
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = repulsion / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        nodes[i].vx += fx;
        nodes[i].vy += fy;
        nodes[j].vx -= fx;
        nodes[j].vy -= fy;
      }
    }

    // Притяжение по рёбрам
    for (const edge of edges) {
      const src = nodes.find((n) => n.id === edge.source);
      const tgt = nodes.find((n) => n.id === edge.target);
      if (!src || !tgt) continue;
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const force = (dist - 180) * attraction * edge.weight;
      const fx = (dx / Math.max(dist, 1)) * force;
      const fy = (dy / Math.max(dist, 1)) * force;
      src.vx += fx;
      src.vy += fy;
      tgt.vx -= fx;
      tgt.vy -= fy;
    }

    // Гравитация к центру
    for (const node of nodes) {
      node.vx += (cx - node.x) * k;
      node.vy += (cy - node.y) * k;
      node.vx *= damping;
      node.vy *= damping;
      node.x += node.vx;
      node.y += node.vy;
      // Ограничения
      node.x = Math.max(60, Math.min(canvasSize.w - 60, node.x));
      node.y = Math.max(60, Math.min(canvasSize.h - 60, node.y));
    }
  }, [nodesRef, edges, canvasSize]);

  useEffect(() => {
    // Изначальные позиции — случайные
    const nodes = nodesRef.current;
    const cx = canvasSize.w / 2;
    const cy = canvasSize.h / 2;
    for (const node of nodes) {
      node.x = cx + (Math.random() - 0.5) * 400;
      node.y = cy + (Math.random() - 0.5) * 300;
    }
  }, [nodesRef, canvasSize]);

  return { tick, frameRef };
}

/* ══════════════ Отрисовка ══════════════ */
function drawGraph(
  ctx: CanvasRenderingContext2D,
  nodes: GraphNode[],
  edges: GraphEdge[],
  w: number, h: number,
  zoom: number,
  panX: number, panY: number,
  hoveredId: string | null,
  selectedId: string | null,
  filterType: string | null,
) {
  ctx.clearRect(0, 0, w, h);

  // Фон с сеткой
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = 'rgba(51,65,85,0.3)';
  ctx.lineWidth = 0.5;
  const gridSize = 40 * zoom;
  const offsetX = (panX * zoom) % gridSize;
  const offsetY = (panY * zoom) % gridSize;
  for (let x = offsetX; x < w; x += gridSize) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = offsetY; y < h; y += gridSize) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  ctx.save();
  ctx.translate(panX * zoom, panY * zoom);
  ctx.scale(zoom, zoom);

  const posMap: Record<string, { x: number; y: number }> = {};
  for (const n of nodes) posMap[n.id] = { x: n.x, y: n.y };

  const isVisible = (node: GraphNode) => !filterType || node.type === filterType;

  // Рёбра
  for (const edge of edges) {
    const from = posMap[edge.source];
    const to = posMap[edge.target];
    if (!from || !to) continue;

    const srcNode = nodes.find(n => n.id === edge.source);
    const tgtNode = nodes.find(n => n.id === edge.target);
    if (!srcNode || !tgtNode) continue;

    const isHighlighting = hoveredId || selectedId;
    const relevantId = hoveredId || selectedId;
    const isRelevant = edge.source === relevantId || edge.target === relevantId;
    const bothVisible = isVisible(srcNode) && isVisible(tgtNode);

    if (!bothVisible) continue;

    const alpha = isHighlighting ? (isRelevant ? 1 : 0.08) : 0.5;

    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);

    const baseColor = EDGE_COLORS[edge.type] || 'rgba(148,163,184,0.3)';
    ctx.strokeStyle = baseColor;
    ctx.globalAlpha = alpha;
    ctx.lineWidth = isRelevant ? 2.5 : 1.5;
    ctx.setLineDash(edge.type === 'family' ? [6, 4] : []);
    ctx.stroke();
    ctx.setLineDash([]);

    // Подпись ребра
    if (alpha > 0.3) {
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2;
      ctx.fillStyle = '#94a3b8';
      ctx.globalAlpha = alpha * 0.9;
      ctx.font = '9px "Inter", sans-serif';
      ctx.textAlign = 'center';

      // Фон для текста
      const textW = ctx.measureText(edge.label).width + 8;
      ctx.fillStyle = 'rgba(15,23,42,0.8)';
      ctx.fillRect(midX - textW / 2, midY - 7, textW, 14);
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(edge.label, midX, midY + 3);
    }
    ctx.globalAlpha = 1;
  }

  // Узлы
  for (const node of nodes) {
    if (!isVisible(node)) continue;

    const cfg = NODE_CONFIG[node.type] || NODE_CONFIG.company;
    const isHovered = node.id === hoveredId;
    const isSelected = node.id === selectedId;
    const isHighlighting = hoveredId || selectedId;
    const relevantId = hoveredId || selectedId;

    // Проверяем связь с hovered/selected
    const isConnected = edges.some(
      e => (e.source === relevantId && e.target === node.id) || (e.target === relevantId && e.source === node.id)
    );

    const dimmed = isHighlighting && !isHovered && !isSelected && !isConnected && node.id !== relevantId;

    const baseR = node.type === 'company' ? 26 : node.type === 'person' ? 22 : node.type === 'tender' ? 24 : 20;
    const r = isHovered || isSelected ? baseR + 4 : baseR;

    ctx.globalAlpha = dimmed ? 0.15 : 1;

    // Свечение при риске
    if (node.risk_score && node.risk_score >= 70 && !dimmed) {
      const gradient = ctx.createRadialGradient(node.x, node.y, r, node.x, node.y, r + 20);
      gradient.addColorStop(0, 'rgba(239,68,68,0.25)');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fillRect(node.x - r - 20, node.y - r - 20, (r + 20) * 2, (r + 20) * 2);
    }

    // Свечение при выборе/наведении
    if ((isHovered || isSelected) && !dimmed) {
      const gradient = ctx.createRadialGradient(node.x, node.y, r, node.x, node.y, r + 15);
      gradient.addColorStop(0, cfg.glow);
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fillRect(node.x - r - 15, node.y - r - 15, (r + 15) * 2, (r + 15) * 2);
    }

    // Круг узла
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
    const grad = ctx.createRadialGradient(node.x - r * 0.3, node.y - r * 0.3, 0, node.x, node.y, r);
    grad.addColorStop(0, cfg.color);
    grad.addColorStop(1, shadeColor(cfg.color, -30));
    ctx.fillStyle = grad;
    ctx.fill();

    // Обводка
    ctx.strokeStyle = isSelected ? '#ffffff' : isHovered ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.15)';
    ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;
    ctx.stroke();

    // Иконка
    ctx.font = `${r * 0.7}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(cfg.icon, node.x, node.y);

    // Риск-бейдж
    if (node.risk_score && node.risk_score >= 60 && !dimmed) {
      const bx = node.x + r * 0.6;
      const by = node.y - r * 0.6;
      const bcolor = node.risk_score >= 80 ? '#ef4444' : node.risk_score >= 60 ? '#f59e0b' : '#22c55e';
      ctx.beginPath();
      ctx.arc(bx, by, 10, 0, Math.PI * 2);
      ctx.fillStyle = bcolor;
      ctx.fill();
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 8px "Inter", sans-serif';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${node.risk_score}`, bx, by);
    }

    // Подпись
    if (!dimmed) {
      ctx.textBaseline = 'top';
      ctx.font = `${isHovered || isSelected ? 'bold ' : ''}11px "Inter", sans-serif`;
      ctx.textAlign = 'center';

      // Тень текста
      const textW = ctx.measureText(node.label).width + 10;
      ctx.fillStyle = 'rgba(15,23,42,0.85)';
      ctx.fillRect(node.x - textW / 2, node.y + r + 4, textW, 16);
      ctx.fillStyle = isHovered || isSelected ? '#f1f5f9' : '#cbd5e1';
      ctx.fillText(node.label, node.x, node.y + r + 7);
    }

    ctx.globalAlpha = 1;
  }

  ctx.restore();
}

function shadeColor(color: string, percent: number) {
  const num = parseInt(color.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + percent));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00ff) + percent));
  const b = Math.min(255, Math.max(0, (num & 0x0000ff) + percent));
  return `#${(0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1)}`;
}

/* ══════════════════════════════════════════
   ГЛАВНЫЙ КОМПОНЕНТ — ГРАФ СВЯЗЕЙ
   ══════════════════════════════════════════ */
export default function GraphPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasSize, setCanvasSize] = useState({ w: 1200, h: 700 });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [filterType, setFilterType] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragNodeId, setDragNodeId] = useState<string | null>(null);
  const dragStart = useRef({ x: 0, y: 0 });

  const { nodes: demoNodes, edges: demoEdges } = createDemoData();
  const nodesRef = useRef<GraphNode[]>(demoNodes);
  const edgesRef = useRef<GraphEdge[]>(demoEdges);

  const { tick } = useForceLayout(nodesRef, edgesRef.current, canvasSize);

  // Размер canvas  
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setCanvasSize({
          w: containerRef.current.clientWidth,
          h: Math.max(600, window.innerHeight - 300),
        });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Рендер-цикл
  useEffect(() => {
    let animId: number;
    const loop = () => {
      tick();
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          drawGraph(ctx, nodesRef.current, edgesRef.current, canvasSize.w, canvasSize.h, zoom, pan.x, pan.y, hoveredNodeId, selectedNode?.id || null, filterType);
        }
      }
      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [canvasSize, zoom, pan, hoveredNodeId, selectedNode, filterType, tick]);

  // Поиск узла по координатам
  const findNode = useCallback((mx: number, my: number): GraphNode | null => {
    const x = (mx / zoom) - pan.x;
    const y = (my / zoom) - pan.y;
    for (const node of nodesRef.current) {
      const r = node.type === 'company' ? 26 : node.type === 'person' ? 22 : 24;
      const dx = node.x - x;
      const dy = node.y - y;
      if (dx * dx + dy * dy < (r + 5) * (r + 5)) return node;
    }
    return null;
  }, [zoom, pan]);

  const getCanvasCoords = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  // Mouse handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    const { x, y } = getCanvasCoords(e);
    const node = findNode(x, y);
    if (node) {
      setDragNodeId(node.id);
    } else {
      setIsDragging(true);
      dragStart.current = { x: x / zoom - pan.x, y: y / zoom - pan.y };
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const { x, y } = getCanvasCoords(e);

    if (dragNodeId) {
      const node = nodesRef.current.find(n => n.id === dragNodeId);
      if (node) {
        node.x = x / zoom - pan.x;
        node.y = y / zoom - pan.y;
        node.vx = 0;
        node.vy = 0;
      }
      return;
    }

    if (isDragging) {
      setPan({ x: x / zoom - dragStart.current.x, y: y / zoom - dragStart.current.y });
      return;
    }

    const node = findNode(x, y);
    setHoveredNodeId(node?.id || null);
    if (canvasRef.current) {
      canvasRef.current.style.cursor = node ? 'pointer' : 'grab';
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragNodeId(null);
  };

  const handleClick = (e: React.MouseEvent) => {
    const { x, y } = getCanvasCoords(e);
    const node = findNode(x, y);
    setSelectedNode(node);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.08 : 0.08;
    setZoom(z => Math.max(0.3, Math.min(3, z + delta)));
  };

  // Статистика
  const riskNodes = nodesRef.current.filter(n => (n.risk_score || 0) >= 70).length;
  const communities = 3; // Демо

  return (
    <div className="space-y-4">
      {/* Заголовок + управление */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
            Граф связей
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Интерактивная карта связей между компаниями, физ. лицами и тендерами
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Фильтр по типу */}
          <div className="flex items-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-1 gap-1">
            <button
              onClick={() => setFilterType(null)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                ${!filterType ? 'bg-blue-500 text-white' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700'}`}
            >
              Все
            </button>
            {Object.entries(NODE_CONFIG).map(([type, cfg]) => (
              <button
                key={type}
                onClick={() => setFilterType(filterType === type ? null : type)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1
                  ${filterType === type ? 'text-white' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700'}`}
                style={filterType === type ? { backgroundColor: cfg.color } : {}}
              >
                <span>{cfg.icon}</span> {cfg.labelRu}
              </button>
            ))}
          </div>

          {/* Zoom */}
          <div className="flex items-center bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-1 gap-1">
            <button onClick={() => setZoom(z => Math.max(0.3, z - 0.15))} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <FiZoomOut className="w-4 h-4 text-slate-500" />
            </button>
            <span className="text-xs text-slate-400 font-mono w-10 text-center">{(zoom * 100).toFixed(0)}%</span>
            <button onClick={() => setZoom(z => Math.min(3, z + 0.15))} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <FiZoomIn className="w-4 h-4 text-slate-500" />
            </button>
            <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
              <FiMaximize className="w-4 h-4 text-slate-500" />
            </button>
          </div>
        </div>
      </div>

      {/* Мини-статистика */}
      <div className="flex gap-3 flex-wrap">
        {[
          { icon: FiUsers, label: 'Узлов', value: nodesRef.current.length, color: 'text-blue-500' },
          { icon: FiTarget, label: 'Связей', value: edgesRef.current.length, color: 'text-violet-500' },
          { icon: FiAlertTriangle, label: 'Высокий риск', value: riskNodes, color: 'text-red-500' },
          { icon: FiCrosshair, label: 'Кластеров', value: communities, color: 'text-amber-500' },
        ].map((s, i) => (
          <div key={i} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
            <s.icon className={`w-4 h-4 ${s.color}`} />
            <span className="text-xs text-slate-400">{s.label}:</span>
            <span className="text-sm font-bold text-slate-900 dark:text-slate-100">{s.value}</span>
          </div>
        ))}
      </div>

      {/* Граф + Детали */}
      <div className="flex gap-4">
        {/* Canvas */}
        <div ref={containerRef} className="flex-1 relative">
          <div className="rounded-2xl overflow-hidden border border-slate-700/50 shadow-xl">
            <canvas
              ref={canvasRef}
              width={canvasSize.w}
              height={canvasSize.h}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onClick={handleClick}
              onWheel={handleWheel}
              style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
              className="block"
            />
          </div>

          {/* Мини-легенда на canvas */}
          <div className="absolute bottom-4 left-4 flex items-center gap-3 px-4 py-2 bg-slate-900/90 backdrop-blur-sm rounded-xl border border-slate-700/50 text-[10px]">
            {Object.entries(NODE_CONFIG).map(([type, cfg]) => (
              <div key={type} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cfg.color }} />
                <span className="text-slate-400">{cfg.labelRu}</span>
              </div>
            ))}
            <div className="w-px h-3 bg-slate-700" />
            {[
              { label: 'Владение', style: 'border-t-2 border-purple-400 w-4' },
              { label: 'Участие', style: 'border-t-2 border-blue-400 w-4' },
              { label: 'Родство', style: 'border-t-2 border-dashed border-red-400 w-4' },
              { label: 'Адрес', style: 'border-t-2 border-amber-400 w-4' },
              { label: 'Финансы', style: 'border-t-2 border-green-400 w-4' },
            ].map((e, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <div className={e.style} />
                <span className="text-slate-500">{e.label}</span>
              </div>
            ))}
          </div>

          {/* Подсказка */}
          <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 bg-slate-900/80 backdrop-blur-sm rounded-lg border border-slate-700/50">
            <FiInfo className="w-3 h-3 text-slate-500" />
            <span className="text-[10px] text-slate-400">Кликните на узел • Перетаскивайте • Скролл = зум</span>
          </div>
        </div>

        {/* Панель деталей */}
        <AnimatePresence>
          {selectedNode && (
            <motion.div
              initial={{ opacity: 0, x: 30, width: 0 }}
              animate={{ opacity: 1, x: 0, width: 320 }}
              exit={{ opacity: 0, x: 30, width: 0 }}
              className="w-80 flex-shrink-0 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-xl"
            >
              {/* Шапка */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-700" style={{ background: `linear-gradient(135deg, ${NODE_CONFIG[selectedNode.type]?.color}15, transparent)` }}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl">{NODE_CONFIG[selectedNode.type]?.icon}</span>
                  <button onClick={() => setSelectedNode(null)} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                    <FiX className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">{selectedNode.label}</h3>
                <span className="text-xs px-2 py-0.5 rounded-full mt-1 inline-block"
                  style={{ backgroundColor: `${NODE_CONFIG[selectedNode.type]?.color}20`, color: NODE_CONFIG[selectedNode.type]?.color }}>
                  {NODE_CONFIG[selectedNode.type]?.labelRu}
                </span>
              </div>

              {/* Риск */}
              {selectedNode.risk_score !== undefined && (
                <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                  <p className="text-xs font-medium text-slate-400 mb-2">Уровень риска</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-3 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${selectedNode.risk_score}%` }}
                        className="h-full rounded-full"
                        style={{
                          background: selectedNode.risk_score >= 80 ? 'linear-gradient(90deg, #ef4444, #dc2626)'
                            : selectedNode.risk_score >= 60 ? 'linear-gradient(90deg, #f59e0b, #d97706)'
                            : 'linear-gradient(90deg, #22c55e, #16a34a)',
                        }}
                      />
                    </div>
                    <span className={`text-lg font-extrabold ${
                      selectedNode.risk_score >= 80 ? 'text-red-500' : selectedNode.risk_score >= 60 ? 'text-amber-500' : 'text-green-500'
                    }`}>
                      {selectedNode.risk_score}
                    </span>
                  </div>
                </div>
              )}

              {/* Детали */}
              {selectedNode.details && (
                <div className="p-4 space-y-2">
                  <p className="text-xs font-medium text-slate-400 mb-2">Информация</p>
                  {Object.entries(selectedNode.details).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50">
                      <span className="text-xs text-slate-400">{key}</span>
                      <span className="text-xs font-medium text-slate-800 dark:text-slate-200">{val}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Связи */}
              <div className="p-4 border-t border-slate-200 dark:border-slate-700">
                <p className="text-xs font-medium text-slate-400 mb-2">
                  Связи ({edgesRef.current.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).length})
                </p>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {edgesRef.current
                    .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e, i) => {
                      const otherId = e.source === selectedNode.id ? e.target : e.source;
                      const other = nodesRef.current.find(n => n.id === otherId);
                      return (
                        <div
                          key={i}
                          onClick={() => other && setSelectedNode(other)}
                          className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer group"
                        >
                          <span className="text-xs">{NODE_CONFIG[other?.type || 'company']?.icon}</span>
                          <span className="text-xs text-slate-700 dark:text-slate-300 flex-1 truncate group-hover:text-blue-500">
                            {other?.label}
                          </span>
                          <span className="text-[10px] text-slate-400 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 rounded">
                            {e.label}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
