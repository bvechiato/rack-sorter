import React from 'react';
import { components } from '../../types/api';
import { TRAITS, Trait } from '../../static/constants';

type TraitProfile = components['schemas']['TraitProfileResponse'];

/** Mirrors `TRAIT_Z_LIMIT` in `server/service/traits.py`. */
const Z_LIMIT = 3;
/** The pool mean sits on this ring; ±Z_LIMIT maps to the centre and the outer edge. */
const MEAN_RADIUS = 0.5;

const SIZE = 240;
const CENTRE = SIZE / 2;
const RADIUS = 82;

interface TraitRadarProps {
  profile: TraitProfile;
  /** Uploaded anchor is drawn as the dashed reference shape. */
  label?: string;
}

interface Point {
  x: number;
  y: number;
}

function angleFor(index: number): number {
  // Start at 12 o'clock and go clockwise so the labels read naturally.
  return -Math.PI / 2 + (index * 2 * Math.PI) / TRAITS.length;
}

function toPoint(index: number, radiusRatio: number): Point {
  const angle = angleFor(index);
  const r = RADIUS * radiusRatio;
  return { x: CENTRE + r * Math.cos(angle), y: CENTRE + r * Math.sin(angle) };
}

/**
 * Convert a raw projection into the same z-score the scorer folds in, then place it on
 * this trait's spoke: z = 0 sits on the mean ring, +3 on the outer ring, −3 at the centre.
 */
function radiusFor(profile: TraitProfile, trait: Trait, value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) return MEAN_RADIUS;
  const std = profile.std[trait] ?? 0;
  const mean = profile.mean[trait] ?? 0;
  const z = std > 1e-9 ? (value - mean) / std : 0;
  const clamped = Math.max(-Z_LIMIT, Math.min(Z_LIMIT, z));
  return Math.max(0, Math.min(1, MEAN_RADIUS + clamped / (2 * Z_LIMIT)));
}

function polygon(profile: TraitProfile, values: Record<string, number> | null | undefined): string {
  return TRAITS.map((trait, index) =>
    Object.values(toPoint(index, radiusFor(profile, trait.key, values?.[trait.key]))).join(',')
  ).join(' ');
}

const TraitRadar: React.FC<TraitRadarProps> = ({ profile, label = 'your photo' }) => {
  const hasItem = Boolean(profile.item);
  const description = [
    `Trait axes for ${profile.count} candidates, top ${profile.top_n}.`,
    hasItem ? 'The clicked item is outlined.' : '',
  ].filter(Boolean).join(' ');

  return (
    <figure className="trait-radar">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} role="img" aria-label={description}>
        {/* Outer ±3σ ring and the pool-mean reference ring. */}
        <polygon className="trait-radar-grid" points={TRAITS.map((_, i) => Object.values(toPoint(i, 1)).join(',')).join(' ')} />
        <polygon
          className="trait-radar-mean"
          points={TRAITS.map((_, i) => Object.values(toPoint(i, MEAN_RADIUS)).join(',')).join(' ')}
        />

        {TRAITS.map((trait, index) => {
          const spoke = toPoint(index, 1);
          const labelPoint = toPoint(index, 1.17);
          return (
            <g key={trait.key}>
              <line className="trait-radar-spoke" x1={CENTRE} y1={CENTRE} x2={spoke.x} y2={spoke.y} />
              <text
                className="trait-radar-label"
                x={labelPoint.x}
                y={labelPoint.y}
                textAnchor={labelPoint.x < CENTRE - 1 ? 'end' : labelPoint.x > CENTRE + 1 ? 'start' : 'middle'}
                dominantBaseline="middle"
              >
                {trait.label}
              </text>
            </g>
          );
        })}

        {/* Where the uploaded photo sits on each axis. */}
        <polygon className="trait-radar-anchor" points={polygon(profile, profile.anchor)} />

        {/* What the ranker currently prefers: the mean profile of the visible top N. */}
        <polygon className="trait-radar-top" points={polygon(profile, profile.top)} />

        {hasItem && (
          <>
            <polygon className="trait-radar-item" points={polygon(profile, profile.item)} />
            {TRAITS.map((trait, index) => {
              const point = toPoint(index, radiusFor(profile, trait.key, profile.item?.[trait.key]));
              return <circle key={trait.key} className="trait-radar-dot" cx={point.x} cy={point.y} r={3.2} />;
            })}
          </>
        )}

        <circle className="trait-radar-origin" cx={CENTRE} cy={CENTRE} r={2} />
      </svg>

      <figcaption className="trait-radar-legend">
        <span><i className="swatch swatch-top" /> Top {profile.top_n}</span>
        <span><i className="swatch swatch-anchor" /> {label}</span>
        {hasItem && <span><i className="swatch swatch-item" /> Clicked</span>}
        <span className="trait-radar-hint">centre = −3σ · ring = mean · edge = +3σ</span>
      </figcaption>
    </figure>
  );
};

export default TraitRadar;
