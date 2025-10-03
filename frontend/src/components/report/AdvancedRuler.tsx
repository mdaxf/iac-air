import React from 'react';

interface AdvancedRulerProps {
  direction: 'horizontal' | 'vertical';
  size: number;
  selectedComponent?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  scale?: number;
}

export default function AdvancedRuler({
  direction,
  size,
  selectedComponent,
  scale = 1
}: AdvancedRulerProps) {
  const majorTickInterval = 50;
  const minorTickInterval = 10;
  const labelInterval = 100;

  const ticks = [];

  for (let i = 0; i <= size; i += minorTickInterval) {
    const isMajorTick = i % majorTickInterval === 0;
    const isLabelTick = i % labelInterval === 0;
    const tickLength = isMajorTick ? 12 : 6;

    if (direction === 'horizontal') {
      ticks.push(
        <line
          key={i}
          x1={i * scale}
          y1={20 - tickLength}
          x2={i * scale}
          y2={20}
          stroke="#666"
          strokeWidth={1}
        />
      );

      if (isLabelTick && i > 0) {
        ticks.push(
          <text
            key={`label-${i}`}
            x={i * scale}
            y={12}
            fontSize="10"
            fill="#666"
            textAnchor="middle"
            fontFamily="system-ui"
          >
            {i}
          </text>
        );
      }
    } else {
      ticks.push(
        <line
          key={i}
          x1={20 - tickLength}
          y1={i * scale}
          x2={20}
          y2={i * scale}
          stroke="#666"
          strokeWidth={1}
        />
      );

      if (isLabelTick && i > 0) {
        ticks.push(
          <text
            key={`label-${i}`}
            x={10}
            y={i * scale + 3}
            fontSize="10"
            fill="#666"
            textAnchor="middle"
            fontFamily="system-ui"
            transform={`rotate(-90 10 ${i * scale + 3})`}
          >
            {i}
          </text>
        );
      }
    }
  }

  // Component position indicator
  let componentShadow = null;
  if (selectedComponent) {
    const position = direction === 'horizontal'
      ? selectedComponent.x
      : selectedComponent.y;
    const dimension = direction === 'horizontal'
      ? selectedComponent.width
      : selectedComponent.height;

    if (direction === 'horizontal') {
      componentShadow = (
        <rect
          x={position * scale}
          y={0}
          width={dimension * scale}
          height={20}
          fill="rgba(59, 130, 246, 0.3)"
          stroke="rgb(59, 130, 246)"
          strokeWidth={1}
        />
      );
    } else {
      componentShadow = (
        <rect
          x={0}
          y={position * scale}
          width={20}
          height={dimension * scale}
          fill="rgba(59, 130, 246, 0.3)"
          stroke="rgb(59, 130, 246)"
          strokeWidth={1}
        />
      );
    }
  }

  const svgWidth = direction === 'horizontal' ? size * scale : 20;
  const svgHeight = direction === 'horizontal' ? 20 : size * scale;

  return (
    <div className="ruler">
      <svg
        width={svgWidth}
        height={svgHeight}
        className="ruler-svg"
      >
        <rect width="100%" height="100%" fill="#f8f9fa" />
        {componentShadow}
        {ticks}
      </svg>
    </div>
  );
}