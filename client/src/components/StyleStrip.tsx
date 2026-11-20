import React, { useState } from 'react';
import { AESTHETIC_PRESETS } from '../static/constants';

interface StyleStripProps {
  /** Phrases currently steering the rack, in the order they were switched on. */
  active: string[];
  /** True before a search has produced a pool: there is nothing to rerank yet. */
  disabled?: boolean;
  /** True while a rerank is in flight, so chips do not stack requests. */
  busy?: boolean;
  onToggle: (phrase: string) => void;
}

/** Inactive presets shown while the strip is collapsed; the rest sit behind "＋ more". */
const COLLAPSED_PRESETS = 4;

/**
 * Global aesthetic steering, deliberately outside the per-item Tune sheet: a phrase
 * applies to the whole rack, so the control lives under the search filters and stays
 * visible whether or not a sheet is open. Chips are absolute (tap = steer toward the
 * phrase, tap again = remove it); "＋ more" reveals the full preset list and free text.
 */
const StyleStrip: React.FC<StyleStripProps> = ({ active, disabled = false, busy = false, onToggle }) => {
  const [expanded, setExpanded] = useState(false);
  const [draft, setDraft] = useState('');
  const locked = disabled || busy;

  const isActive = (phrase: string) => active.some(a => a.toLowerCase() === phrase.toLowerCase());

  // Active phrases always stay visible; only the inactive presets are trimmed.
  const inactive = AESTHETIC_PRESETS.filter(preset => !isActive(preset));
  const shown = expanded ? inactive : inactive.slice(0, COLLAPSED_PRESETS);

  const addDraft = () => {
    const phrase = draft.trim();
    if (!phrase || isActive(phrase)) return;
    onToggle(phrase);
    setDraft('');
  };

  return (
    <div className={`style-strip${disabled ? ' is-disabled' : ''}`}>
      <div className="style-strip-row">
        <span className="style-strip-label">Style</span>

        <div className="style-chips">
          {active.map(phrase => (
            <button
              key={phrase}
              type="button"
              className="style-chip on"
              aria-pressed="true"
              aria-label={`Remove ${phrase}`}
              title={`Remove ${phrase}`}
              disabled={locked}
              onClick={() => onToggle(phrase)}
            >
              {phrase} <span aria-hidden="true">✕</span>
            </button>
          ))}

          {shown.map(phrase => (
            <button
              key={phrase}
              type="button"
              className="style-chip"
              aria-pressed="false"
              disabled={locked}
              onClick={() => onToggle(phrase)}
            >
              {phrase}
            </button>
          ))}

          <button
            type="button"
            className="style-chip more"
            aria-expanded={expanded}
            disabled={locked}
            onClick={() => setExpanded(value => !value)}
          >
            {expanded ? '× close' : '＋ more'}
          </button>
        </div>
      </div>

      {expanded && (
        <form
          className="style-form"
          onSubmit={(event) => {
            event.preventDefault();
            addDraft();
          }}
        >
          <input
            className="style-input"
            type="text"
            autoComplete="off"
            placeholder="Any words work — e.g. quiet luxury, 90s minimal"
            aria-label="Style phrase"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button type="submit" className="style-add" disabled={locked || !draft.trim()}>
            Add
          </button>
        </form>
      )}
    </div>
  );
};

export default StyleStrip;
