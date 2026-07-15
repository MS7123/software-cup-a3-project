import { useEffect, useMemo, useState } from "react";
import type { AnimationSpec } from "../../api/types";

export default function AnimationRenderer({ spec }: { spec: AnimationSpec }) {
  if (spec.template_id === "binary_tree_traversal") {
    return <BinaryTreeTraversalPlayer spec={spec} />;
  }

  return <p className="animation-fallback">当前动画模板暂不支持，请查看下方分镜脚本。</p>;
}

function BinaryTreeTraversalPlayer({ spec }: { spec: AnimationSpec }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const nodesById = useMemo(
    () => new Map(spec.data.nodes.map((node) => [node.id, node])),
    [spec.data.nodes]
  );
  const currentStep = spec.timeline[Math.max(0, currentIndex)];
  const visitedOrder = currentIndex < 0
    ? []
    : spec.timeline
        .slice(0, currentIndex + 1)
        .filter((step) => step.action === "visit")
        .map((step) => step.target);

  useEffect(() => {
    if (!isPlaying) return undefined;
    if (currentIndex >= spec.timeline.length - 1) {
      setIsPlaying(false);
      return undefined;
    }

    const currentAt = spec.timeline[Math.max(0, currentIndex)]?.at_ms ?? 0;
    const nextAt = spec.timeline[currentIndex + 1]?.at_ms ?? currentAt + 1100;
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

  function replay() {
    setIsPlaying(false);
    setCurrentIndex(-1);
  }

  return (
    <article className="svg-animation-player" data-testid="svg-animation-player">
      <header className="animation-player-header">
        <div>
          <span className="animation-template-badge">SVG 实时演示</span>
          <h4>{spec.title}</h4>
          <p>{spec.description}</p>
        </div>
        <span className="animation-duration">{Math.ceil(spec.duration_ms / 1000)} 秒</span>
      </header>

      <div className="animation-stage">
        <svg viewBox="0 0 640 330" role="img" aria-label={`${spec.title}二叉树动画`}>
          <g className="animation-edges" aria-hidden="true">
            {spec.data.edges.map((edge) => {
              const source = nodesById.get(edge.source);
              const target = nodesById.get(edge.target);
              if (!source || !target) return null;
              return <line key={`${edge.source}-${edge.target}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} />;
            })}
          </g>
          <g className="animation-nodes">
            {spec.data.nodes.map((node) => {
              const isVisited = visitedOrder.includes(node.id);
              const isCurrent = currentIndex >= 0 && currentStep?.target === node.id;
              return (
                <g
                  key={node.id}
                  className={`animation-node ${isVisited ? "animation-node-visited" : ""} ${isCurrent ? "animation-node-current" : ""}`}
                  transform={`translate(${node.x} ${node.y})`}
                  data-node-id={node.id}
                >
                  <circle r="28" />
                  <text textAnchor="middle" dominantBaseline="central">{node.label}</text>
                </g>
              );
            })}
          </g>
        </svg>
        <div className="animation-caption" aria-live="polite">
          <span>步骤 {Math.max(0, currentIndex + 1)} / {spec.timeline.length}</span>
          <strong data-testid="animation-step-caption">
            {currentIndex < 0 ? "点击播放，从根节点开始观察" : currentStep?.caption}
          </strong>
        </div>
      </div>

      <footer className="animation-controls">
        <div className="animation-visit-order">
          <span>访问序列</span>
          <strong data-testid="animation-visit-order">
            {visitedOrder.length > 0 ? visitedOrder.join(" → ") : "尚未开始"}
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
          <button type="button" onClick={replay}>重播</button>
        </div>
      </footer>
    </article>
  );
}
