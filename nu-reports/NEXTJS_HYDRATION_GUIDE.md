# Next.js + Firebase Hydration Guide

Server-first architecture for financial analysis data with minimal client-side JavaScript.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tailwind CSS Setup](#tailwind-css-setup)
3. [Recharts Setup](#recharts-setup)
4. [Adaptive Signal Charts](#adaptive-signal-charts)
5. [Firebase Admin Setup](#firebase-admin-setup)
6. [Data Access Layer](#data-access-layer)
7. [Server Components](#server-components)
8. [Server Actions](#server-actions)
9. [Streaming & Suspense](#streaming--suspense)
10. [Caching Strategies](#caching-strategies)
11. [When to Use Client Components](#when-to-use-client-components)
12. [Python Integration Patterns](#python-integration-patterns)
13. [Security Best Practices](#security-best-practices)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Next.js App                          │
├─────────────────────────────────────────────────────────────┤
│  Server Components (default)     │  Client Components       │
│  ─────────────────────────────   │  (minimal, isolated)     │
│  • Data fetching                 │  • Interactive charts    │
│  • Firebase queries              │  • Real-time updates     │
│  • HTML rendering                │  • Form inputs           │
│  • Zero JS shipped               │  • onClick handlers      │
├─────────────────────────────────────────────────────────────┤
│                     Server Actions                          │
│  • Mutations (upload, update)                               │
│  • Form submissions                                         │
│  • Revalidation triggers                                    │
├─────────────────────────────────────────────────────────────┤
│                   Data Access Layer                         │
│  • Firebase Admin SDK                                       │
│  • Type-safe queries                                        │
│  • Caching & revalidation                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Firebase                               │
│  analyses/  │  signals/  │  ai_outputs/                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Python Pipeline                           │
│  • Analysis generation                                      │
│  • Signal detection                                         │
│  • AI recommendations                                       │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Server Components by Default** - No "use client" unless absolutely necessary
2. **Data Fetching at the Top** - Fetch in layouts/pages, pass down as props
3. **Composition Over Configuration** - Small, focused components
4. **Type Safety End-to-End** - TypeScript from Firebase to UI
5. **Single Responsibility** - Each module has one clear purpose

---

## Tailwind CSS Setup

### 1. Installation

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Configuration

```javascript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Signal strength colors
        bullish: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        bearish: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        neutral: {
          50: '#fafafa',
          100: '#f4f4f5',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
        },
        // Category colors for charts
        fibonacci: '#8b5cf6',
        macd: '#06b6d4',
        rsi: '#f59e0b',
        stochastic: '#ec4899',
        ma: '#3b82f6',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

### 3. Global Styles

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --border: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;
  }
}

@layer components {
  /* Signal strength badges */
  .signal-bullish {
    @apply bg-bullish-100 text-bullish-700 border-bullish-500;
  }
  .signal-bearish {
    @apply bg-bearish-100 text-bearish-700 border-bearish-500;
  }
  .signal-neutral {
    @apply bg-neutral-100 text-neutral-700 border-neutral-500;
  }

  /* Chart container */
  .chart-container {
    @apply w-full h-64 md:h-80 lg:h-96 rounded-lg border bg-white dark:bg-neutral-900 p-4;
  }

  /* Card styles */
  .card {
    @apply rounded-lg border bg-white dark:bg-neutral-900 shadow-sm;
  }
  .card-header {
    @apply flex flex-col space-y-1.5 p-6;
  }
  .card-content {
    @apply p-6 pt-0;
  }
}
```

### 4. Utility Functions for Dynamic Colors

```typescript
// lib/utils/tailwind.ts

import type { Signal } from '@/lib/types/analysis';

export function getStrengthClasses(strength: Signal['strength']): string {
  const classes: Record<Signal['strength'], string> = {
    BULLISH: 'bg-bullish-100 text-bullish-700 border-bullish-500',
    STRONG: 'bg-bullish-100 text-bullish-700 border-bullish-500',
    BEARISH: 'bg-bearish-100 text-bearish-700 border-bearish-500',
    WEAK: 'bg-neutral-100 text-neutral-600 border-neutral-400',
    MODERATE: 'bg-amber-100 text-amber-700 border-amber-500',
    NEUTRAL: 'bg-neutral-100 text-neutral-700 border-neutral-500',
  };
  return classes[strength] ?? classes.NEUTRAL;
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    FIBONACCI: '#8b5cf6',
    MACD: '#06b6d4',
    RSI: '#f59e0b',
    STOCHASTIC: '#ec4899',
    MA_RIBBON: '#3b82f6',
    MA_POSITION: '#3b82f6',
  };
  return colors[category] ?? '#71717a';
}

export function getConfidenceWidth(confidence: number): string {
  // Returns Tailwind width class based on confidence (0-1)
  const percent = Math.round(confidence * 100);
  if (percent >= 80) return 'w-full';
  if (percent >= 60) return 'w-4/5';
  if (percent >= 40) return 'w-3/5';
  if (percent >= 20) return 'w-2/5';
  return 'w-1/5';
}

// For dynamic inline styles (when Tailwind classes aren't sufficient)
export function getConfidenceStyle(confidence: number): React.CSSProperties {
  return { width: `${Math.round(confidence * 100)}%` };
}
```

---

## Recharts Setup

### 1. Installation

```bash
npm install recharts
```

### 2. Chart Theme Configuration

```typescript
// lib/charts/theme.ts

export const CHART_COLORS = {
  // Primary palette
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  accent: '#06b6d4',

  // Signal colors
  bullish: '#22c55e',
  bearish: '#ef4444',
  neutral: '#71717a',

  // Category colors
  categories: {
    FIBONACCI: '#8b5cf6',
    MACD: '#06b6d4',
    RSI: '#f59e0b',
    STOCHASTIC: '#ec4899',
    MA_RIBBON: '#3b82f6',
    MA_POSITION: '#10b981',
  } as Record<string, string>,

  // Strength colors
  strengths: {
    BULLISH: '#22c55e',
    STRONG: '#16a34a',
    BEARISH: '#ef4444',
    WEAK: '#9ca3af',
    MODERATE: '#f59e0b',
    NEUTRAL: '#71717a',
  } as Record<string, string>,

  // Grid and axis
  grid: '#e5e7eb',
  axis: '#6b7280',
  tooltip: {
    bg: '#ffffff',
    border: '#e5e7eb',
    text: '#1f2937',
  },
};

export const CHART_CONFIG = {
  margin: { top: 20, right: 30, left: 20, bottom: 20 },
  fontSize: 12,
  fontFamily: 'system-ui, -apple-system, sans-serif',
};
```

### 3. Reusable Chart Components

```typescript
// components/charts/base-chart.tsx
'use client';

import { ResponsiveContainer } from 'recharts';
import type { ReactNode } from 'react';

interface BaseChartProps {
  children: ReactNode;
  height?: number;
  className?: string;
}

export function BaseChart({ children, height = 300, className = '' }: BaseChartProps) {
  return (
    <div className={`chart-container ${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}
```

```typescript
// components/charts/custom-tooltip.tsx
'use client';

import type { TooltipProps } from 'recharts';
import { CHART_COLORS } from '@/lib/charts/theme';

interface CustomTooltipProps extends TooltipProps<number, string> {
  formatValue?: (value: number) => string;
  formatLabel?: (label: string) => string;
}

export function CustomTooltip({
  active,
  payload,
  label,
  formatValue = (v) => v.toFixed(2),
  formatLabel = (l) => l,
}: CustomTooltipProps) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div
      className="rounded-lg border bg-white p-3 shadow-lg dark:bg-neutral-900"
      style={{
        borderColor: CHART_COLORS.tooltip.border,
      }}
    >
      <p className="mb-2 font-medium text-sm">{formatLabel(label)}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium">{formatValue(entry.value as number)}</span>
        </div>
      ))}
    </div>
  );
}
```

---

## Adaptive Signal Charts

Charts that dynamically render based on whatever signals the pipeline detects.

### 1. Signal Chart Factory

```typescript
// components/charts/signal-chart-factory.tsx
import type { Signal } from '@/lib/types/analysis';
import { SignalRadarChart } from './signal-radar-chart';
import { SignalBarChart } from './signal-bar-chart';
import { SignalCategoryPie } from './signal-category-pie';
import { SignalConfidenceGauge } from './signal-confidence-gauge';
import { SignalStrengthHeatmap } from './signal-strength-heatmap';
import { SignalTimelineChart } from './signal-timeline-chart';

interface SignalChartFactoryProps {
  signals: Signal[];
  variant?: 'radar' | 'bar' | 'pie' | 'gauge' | 'heatmap' | 'timeline' | 'auto';
}

export function SignalChartFactory({ signals, variant = 'auto' }: SignalChartFactoryProps) {
  if (signals.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        No signals to display
      </div>
    );
  }

  // Auto-select best chart based on signal characteristics
  if (variant === 'auto') {
    const categories = new Set(signals.map((s) => s.category));
    const hasMultipleCategories = categories.size > 2;
    const hasConfidenceVariance = hasSignificantVariance(signals.map((s) => s.confidence));

    if (hasMultipleCategories && signals.length >= 4) {
      return <SignalRadarChart signals={signals} />;
    }
    if (hasConfidenceVariance) {
      return <SignalBarChart signals={signals} />;
    }
    return <SignalCategoryPie signals={signals} />;
  }

  // Explicit variant selection
  switch (variant) {
    case 'radar':
      return <SignalRadarChart signals={signals} />;
    case 'bar':
      return <SignalBarChart signals={signals} />;
    case 'pie':
      return <SignalCategoryPie signals={signals} />;
    case 'gauge':
      return <SignalConfidenceGauge signals={signals} />;
    case 'heatmap':
      return <SignalStrengthHeatmap signals={signals} />;
    case 'timeline':
      return <SignalTimelineChart signals={signals} />;
    default:
      return <SignalBarChart signals={signals} />;
  }
}

function hasSignificantVariance(values: number[]): boolean {
  if (values.length < 2) return false;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  return Math.sqrt(variance) > 0.15;
}
```

### 2. Radar Chart (Multi-category overview)

```typescript
// components/charts/signal-radar-chart.tsx
'use client';

import { useMemo } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
  Legend,
} from 'recharts';
import { BaseChart } from './base-chart';
import { CustomTooltip } from './custom-tooltip';
import { CHART_COLORS } from '@/lib/charts/theme';
import type { Signal } from '@/lib/types/analysis';

interface SignalRadarChartProps {
  signals: Signal[];
}

export function SignalRadarChart({ signals }: SignalRadarChartProps) {
  const data = useMemo(() => {
    // Group by category and calculate aggregate metrics
    const categories = signals.reduce<Record<string, { confidence: number; count: number; strength: number }>>((acc, signal) => {
      const cat = signal.category;
      if (!acc[cat]) {
        acc[cat] = { confidence: 0, count: 0, strength: 0 };
      }
      acc[cat].confidence += signal.confidence;
      acc[cat].count += 1;
      acc[cat].strength += strengthToNumber(signal.strength);
      return acc;
    }, {});

    return Object.entries(categories).map(([category, data]) => ({
      category: formatCategory(category),
      confidence: Math.round((data.confidence / data.count) * 100),
      strength: Math.round((data.strength / data.count) * 100),
      count: data.count,
    }));
  }, [signals]);

  return (
    <BaseChart height={350}>
      <RadarChart data={data}>
        <PolarGrid stroke={CHART_COLORS.grid} />
        <PolarAngleAxis
          dataKey="category"
          tick={{ fontSize: 11, fill: CHART_COLORS.axis }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: CHART_COLORS.axis }}
        />
        <Radar
          name="Confidence"
          dataKey="confidence"
          stroke={CHART_COLORS.primary}
          fill={CHART_COLORS.primary}
          fillOpacity={0.3}
        />
        <Radar
          name="Strength"
          dataKey="strength"
          stroke={CHART_COLORS.secondary}
          fill={CHART_COLORS.secondary}
          fillOpacity={0.3}
        />
        <Tooltip content={<CustomTooltip formatValue={(v) => `${v}%`} />} />
        <Legend />
      </RadarChart>
    </BaseChart>
  );
}

function strengthToNumber(strength: Signal['strength']): number {
  const map: Record<Signal['strength'], number> = {
    STRONG: 1,
    BULLISH: 0.8,
    MODERATE: 0.6,
    NEUTRAL: 0.5,
    WEAK: 0.3,
    BEARISH: 0.2,
  };
  return map[strength] ?? 0.5;
}

function formatCategory(category: string): string {
  return category.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
```

### 3. Bar Chart (Signal comparison)

```typescript
// components/charts/signal-bar-chart.tsx
'use client';

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts';
import { BaseChart } from './base-chart';
import { CustomTooltip } from './custom-tooltip';
import { CHART_COLORS, CHART_CONFIG } from '@/lib/charts/theme';
import type { Signal } from '@/lib/types/analysis';

interface SignalBarChartProps {
  signals: Signal[];
  sortBy?: 'confidence' | 'value' | 'category';
}

export function SignalBarChart({ signals, sortBy = 'confidence' }: SignalBarChartProps) {
  const data = useMemo(() => {
    const sorted = [...signals].sort((a, b) => {
      if (sortBy === 'confidence') return b.confidence - a.confidence;
      if (sortBy === 'value') return b.value - a.value;
      return a.category.localeCompare(b.category);
    });

    return sorted.map((signal) => ({
      name: truncate(signal.name, 20),
      fullName: signal.name,
      confidence: Math.round(signal.confidence * 100),
      category: signal.category,
      strength: signal.strength,
      value: signal.value,
    }));
  }, [signals, sortBy]);

  const avgConfidence = useMemo(() => {
    return Math.round(signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length * 100);
  }, [signals]);

  return (
    <BaseChart height={Math.max(300, signals.length * 40)}>
      <BarChart data={data} layout="vertical" margin={CHART_CONFIG.margin}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis }}
          tickFormatter={(v) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={120}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis }}
        />
        <Tooltip
          content={
            <CustomTooltip
              formatValue={(v) => `${v}%`}
              formatLabel={(label) => data.find((d) => d.name === label)?.fullName ?? label}
            />
          }
        />
        <ReferenceLine
          x={avgConfidence}
          stroke={CHART_COLORS.neutral}
          strokeDasharray="5 5"
          label={{ value: 'Avg', position: 'top', fontSize: 10 }}
        />
        <Bar dataKey="confidence" radius={[0, 4, 4, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={CHART_COLORS.categories[entry.category] ?? CHART_COLORS.neutral}
            />
          ))}
        </Bar>
      </BarChart>
    </BaseChart>
  );
}

function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max - 1) + '...' : str;
}
```

### 4. Category Pie Chart

```typescript
// components/charts/signal-category-pie.tsx
'use client';

import { useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { BaseChart } from './base-chart';
import { CHART_COLORS } from '@/lib/charts/theme';
import type { Signal } from '@/lib/types/analysis';

interface SignalCategoryPieProps {
  signals: Signal[];
}

export function SignalCategoryPie({ signals }: SignalCategoryPieProps) {
  const data = useMemo(() => {
    const counts = signals.reduce<Record<string, number>>((acc, signal) => {
      acc[signal.category] = (acc[signal.category] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(counts)
      .map(([category, count]) => ({
        name: formatCategory(category),
        value: count,
        category,
      }))
      .sort((a, b) => b.value - a.value);
  }, [signals]);

  return (
    <BaseChart height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          labelLine={{ stroke: CHART_COLORS.axis }}
        >
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={CHART_COLORS.categories[entry.category] ?? CHART_COLORS.neutral}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [`${value} signals`, 'Count']}
        />
      </PieChart>
    </BaseChart>
  );
}

function formatCategory(category: string): string {
  return category.replace(/_/g, ' ');
}
```

### 5. Confidence Gauge (Aggregate view)

```typescript
// components/charts/signal-confidence-gauge.tsx
'use client';

import { useMemo } from 'react';
import { PieChart, Pie, Cell } from 'recharts';
import { BaseChart } from './base-chart';
import { CHART_COLORS } from '@/lib/charts/theme';
import type { Signal } from '@/lib/types/analysis';

interface SignalConfidenceGaugeProps {
  signals: Signal[];
}

export function SignalConfidenceGauge({ signals }: SignalConfidenceGaugeProps) {
  const { avgConfidence, sentiment, color } = useMemo(() => {
    const avg = signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length;
    const bullish = signals.filter((s) => s.strength === 'BULLISH' || s.strength === 'STRONG').length;
    const bearish = signals.filter((s) => s.strength === 'BEARISH' || s.strength === 'WEAK').length;

    let sentiment: 'bullish' | 'bearish' | 'neutral' = 'neutral';
    let color = CHART_COLORS.neutral;

    if (bullish > bearish) {
      sentiment = 'bullish';
      color = CHART_COLORS.bullish;
    } else if (bearish > bullish) {
      sentiment = 'bearish';
      color = CHART_COLORS.bearish;
    }

    return { avgConfidence: avg, sentiment, color };
  }, [signals]);

  const gaugeData = [
    { value: avgConfidence * 100 },
    { value: 100 - avgConfidence * 100 },
  ];

  return (
    <div className="flex flex-col items-center">
      <BaseChart height={200}>
        <PieChart>
          <Pie
            data={gaugeData}
            cx="50%"
            cy="70%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={90}
            paddingAngle={0}
            dataKey="value"
          >
            <Cell fill={color} />
            <Cell fill={CHART_COLORS.grid} />
          </Pie>
        </PieChart>
      </BaseChart>
      <div className="text-center -mt-8">
        <p className="text-3xl font-bold" style={{ color }}>
          {Math.round(avgConfidence * 100)}%
        </p>
        <p className="text-sm text-muted-foreground capitalize">
          {sentiment} ({signals.length} signals)
        </p>
      </div>
    </div>
  );
}
```

### 6. Strength Heatmap

```typescript
// components/charts/signal-strength-heatmap.tsx
'use client';

import { useMemo } from 'react';
import { CHART_COLORS } from '@/lib/charts/theme';
import type { Signal } from '@/lib/types/analysis';

interface SignalStrengthHeatmapProps {
  signals: Signal[];
}

export function SignalStrengthHeatmap({ signals }: SignalStrengthHeatmapProps) {
  const grid = useMemo(() => {
    // Create a 2D grid: categories x strength levels
    const categories = [...new Set(signals.map((s) => s.category))].sort();
    const strengths: Signal['strength'][] = ['STRONG', 'BULLISH', 'MODERATE', 'NEUTRAL', 'WEAK', 'BEARISH'];

    return {
      categories,
      strengths,
      cells: categories.map((cat) => ({
        category: cat,
        values: strengths.map((str) => {
          const matching = signals.filter((s) => s.category === cat && s.strength === str);
          return {
            strength: str,
            count: matching.length,
            avgConfidence: matching.length > 0
              ? matching.reduce((sum, s) => sum + s.confidence, 0) / matching.length
              : 0,
          };
        }),
      })),
    };
  }, [signals]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="p-2 text-left font-medium text-muted-foreground">Category</th>
            {grid.strengths.map((str) => (
              <th key={str} className="p-2 text-center font-medium text-muted-foreground">
                {str}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.cells.map((row) => (
            <tr key={row.category} className="border-t">
              <td className="p-2 font-medium">{formatCategory(row.category)}</td>
              {row.values.map((cell) => (
                <td key={cell.strength} className="p-1">
                  <div
                    className="mx-auto flex h-10 w-10 items-center justify-center rounded text-xs font-medium text-white"
                    style={{
                      backgroundColor: cell.count > 0
                        ? getHeatColor(cell.avgConfidence, cell.strength)
                        : '#f4f4f5',
                      color: cell.count > 0 ? 'white' : '#a1a1aa',
                    }}
                  >
                    {cell.count > 0 ? cell.count : '-'}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function getHeatColor(confidence: number, strength: Signal['strength']): string {
  const baseColor = CHART_COLORS.strengths[strength] ?? CHART_COLORS.neutral;
  // Adjust opacity based on confidence
  const opacity = 0.4 + confidence * 0.6;
  return adjustColorOpacity(baseColor, opacity);
}

function adjustColorOpacity(hex: string, opacity: number): string {
  // Simple opacity adjustment - for production use a proper color library
  const alpha = Math.round(opacity * 255).toString(16).padStart(2, '0');
  return hex + alpha;
}

function formatCategory(category: string): string {
  return category.replace(/_/g, ' ');
}
```

### 7. Dynamic Dashboard with Adaptive Charts

```typescript
// components/analysis/signal-charts-section.tsx (Server Component)
import type { Signal } from '@/lib/types/analysis';
import { SignalChartFactory } from '@/components/charts/signal-chart-factory';

interface SignalChartsSectionProps {
  signals: Signal[];
}

export function SignalChartsSection({ signals }: SignalChartsSectionProps) {
  // Group signals for different visualizations
  const categories = [...new Set(signals.map((s) => s.category))];
  const hasManyCategories = categories.length >= 3;
  const hasManySignals = signals.length >= 5;

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-semibold">Signal Analysis</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overview chart - auto-selected based on data */}
        <div className="card">
          <div className="card-header">
            <h3 className="font-medium">Signal Overview</h3>
          </div>
          <div className="card-content">
            <SignalChartFactory signals={signals} variant="auto" />
          </div>
        </div>

        {/* Confidence gauge */}
        <div className="card">
          <div className="card-header">
            <h3 className="font-medium">Aggregate Confidence</h3>
          </div>
          <div className="card-content">
            <SignalChartFactory signals={signals} variant="gauge" />
          </div>
        </div>

        {/* Category breakdown - only if multiple categories */}
        {hasManyCategories && (
          <div className="card">
            <div className="card-header">
              <h3 className="font-medium">By Category</h3>
            </div>
            <div className="card-content">
              <SignalChartFactory signals={signals} variant="pie" />
            </div>
          </div>
        )}

        {/* Detailed bar chart - only if many signals */}
        {hasManySignals && (
          <div className="card lg:col-span-2">
            <div className="card-header">
              <h3 className="font-medium">Signal Confidence Ranking</h3>
            </div>
            <div className="card-content">
              <SignalChartFactory signals={signals} variant="bar" />
            </div>
          </div>
        )}

        {/* Heatmap for comprehensive view */}
        {hasManyCategories && hasManySignals && (
          <div className="card lg:col-span-2">
            <div className="card-header">
              <h3 className="font-medium">Strength Distribution</h3>
            </div>
            <div className="card-content">
              <SignalChartFactory signals={signals} variant="heatmap" />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
```

### 8. Indicator Charts (Dynamic based on available data)

```typescript
// components/charts/indicator-chart.tsx
'use client';

import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { BaseChart } from './base-chart';
import { CHART_COLORS } from '@/lib/charts/theme';
import type { IndicatorData } from '@/lib/types/analysis';

interface IndicatorChartProps {
  indicators: IndicatorData;
  showMAs?: boolean;
  showMACD?: boolean;
}

export function IndicatorChart({ indicators, showMAs = true, showMACD = true }: IndicatorChartProps) {
  const maData = useMemo(() => {
    if (!showMAs) return [];

    const smaKeys = Object.keys(indicators).filter((k) => k.startsWith('SMA_'));
    return smaKeys
      .map((key) => ({
        name: key.replace('SMA_', 'SMA '),
        value: indicators[key as keyof IndicatorData] as number,
        period: parseInt(key.replace('SMA_', '')),
      }))
      .sort((a, b) => a.period - b.period);
  }, [indicators, showMAs]);

  const priceVsMA = useMemo(() => {
    const price = indicators.Current_Price;
    return maData.map((ma) => ({
      ...ma,
      diff: ((price - ma.value) / ma.value * 100).toFixed(2),
      aboveMA: price > ma.value,
    }));
  }, [indicators.Current_Price, maData]);

  return (
    <div className="space-y-6">
      {/* Price vs MAs */}
      {showMAs && maData.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-medium">Price vs Moving Averages</h3>
          </div>
          <div className="card-content">
            <BaseChart height={250}>
              <ComposedChart data={priceVsMA}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis
                  yAxisId="price"
                  domain={['auto', 'auto']}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `$${v.toFixed(0)}`}
                />
                <YAxis
                  yAxisId="diff"
                  orientation="right"
                  domain={[-10, 10]}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip />
                <Legend />
                <ReferenceLine
                  yAxisId="price"
                  y={indicators.Current_Price}
                  stroke={CHART_COLORS.primary}
                  strokeDasharray="5 5"
                  label={{ value: `Price: $${indicators.Current_Price.toFixed(2)}`, position: 'right' }}
                />
                <Bar yAxisId="price" dataKey="value" fill={CHART_COLORS.ma} name="MA Value" />
                <Line
                  yAxisId="diff"
                  type="monotone"
                  dataKey="diff"
                  stroke={CHART_COLORS.accent}
                  name="% from Price"
                  dot={{ fill: CHART_COLORS.accent }}
                />
              </ComposedChart>
            </BaseChart>
          </div>
        </div>
      )}

      {/* MACD */}
      {showMACD && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-medium">MACD Analysis</h3>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold" style={{
                  color: indicators.MACD > 0 ? CHART_COLORS.bullish : CHART_COLORS.bearish
                }}>
                  {indicators.MACD.toFixed(4)}
                </p>
                <p className="text-sm text-muted-foreground">MACD</p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {indicators.MACD_Signal.toFixed(4)}
                </p>
                <p className="text-sm text-muted-foreground">Signal</p>
              </div>
              <div>
                <p className="text-2xl font-bold" style={{
                  color: indicators.MACD > indicators.MACD_Signal
                    ? CHART_COLORS.bullish
                    : CHART_COLORS.bearish
                }}>
                  {(indicators.MACD - indicators.MACD_Signal).toFixed(4)}
                </p>
                <p className="text-sm text-muted-foreground">Histogram</p>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-center gap-2">
              <div
                className="h-3 w-3 rounded-full"
                style={{
                  backgroundColor: indicators.MACD > indicators.MACD_Signal
                    ? CHART_COLORS.bullish
                    : CHART_COLORS.bearish
                }}
              />
              <span className="text-sm font-medium">
                {indicators.MACD > indicators.MACD_Signal ? 'Bullish Crossover' : 'Bearish Crossover'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 9. Complete Analysis Page with Adaptive Charts

```typescript
// app/analysis/[symbol]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { AnalysisService } from '@/lib/services/analysis-service';
import { AnalysisHeader } from '@/components/analysis/header';
import { SignalChartsSection } from '@/components/analysis/signal-charts-section';
import { IndicatorChart } from '@/components/charts/indicator-chart';
import { AIInsights } from '@/components/analysis/ai-insights';
import { ChartSkeleton } from '@/components/skeletons';

interface PageProps {
  params: Promise<{ symbol: string }>;
}

export default async function AnalysisPage({ params }: PageProps) {
  const { symbol } = await params;
  const data = await AnalysisService.getFullAnalysis(symbol);

  if (!data) {
    notFound();
  }

  const { analysis, signals, aiOutput } = data;

  return (
    <main className="container mx-auto py-8 space-y-8">
      <AnalysisHeader analysis={analysis} />

      {/* Adaptive signal charts - renders based on what signals exist */}
      <Suspense fallback={<ChartSkeleton />}>
        <SignalChartsSection signals={signals} />
      </Suspense>

      {/* Indicator charts - adapts to available indicators */}
      <Suspense fallback={<ChartSkeleton />}>
        <IndicatorChart
          indicators={analysis.indicators}
          showMAs={hasMovingAverages(analysis.indicators)}
          showMACD={hasMACD(analysis.indicators)}
        />
      </Suspense>

      {/* AI Insights */}
      {aiOutput && (
        <Suspense fallback={<ChartSkeleton />}>
          <AIInsights output={aiOutput} />
        </Suspense>
      )}
    </main>
  );
}

function hasMovingAverages(indicators: Record<string, unknown>): boolean {
  return Object.keys(indicators).some((k) => k.startsWith('SMA_'));
}

function hasMACD(indicators: Record<string, unknown>): boolean {
  return 'MACD' in indicators && 'MACD_Signal' in indicators;
}
```

### 10. Chart Loading Skeletons

```typescript
// components/skeletons/chart-skeleton.tsx
export function ChartSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="card-header">
        <div className="h-5 w-32 bg-muted rounded" />
      </div>
      <div className="card-content">
        <div className="h-64 bg-muted rounded flex items-center justify-center">
          <svg
            className="h-12 w-12 text-muted-foreground/50"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}

export function MultiChartSkeleton({ count = 2 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <ChartSkeleton key={i} />
      ))}
    </div>
  );
}
```

---

## Firebase Admin Setup

### 1. Install Dependencies

```bash
npm install firebase-admin
```

### 2. Singleton Pattern for Firebase Admin

```typescript
// lib/firebase-admin.ts
import { initializeApp, getApps, cert, type App } from 'firebase-admin/app';
import { getFirestore, type Firestore } from 'firebase-admin/firestore';

// Singleton instance
let firebaseApp: App | null = null;
let firestoreDb: Firestore | null = null;

function getFirebaseApp(): App {
  if (firebaseApp) {
    return firebaseApp;
  }

  const existingApps = getApps();
  if (existingApps.length > 0) {
    firebaseApp = existingApps[0];
    return firebaseApp;
  }

  // Initialize new app
  firebaseApp = initializeApp({
    credential: cert({
      projectId: process.env.FIREBASE_PROJECT_ID,
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
      privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
    }),
  });

  return firebaseApp;
}

export function getDb(): Firestore {
  if (firestoreDb) {
    return firestoreDb;
  }

  getFirebaseApp();
  firestoreDb = getFirestore();
  return firestoreDb;
}
```

### 3. Environment Variables

```bash
# .env.local (never commit this)
FIREBASE_PROJECT_ID=testy-test-65614
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@testy-test-65614.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

---

## Data Access Layer

Following **Single Responsibility** and **Law of Demeter** principles.

### 1. Type Definitions

```typescript
// lib/types/analysis.ts
export interface Analysis {
  id: string;
  symbol: string;
  interval: string;
  timestamp: Date;
  bars_analyzed: number;
  indicators: IndicatorData;
  signal_summary: SignalSummary;
  ai_enabled: boolean;
}

export interface Signal {
  id: string;
  analysis_id: string;
  symbol: string;
  name: string;
  category: SignalCategory;
  strength: 'WEAK' | 'MODERATE' | 'STRONG' | 'NEUTRAL' | 'BULLISH' | 'BEARISH';
  confidence: number;
  description: string;
  trading_implication: string | null;
  value: number;
  indicator_name: string;
}

export interface AIOutput {
  id: string;
  signal_summary: string;
  trading_recommendation: TradingRecommendation;
  risk_assessment: RiskAssessment;
  volatility_regime: VolatilityRegime;
  opportunities: Opportunity[];
  alerts: Alert[];
}

export type SignalCategory =
  | 'FIBONACCI'
  | 'MA_RIBBON'
  | 'MA_POSITION'
  | 'RSI'
  | 'STOCHASTIC'
  | 'MACD';

export interface IndicatorData {
  Current_Price: number;
  Open: number;
  High: number;
  Low: number;
  Volume: number;
  MACD: number;
  MACD_Signal: number;
  OBV: number;
  SMA_10: number;
  SMA_20: number;
  SMA_50: number;
  SMA_100: number;
  SMA_200: number;
}

export interface SignalSummary {
  total: number;
  bullish: number;
  bearish: number;
  neutral: number;
}

export interface TradingRecommendation {
  recommendation: 'BUY' | 'SELL' | 'NEUTRAL';
  entry: number;
  stop_loss: number;
  target: number;
  risk_reward_ratio: number;
  confidence: number;
  reasoning: string;
  position_size_adjustment: string;
}

export interface RiskAssessment {
  overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  identified_risks: string[];
  recommended_stop_loss_pct: number;
  position_size_adjustment: string;
}

export interface VolatilityRegime {
  regime: 'LOW_VOLATILITY' | 'NORMAL' | 'HIGH_VOLATILITY';
  hv_30d: string;
  atr_pct: string;
  recommended_action: string;
}

export interface Opportunity {
  type: string;
  description: string;
  entry_trigger: string;
  confidence: number;
  action: string;
}

export interface Alert {
  type: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
}
```

### 2. Repository Pattern

```typescript
// lib/repositories/analysis-repository.ts
import { getDb } from '@/lib/firebase-admin';
import type { Analysis, Signal, AIOutput } from '@/lib/types/analysis';

// Transform Firestore document to typed object
function toAnalysis(doc: FirebaseFirestore.DocumentSnapshot): Analysis {
  const data = doc.data();
  if (!data) {
    throw new Error(`Analysis not found: ${doc.id}`);
  }

  return {
    id: doc.id,
    symbol: data.symbol,
    interval: data.interval,
    timestamp: data.timestamp?.toDate() ?? new Date(),
    bars_analyzed: data.bars_analyzed,
    indicators: data.indicators,
    signal_summary: data.signal_summary,
    ai_enabled: data.ai_enabled,
  };
}

function toSignal(doc: FirebaseFirestore.DocumentSnapshot): Signal {
  const data = doc.data();
  if (!data) {
    throw new Error(`Signal not found: ${doc.id}`);
  }

  return {
    id: doc.id,
    analysis_id: data.analysis_id,
    symbol: data.symbol,
    name: data.name,
    category: data.category,
    strength: data.strength,
    confidence: data.confidence,
    description: data.description,
    trading_implication: data.trading_implication,
    value: data.value,
    indicator_name: data.indicator_name,
  };
}

function toAIOutput(doc: FirebaseFirestore.DocumentSnapshot): AIOutput {
  const data = doc.data();
  if (!data) {
    throw new Error(`AI Output not found: ${doc.id}`);
  }

  return {
    id: doc.id,
    signal_summary: data.signal_summary,
    trading_recommendation: data.trading_recommendation,
    risk_assessment: data.risk_assessment,
    volatility_regime: data.volatility_regime,
    opportunities: data.opportunities ?? [],
    alerts: data.alerts ?? [],
  };
}

export const AnalysisRepository = {
  async getAll(): Promise<Analysis[]> {
    const db = getDb();
    const snapshot = await db
      .collection('analyses')
      .orderBy('timestamp', 'desc')
      .get();

    return snapshot.docs.map(toAnalysis);
  },

  async getBySymbol(symbol: string): Promise<Analysis | null> {
    const db = getDb();
    const snapshot = await db
      .collection('analyses')
      .where('symbol', '==', symbol.toUpperCase())
      .orderBy('timestamp', 'desc')
      .limit(1)
      .get();

    if (snapshot.empty) {
      return null;
    }

    return toAnalysis(snapshot.docs[0]);
  },

  async getById(id: string): Promise<Analysis | null> {
    const db = getDb();
    const doc = await db.collection('analyses').doc(id).get();

    if (!doc.exists) {
      return null;
    }

    return toAnalysis(doc);
  },
};

export const SignalRepository = {
  async getByAnalysisId(analysisId: string): Promise<Signal[]> {
    const db = getDb();
    const snapshot = await db
      .collection('signals')
      .where('analysis_id', '==', analysisId)
      .get();

    return snapshot.docs.map(toSignal);
  },

  async getBySymbol(symbol: string): Promise<Signal[]> {
    const db = getDb();
    const snapshot = await db
      .collection('signals')
      .where('symbol', '==', symbol.toUpperCase())
      .orderBy('timestamp', 'desc')
      .get();

    return snapshot.docs.map(toSignal);
  },

  async getByCategory(category: string): Promise<Signal[]> {
    const db = getDb();
    const snapshot = await db
      .collection('signals')
      .where('category', '==', category)
      .get();

    return snapshot.docs.map(toSignal);
  },

  async getBullish(limit = 20): Promise<Signal[]> {
    const db = getDb();
    const snapshot = await db
      .collection('signals')
      .where('strength', '==', 'BULLISH')
      .orderBy('confidence', 'desc')
      .limit(limit)
      .get();

    return snapshot.docs.map(toSignal);
  },
};

export const AIOutputRepository = {
  async getByAnalysisId(analysisId: string): Promise<AIOutput | null> {
    const db = getDb();
    const doc = await db.collection('ai_outputs').doc(analysisId).get();

    if (!doc.exists) {
      return null;
    }

    return toAIOutput(doc);
  },
};
```

### 3. Service Layer (Aggregation)

```typescript
// lib/services/analysis-service.ts
import { AnalysisRepository, SignalRepository, AIOutputRepository } from '@/lib/repositories/analysis-repository';
import type { Analysis, Signal, AIOutput } from '@/lib/types/analysis';

export interface FullAnalysis {
  analysis: Analysis;
  signals: Signal[];
  aiOutput: AIOutput | null;
}

export const AnalysisService = {
  async getFullAnalysis(symbol: string): Promise<FullAnalysis | null> {
    const analysis = await AnalysisRepository.getBySymbol(symbol);

    if (!analysis) {
      return null;
    }

    // Parallel fetch for signals and AI output
    const [signals, aiOutput] = await Promise.all([
      SignalRepository.getByAnalysisId(analysis.id),
      AIOutputRepository.getByAnalysisId(analysis.id),
    ]);

    return { analysis, signals, aiOutput };
  },

  async getDashboardData(): Promise<{
    analyses: Analysis[];
    bullishSignals: Signal[];
  }> {
    const [analyses, bullishSignals] = await Promise.all([
      AnalysisRepository.getAll(),
      SignalRepository.getBullish(10),
    ]);

    return { analyses, bullishSignals };
  },
};
```

---

## Server Components

### 1. Page Component (Data Fetching)

```typescript
// app/analysis/[symbol]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { AnalysisService } from '@/lib/services/analysis-service';
import { AnalysisHeader } from '@/components/analysis/header';
import { SignalList } from '@/components/analysis/signal-list';
import { AIInsights } from '@/components/analysis/ai-insights';
import { IndicatorGrid } from '@/components/analysis/indicator-grid';
import { SignalsSkeleton, AIInsightsSkeleton } from '@/components/skeletons';

interface PageProps {
  params: Promise<{ symbol: string }>;
}

export default async function AnalysisPage({ params }: PageProps) {
  const { symbol } = await params;
  const data = await AnalysisService.getFullAnalysis(symbol);

  if (!data) {
    notFound();
  }

  const { analysis, signals, aiOutput } = data;

  return (
    <main className="container mx-auto py-8 space-y-8">
      {/* Static content - rendered immediately */}
      <AnalysisHeader analysis={analysis} />
      <IndicatorGrid indicators={analysis.indicators} />

      {/* Streamed content with suspense boundaries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Suspense fallback={<SignalsSkeleton />}>
          <SignalList signals={signals} />
        </Suspense>

        <Suspense fallback={<AIInsightsSkeleton />}>
          <AIInsights output={aiOutput} />
        </Suspense>
      </div>
    </main>
  );
}

// Generate static params for common symbols
export async function generateStaticParams() {
  return [
    { symbol: 'NVDA' },
    { symbol: 'AAPL' },
    { symbol: 'MSFT' },
    { symbol: 'SPY' },
    { symbol: 'QQQ' },
  ];
}

// Metadata
export async function generateMetadata({ params }: PageProps) {
  const { symbol } = await params;
  return {
    title: `${symbol.toUpperCase()} Analysis`,
    description: `Technical analysis and AI insights for ${symbol.toUpperCase()}`,
  };
}
```

### 2. Pure Display Components (No State)

```typescript
// components/analysis/header.tsx
import type { Analysis } from '@/lib/types/analysis';
import { formatDate } from '@/lib/utils/format';

interface AnalysisHeaderProps {
  analysis: Analysis;
}

export function AnalysisHeader({ analysis }: AnalysisHeaderProps) {
  const { signal_summary } = analysis;

  return (
    <header className="border-b pb-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{analysis.symbol}</h1>
          <p className="text-muted-foreground">
            {formatDate(analysis.timestamp)} | {analysis.interval} | {analysis.bars_analyzed} bars
          </p>
        </div>

        <div className="flex gap-4 text-sm">
          <SignalBadge label="Bullish" count={signal_summary.bullish} variant="success" />
          <SignalBadge label="Bearish" count={signal_summary.bearish} variant="danger" />
          <SignalBadge label="Neutral" count={signal_summary.neutral} variant="muted" />
        </div>
      </div>
    </header>
  );
}

interface SignalBadgeProps {
  label: string;
  count: number;
  variant: 'success' | 'danger' | 'muted';
}

function SignalBadge({ label, count, variant }: SignalBadgeProps) {
  const colors = {
    success: 'bg-green-100 text-green-800',
    danger: 'bg-red-100 text-red-800',
    muted: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-3 py-1 rounded-full ${colors[variant]}`}>
      {label}: {count}
    </span>
  );
}
```

```typescript
// components/analysis/signal-list.tsx
import type { Signal } from '@/lib/types/analysis';

interface SignalListProps {
  signals: Signal[];
}

export function SignalList({ signals }: SignalListProps) {
  if (signals.length === 0) {
    return (
      <section className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Signals</h2>
        <p className="text-muted-foreground">No signals detected</p>
      </section>
    );
  }

  // Group signals by category
  const grouped = signals.reduce<Record<string, Signal[]>>((acc, signal) => {
    const category = signal.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(signal);
    return acc;
  }, {});

  return (
    <section className="border rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">
        Signals ({signals.length})
      </h2>

      <div className="space-y-6">
        {Object.entries(grouped).map(([category, categorySignals]) => (
          <SignalCategory
            key={category}
            category={category}
            signals={categorySignals}
          />
        ))}
      </div>
    </section>
  );
}

interface SignalCategoryProps {
  category: string;
  signals: Signal[];
}

function SignalCategory({ category, signals }: SignalCategoryProps) {
  return (
    <div>
      <h3 className="text-sm font-medium text-muted-foreground mb-2">
        {category}
      </h3>
      <ul className="space-y-2">
        {signals.map((signal) => (
          <SignalItem key={signal.id} signal={signal} />
        ))}
      </ul>
    </div>
  );
}

function SignalItem({ signal }: { signal: Signal }) {
  const strengthColors: Record<string, string> = {
    BULLISH: 'text-green-600',
    BEARISH: 'text-red-600',
    STRONG: 'text-green-600',
    MODERATE: 'text-yellow-600',
    WEAK: 'text-gray-500',
    NEUTRAL: 'text-gray-500',
  };

  return (
    <li className="flex items-start justify-between p-3 bg-muted/50 rounded">
      <div>
        <p className="font-medium">{signal.name}</p>
        <p className="text-sm text-muted-foreground">{signal.description}</p>
        {signal.trading_implication && (
          <p className="text-sm mt-1 italic">{signal.trading_implication}</p>
        )}
      </div>
      <div className="text-right">
        <span className={`font-medium ${strengthColors[signal.strength] ?? ''}`}>
          {signal.strength}
        </span>
        <p className="text-xs text-muted-foreground">
          {(signal.confidence * 100).toFixed(0)}% conf
        </p>
      </div>
    </li>
  );
}
```

```typescript
// components/analysis/indicator-grid.tsx
import type { IndicatorData } from '@/lib/types/analysis';
import { formatNumber, formatVolume } from '@/lib/utils/format';

interface IndicatorGridProps {
  indicators: IndicatorData;
}

export function IndicatorGrid({ indicators }: IndicatorGridProps) {
  return (
    <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <IndicatorCard
        label="Price"
        value={formatNumber(indicators.Current_Price)}
        highlight
      />
      <IndicatorCard
        label="Volume"
        value={formatVolume(indicators.Volume)}
      />
      <IndicatorCard
        label="MACD"
        value={formatNumber(indicators.MACD)}
        trend={indicators.MACD > indicators.MACD_Signal ? 'up' : 'down'}
      />
      <IndicatorCard
        label="SMA 20"
        value={formatNumber(indicators.SMA_20)}
      />
      <IndicatorCard
        label="SMA 50"
        value={formatNumber(indicators.SMA_50)}
      />
      <IndicatorCard
        label="SMA 200"
        value={formatNumber(indicators.SMA_200)}
      />
    </section>
  );
}

interface IndicatorCardProps {
  label: string;
  value: string;
  highlight?: boolean;
  trend?: 'up' | 'down';
}

function IndicatorCard({ label, value, highlight, trend }: IndicatorCardProps) {
  return (
    <div className={`p-4 rounded-lg border ${highlight ? 'bg-primary/5 border-primary' : ''}`}>
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-semibold ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : ''}`}>
        {value}
      </p>
    </div>
  );
}
```

### 3. AI Insights Component

```typescript
// components/analysis/ai-insights.tsx
import type { AIOutput } from '@/lib/types/analysis';

interface AIInsightsProps {
  output: AIOutput | null;
}

export function AIInsights({ output }: AIInsightsProps) {
  if (!output) {
    return (
      <section className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">AI Insights</h2>
        <p className="text-muted-foreground">AI analysis not available</p>
      </section>
    );
  }

  const { trading_recommendation, risk_assessment, volatility_regime } = output;

  return (
    <section className="border rounded-lg p-6 space-y-6">
      <h2 className="text-xl font-semibold">AI Insights</h2>

      {/* Trading Recommendation */}
      <RecommendationCard recommendation={trading_recommendation} />

      {/* Risk Assessment */}
      <div>
        <h3 className="font-medium mb-2">Risk Assessment</h3>
        <div className="flex items-center gap-2">
          <RiskBadge level={risk_assessment.overall_risk_level} />
          <span className="text-sm text-muted-foreground">
            {risk_assessment.position_size_adjustment}
          </span>
        </div>
      </div>

      {/* Volatility */}
      <div>
        <h3 className="font-medium mb-2">Volatility Regime</h3>
        <p className="text-sm">{volatility_regime.regime.replace(/_/g, ' ')}</p>
        <p className="text-sm text-muted-foreground">
          {volatility_regime.recommended_action}
        </p>
      </div>

      {/* Summary */}
      <div>
        <h3 className="font-medium mb-2">Analysis Summary</h3>
        <div className="text-sm space-y-2 whitespace-pre-line">
          {output.signal_summary}
        </div>
      </div>
    </section>
  );
}

function RecommendationCard({ recommendation }: { recommendation: AIOutput['trading_recommendation'] }) {
  const colors = {
    BUY: 'border-green-500 bg-green-50',
    SELL: 'border-red-500 bg-red-50',
    NEUTRAL: 'border-gray-300 bg-gray-50',
  };

  return (
    <div className={`p-4 rounded-lg border-2 ${colors[recommendation.recommendation]}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-lg font-bold">{recommendation.recommendation}</span>
        <span className="text-sm">
          {(recommendation.confidence * 100).toFixed(0)}% confidence
        </span>
      </div>
      <p className="text-sm">{recommendation.reasoning}</p>
      <p className="text-xs text-muted-foreground mt-2">
        {recommendation.position_size_adjustment}
      </p>
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    LOW: 'bg-green-100 text-green-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    HIGH: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[level] ?? colors.MEDIUM}`}>
      {level}
    </span>
  );
}
```

---

## Server Actions

For mutations (triggering Python pipeline, refreshing data).

```typescript
// app/actions/analysis.ts
'use server';

import { revalidatePath } from 'next/cache';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface RunAnalysisResult {
  success: boolean;
  message: string;
  symbols?: string[];
}

export async function runAnalysis(formData: FormData): Promise<RunAnalysisResult> {
  const symbols = formData.get('symbols') as string;
  const withAI = formData.get('withAI') === 'true';

  if (!symbols) {
    return { success: false, message: 'No symbols provided' };
  }

  const symbolList = symbols
    .toUpperCase()
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  if (symbolList.length === 0) {
    return { success: false, message: 'Invalid symbols' };
  }

  try {
    // Run Python pipeline
    const aiFlag = withAI ? '--ai' : '';
    const command = `python main.py ${symbolList.join(' ')} ${aiFlag} --export firebase`;

    const { stdout, stderr } = await execAsync(command, {
      cwd: process.env.PYTHON_PIPELINE_PATH,
      timeout: 120000, // 2 minute timeout
    });

    if (stderr && !stderr.includes('WARNING')) {
      console.error('Pipeline stderr:', stderr);
    }

    // Revalidate affected pages
    for (const symbol of symbolList) {
      revalidatePath(`/analysis/${symbol}`);
    }
    revalidatePath('/');
    revalidatePath('/dashboard');

    return {
      success: true,
      message: `Analysis complete for ${symbolList.length} symbols`,
      symbols: symbolList,
    };
  } catch (error) {
    console.error('Pipeline error:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Pipeline failed',
    };
  }
}

export async function refreshAnalysis(symbol: string): Promise<void> {
  'use server';

  revalidatePath(`/analysis/${symbol}`);
  revalidatePath('/');
}
```

### Using Server Actions in Forms

```typescript
// components/analysis/run-analysis-form.tsx
import { runAnalysis } from '@/app/actions/analysis';
import { SubmitButton } from '@/components/ui/submit-button';

export function RunAnalysisForm() {
  return (
    <form action={runAnalysis} className="space-y-4">
      <div>
        <label htmlFor="symbols" className="block text-sm font-medium">
          Symbols (comma-separated)
        </label>
        <input
          type="text"
          id="symbols"
          name="symbols"
          placeholder="NVDA, AAPL, MSFT"
          className="mt-1 block w-full rounded border px-3 py-2"
          required
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="withAI"
          name="withAI"
          value="true"
          className="rounded"
        />
        <label htmlFor="withAI" className="text-sm">
          Include AI Analysis
        </label>
      </div>

      <SubmitButton>Run Analysis</SubmitButton>
    </form>
  );
}
```

```typescript
// components/ui/submit-button.tsx
'use client';

import { useFormStatus } from 'react-dom';

interface SubmitButtonProps {
  children: React.ReactNode;
}

export function SubmitButton({ children }: SubmitButtonProps) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="px-4 py-2 bg-primary text-primary-foreground rounded disabled:opacity-50"
    >
      {pending ? 'Processing...' : children}
    </button>
  );
}
```

---

## Streaming & Suspense

### Layout with Streaming

```typescript
// app/dashboard/layout.tsx
import { Suspense } from 'react';
import { DashboardNav } from '@/components/dashboard/nav';
import { DashboardSkeleton } from '@/components/skeletons';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <DashboardNav />
      <main className="flex-1 p-8">
        <Suspense fallback={<DashboardSkeleton />}>
          {children}
        </Suspense>
      </main>
    </div>
  );
}
```

### Parallel Data Fetching

```typescript
// app/dashboard/page.tsx
import { Suspense } from 'react';
import { AnalysisService } from '@/lib/services/analysis-service';
import { AnalysisTable } from '@/components/dashboard/analysis-table';
import { TopSignals } from '@/components/dashboard/top-signals';
import { TableSkeleton, SignalsSkeleton } from '@/components/skeletons';

export default async function DashboardPage() {
  // Single service call handles parallel fetching internally
  const { analyses, bullishSignals } = await AnalysisService.getDashboardData();

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Suspense fallback={<TableSkeleton />}>
            <AnalysisTable analyses={analyses} />
          </Suspense>
        </div>

        <div>
          <Suspense fallback={<SignalsSkeleton />}>
            <TopSignals signals={bullishSignals} />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
```

---

## Caching Strategies

### 1. Route Segment Config

```typescript
// app/analysis/[symbol]/page.tsx

// Revalidate every 5 minutes
export const revalidate = 300;

// Or use dynamic for real-time data
// export const dynamic = 'force-dynamic';
```

### 2. Fetch-level Caching

```typescript
// lib/repositories/analysis-repository.ts
import { unstable_cache } from 'next/cache';

export const AnalysisRepository = {
  getBySymbol: unstable_cache(
    async (symbol: string) => {
      const db = getDb();
      const snapshot = await db
        .collection('analyses')
        .where('symbol', '==', symbol.toUpperCase())
        .orderBy('timestamp', 'desc')
        .limit(1)
        .get();

      if (snapshot.empty) return null;
      return toAnalysis(snapshot.docs[0]);
    },
    ['analysis-by-symbol'],
    {
      revalidate: 300, // 5 minutes
      tags: ['analyses'],
    }
  ),
};
```

### 3. On-Demand Revalidation

```typescript
// app/api/revalidate/route.ts
import { revalidateTag, revalidatePath } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const { secret, tag, path } = await request.json();

  // Verify webhook secret
  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 });
  }

  if (tag) {
    revalidateTag(tag);
  }

  if (path) {
    revalidatePath(path);
  }

  return NextResponse.json({ revalidated: true, now: Date.now() });
}
```

---

## When to Use Client Components

Only use `'use client'` for:

### 1. Interactive Charts

```typescript
// components/charts/price-chart.tsx
'use client';

import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface PriceChartProps {
  data: Array<{ date: string; price: number }>;
}

export function PriceChart({ data }: PriceChartProps) {
  const formattedData = useMemo(() =>
    data.map(d => ({
      ...d,
      date: new Date(d.date).toLocaleDateString(),
    })),
    [data]
  );

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={formattedData}>
        <XAxis dataKey="date" />
        <YAxis domain={['auto', 'auto']} />
        <Tooltip />
        <Line type="monotone" dataKey="price" stroke="#2563eb" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### 2. Real-time Updates (WebSocket)

```typescript
// components/realtime/price-ticker.tsx
'use client';

import { useEffect, useState } from 'react';

interface PriceTickerProps {
  symbol: string;
  initialPrice: number;
}

export function PriceTicker({ symbol, initialPrice }: PriceTickerProps) {
  const [price, setPrice] = useState(initialPrice);
  const [change, setChange] = useState(0);

  useEffect(() => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket(`wss://stream.example.com/${symbol}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setChange(data.price - price);
      setPrice(data.price);
    };

    return () => ws.close();
  }, [symbol]);

  return (
    <div className="flex items-center gap-2">
      <span className="text-2xl font-bold">${price.toFixed(2)}</span>
      <span className={change >= 0 ? 'text-green-600' : 'text-red-600'}>
        {change >= 0 ? '+' : ''}{change.toFixed(2)}
      </span>
    </div>
  );
}
```

### 3. Client-side Form Validation

```typescript
// components/forms/symbol-search.tsx
'use client';

import { useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';

export function SymbolSearch() {
  const [symbol, setSymbol] = useState('');
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) return;

    startTransition(() => {
      router.push(`/analysis/${symbol.toUpperCase()}`);
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
        placeholder="Enter symbol..."
        className="px-3 py-2 border rounded"
        maxLength={5}
      />
      <button
        type="submit"
        disabled={isPending || !symbol.trim()}
        className="px-4 py-2 bg-primary text-white rounded disabled:opacity-50"
      >
        {isPending ? 'Loading...' : 'Search'}
      </button>
    </form>
  );
}
```

### Composition Pattern: Server Wrapper + Client Island

```typescript
// components/analysis/price-section.tsx (Server Component)
import { AnalysisRepository } from '@/lib/repositories/analysis-repository';
import { PriceChart } from './price-chart'; // Client Component

interface PriceSectionProps {
  symbol: string;
}

export async function PriceSection({ symbol }: PriceSectionProps) {
  // Data fetching happens on server
  const priceHistory = await AnalysisRepository.getPriceHistory(symbol);

  return (
    <section className="border rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Price History</h2>
      {/* Pass data to client component as props */}
      <PriceChart data={priceHistory} />
    </section>
  );
}
```

---

## Python Integration Patterns

### 1. Direct Subprocess Execution

```typescript
// lib/python/executor.ts
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface PipelineOptions {
  symbols: string[];
  interval?: string;
  withAI?: boolean;
  exportFormat?: 'json' | 'firebase';
}

interface PipelineResult {
  success: boolean;
  output?: string;
  error?: string;
}

export async function runPipeline(options: PipelineOptions): Promise<PipelineResult> {
  const { symbols, interval = '1d', withAI = false, exportFormat = 'firebase' } = options;

  const args = [
    ...symbols,
    `--interval ${interval}`,
    withAI ? '--ai' : '',
    `--export ${exportFormat}`,
  ].filter(Boolean).join(' ');

  try {
    const { stdout, stderr } = await execAsync(
      `python main.py ${args}`,
      {
        cwd: process.env.PYTHON_PIPELINE_PATH,
        timeout: 180000, // 3 minutes
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
        },
      }
    );

    return { success: true, output: stdout };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { success: false, error: message };
  }
}
```

### 2. API Route for Pipeline

```typescript
// app/api/pipeline/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { runPipeline } from '@/lib/python/executor';
import { revalidatePath } from 'next/cache';

export async function POST(request: NextRequest) {
  const { symbols, withAI } = await request.json();

  if (!symbols || !Array.isArray(symbols)) {
    return NextResponse.json(
      { error: 'symbols array required' },
      { status: 400 }
    );
  }

  const result = await runPipeline({ symbols, withAI });

  if (result.success) {
    // Revalidate affected pages
    for (const symbol of symbols) {
      revalidatePath(`/analysis/${symbol}`);
    }
    revalidatePath('/dashboard');
  }

  return NextResponse.json(result);
}
```

### 3. Background Processing with Queue

```typescript
// lib/queue/analysis-queue.ts
import { Queue, Worker } from 'bullmq';
import { runPipeline } from '@/lib/python/executor';

const connection = {
  host: process.env.REDIS_HOST,
  port: parseInt(process.env.REDIS_PORT || '6379'),
};

export const analysisQueue = new Queue('analysis', { connection });

// Worker (run in separate process)
export function startWorker() {
  const worker = new Worker(
    'analysis',
    async (job) => {
      const { symbols, withAI } = job.data;
      return runPipeline({ symbols, withAI });
    },
    { connection }
  );

  worker.on('completed', (job, result) => {
    console.log(`Job ${job.id} completed:`, result);
  });

  return worker;
}

// Enqueue analysis
export async function enqueueAnalysis(symbols: string[], withAI = false) {
  return analysisQueue.add('run', { symbols, withAI });
}
```

---

## Security Best Practices

### 1. Input Validation

```typescript
// lib/validation/symbols.ts
const VALID_SYMBOL_REGEX = /^[A-Z]{1,5}$/;

export function validateSymbols(input: string): string[] {
  return input
    .toUpperCase()
    .split(',')
    .map((s) => s.trim())
    .filter((s) => VALID_SYMBOL_REGEX.test(s))
    .slice(0, 10); // Limit to 10 symbols
}

export function sanitizeSymbol(symbol: string): string | null {
  const cleaned = symbol.toUpperCase().trim();
  return VALID_SYMBOL_REGEX.test(cleaned) ? cleaned : null;
}
```

### 2. Rate Limiting

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const rateLimit = new Map<string, { count: number; timestamp: number }>();

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/pipeline')) {
    const ip = request.ip || 'unknown';
    const now = Date.now();
    const windowMs = 60000; // 1 minute
    const maxRequests = 5;

    const record = rateLimit.get(ip);

    if (record && now - record.timestamp < windowMs) {
      if (record.count >= maxRequests) {
        return NextResponse.json(
          { error: 'Too many requests' },
          { status: 429 }
        );
      }
      record.count++;
    } else {
      rateLimit.set(ip, { count: 1, timestamp: now });
    }
  }

  return NextResponse.next();
}
```

### 3. Environment Variable Validation

```typescript
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  FIREBASE_PROJECT_ID: z.string().min(1),
  FIREBASE_CLIENT_EMAIL: z.string().email(),
  FIREBASE_PRIVATE_KEY: z.string().min(1),
  PYTHON_PIPELINE_PATH: z.string().min(1),
  REVALIDATION_SECRET: z.string().min(32),
});

export const env = envSchema.parse(process.env);
```

---

## Project Structure

```
app/
├── (dashboard)/
│   ├── layout.tsx          # Dashboard layout (server)
│   ├── page.tsx             # Dashboard home (server)
│   └── analysis/
│       └── [symbol]/
│           └── page.tsx     # Analysis detail (server)
├── api/
│   ├── pipeline/
│   │   └── route.ts         # Pipeline trigger endpoint
│   └── revalidate/
│       └── route.ts         # Cache revalidation webhook
├── actions/
│   └── analysis.ts          # Server actions
└── layout.tsx               # Root layout

components/
├── analysis/
│   ├── header.tsx           # Server component
│   ├── signal-list.tsx      # Server component
│   ├── indicator-grid.tsx   # Server component
│   └── ai-insights.tsx      # Server component
├── charts/
│   └── price-chart.tsx      # Client component ('use client')
├── forms/
│   └── symbol-search.tsx    # Client component ('use client')
├── realtime/
│   └── price-ticker.tsx     # Client component ('use client')
├── skeletons/
│   └── index.tsx            # Loading skeletons (server)
└── ui/
    └── submit-button.tsx    # Client component ('use client')

lib/
├── firebase-admin.ts        # Firebase singleton
├── env.ts                   # Environment validation
├── types/
│   └── analysis.ts          # Type definitions
├── repositories/
│   └── analysis-repository.ts
├── services/
│   └── analysis-service.ts
├── python/
│   └── executor.ts          # Python subprocess runner
├── validation/
│   └── symbols.ts           # Input validation
└── utils/
    └── format.ts            # Formatting helpers
```

---

## Summary Checklist

| Principle | Implementation |
|-----------|---------------|
| Server Components by default | All data fetching in page.tsx |
| Single Responsibility | Repository → Service → Component |
| Law of Demeter | Service layer aggregates data |
| Early Returns | Guard clauses in all functions |
| Type Safety | End-to-end TypeScript types |
| Minimal Client JS | Only charts, forms, real-time |
| Parallel Fetching | Promise.all in services |
| Streaming | Suspense boundaries |
| Caching | Route + fetch-level caching |
| Security | Validation, rate limiting, env checks |
| Tailwind CSS | Custom signal colors, responsive charts |
| Recharts | Client components with server data props |
| Adaptive Charts | SignalChartFactory auto-selects best viz |

---

## Quick Start Commands

```bash
# Create Next.js app with TypeScript
npx create-next-app@latest my-analysis-app --typescript --tailwind --app

# Install dependencies
cd my-analysis-app
npm install firebase-admin recharts

# Set up environment
cp .env.example .env.local
# Edit .env.local with your Firebase credentials

# Run development server
npm run dev
```

## File Structure Summary

```
components/
├── charts/
│   ├── base-chart.tsx              # 'use client' - ResponsiveContainer wrapper
│   ├── custom-tooltip.tsx          # 'use client' - Reusable tooltip
│   ├── signal-chart-factory.tsx    # Auto-selects chart type
│   ├── signal-radar-chart.tsx      # 'use client' - Multi-category overview
│   ├── signal-bar-chart.tsx        # 'use client' - Confidence ranking
│   ├── signal-category-pie.tsx     # 'use client' - Category distribution
│   ├── signal-confidence-gauge.tsx # 'use client' - Aggregate sentiment
│   ├── signal-strength-heatmap.tsx # 'use client' - Category × Strength grid
│   └── indicator-chart.tsx         # 'use client' - MA/MACD visualization
├── analysis/
│   ├── signal-charts-section.tsx   # Server - Adaptive chart layout
│   └── ...
lib/
├── charts/
│   └── theme.ts                    # Chart colors and config
├── utils/
│   └── tailwind.ts                 # Dynamic Tailwind utilities
```
