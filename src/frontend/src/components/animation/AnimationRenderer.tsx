import { useEffect, useMemo, useState } from "react";
import type { AnimationNode, AnimationSpec } from "../../api/types";

export default function AnimationRenderer({ spec }: { spec: AnimationSpec }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const currentStep = spec.timeline[Math.max(0, currentIndex)];
  const completedTargets = currentIndex < 0 ? [] : spec.timeline.slice(0, currentIndex + 1).map((step) => step.target);

  useEffect(() => {
    if (!isPlaying) return undefined;
    if (currentIndex >= spec.timeline.length - 1) {
      setIsPlaying(false);
      return undefined;
    }
    const currentAt = spec.timeline[Math.max(0, currentIndex)]?.at_ms ?? 0;
    const nextAt = spec.timeline[currentIndex + 1]?.at_ms ?? currentAt + 1000;
    const timer = window.setTimeout(
      () => setCurrentIndex((index) => Math.min(index + 1, spec.timeline.length - 1)),
      Math.max(650, nextAt - currentAt)
    );
    return () => window.clearTimeout(timer);
  }, [currentIndex, isPlaying, spec.timeline]);

  function togglePlayback() {
    if (currentIndex >= spec.timeline.length - 1) setCurrentIndex(0);
    setIsPlaying((playing) => !playing);
  }

  return (
    <article className="svg-animation-player" data-testid="svg-animation-player" data-template-id={spec.template_id}>
      <header className="animation-player-header">
        <div>
          <span className="animation-template-badge">SVG 实时演示</span>
          <h4>{spec.title}</h4>
          <p>{spec.description}</p>
        </div>
        <span className="animation-duration">{Math.ceil(spec.duration_ms / 1000)} 秒</span>
      </header>

      <div className="animation-stage">
        <Scene spec={spec} currentTarget={currentIndex < 0 ? null : currentStep?.target ?? null} completedTargets={completedTargets} />
        <div className="animation-caption" aria-live="polite">
          <span>步骤 {Math.max(0, currentIndex + 1)} / {spec.timeline.length}</span>
          <strong data-testid="animation-step-caption">
            {currentIndex < 0 ? "点击播放，观察结构如何逐步变化" : currentStep?.caption}
          </strong>
        </div>
      </div>

      <footer className="animation-controls">
        <div className="animation-visit-order">
          <span>演示序列</span>
          <strong data-testid="animation-visit-order">
            {completedTargets.length > 0 ? completedTargets.map((id) => spec.data.nodes.find((node) => node.id === id)?.label ?? id).join(" → ") : "尚未开始"}
          </strong>
        </div>
        <div className="animation-control-buttons">
          <button type="button" onClick={togglePlayback}>{isPlaying ? "暂停动画" : "播放动画"}</button>
          <button
            type="button"
            onClick={() => {
              setIsPlaying(false);
              setCurrentIndex((index) => Math.min(index + 1, spec.timeline.length - 1));
            }}
            disabled={currentIndex >= spec.timeline.length - 1}
          >
            下一步
          </button>
          <button type="button" onClick={() => { setIsPlaying(false); setCurrentIndex(-1); }}>重播</button>
        </div>
      </footer>
    </article>
  );
}

function Scene({ spec, currentTarget, completedTargets }: { spec: AnimationSpec; currentTarget: string | null; completedTargets: string[] }) {
  const nodeMap = useMemo(() => new Map(spec.data.nodes.map((node) => [node.id, node])), [spec.data.nodes]);
  const isBarScene = spec.template_id === "complexity_visualizer" || spec.template_id === "sorting_visualizer";
  const isBoxScene = ["linear_structure", "stack_queue_operations", "search_visualizer", "algorithm_workflow"].includes(spec.template_id);
  const classNameFor = (node: AnimationNode) => [
    "animation-node",
    completedTargets.includes(node.id) ? "animation-node-visited" : "",
    currentTarget === node.id ? "animation-node-current" : "",
  ].filter(Boolean).join(" ");

  return (
    <svg viewBox="0 0 640 330" role="img" aria-label={`${spec.title}动画`} data-testid="animation-scene">
      <defs>
        <marker id="animation-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" />
        </marker>
      </defs>
      <g className="animation-edges" aria-hidden="true">
        {spec.data.edges.map((edge) => {
          const source = nodeMap.get(edge.source);
          const target = nodeMap.get(edge.target);
          if (!source || !target) return null;
          const key = `${edge.source}-${edge.target}`;
          return (
            <g key={key}>
              <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} markerEnd="url(#animation-arrow)" />
              {edge.label ? <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 8}>{edge.label}</text> : null}
            </g>
          );
        })}
      </g>
      <g className={`animation-nodes animation-scene-${spec.template_id}`}>
        {spec.data.nodes.map((node) => {
          const className = classNameFor(node);
          if (isBarScene) {
            const height = Math.max(42, (node.value ?? 20) * 2.15);
            return (
              <g key={node.id} className={`${className} animation-bar`} transform={`translate(${node.x} 300)`} data-node-id={node.id}>
                <rect x="-34" y={-height} width="68" height={height} rx="8" />
                <text textAnchor="middle" y={-height - 12}>{node.label}</text>
              </g>
            );
          }
          if (isBoxScene) {
            const width = spec.template_id === "algorithm_workflow" ? 112 : 88;
            return (
              <g key={node.id} className={`${className} animation-box`} transform={`translate(${node.x} ${node.y})`} data-node-id={node.id}>
                <rect x={-width / 2} y="-27" width={width} height="54" rx="9" />
                <text textAnchor="middle" dominantBaseline="central">{node.label}</text>
              </g>
            );
          }
          return (
            <g key={node.id} className={className} transform={`translate(${node.x} ${node.y})`} data-node-id={node.id}>
              <circle r={node.kind === "focus" ? 42 : 28} />
              <text textAnchor="middle" dominantBaseline="central">{node.label}</text>
            </g>
          );
        })}
      </g>
    </svg>
  );
}
