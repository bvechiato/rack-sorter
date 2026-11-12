import React, { useEffect, useRef, useState } from 'react';
import { components } from '../../types/api';
import { TRAITS, Trait } from '../../static/constants';
import TraitRadar from './TraitRadar';

type ItemResponse = components['schemas']['ItemResponse'];
type TraitProfile = components['schemas']['TraitProfileResponse'];
type Direction = 'MORE' | 'LESS';

interface TraitSheetProps {
  item: ItemResponse;
  /** Fired for the item's tapped trait; the parent replays the whole history. */
  onFeedback: (trait: Trait, direction: Direction) => Promise<void>;
  /** Traits already applied to this item, so reopening the sheet reflects them. */
  appliedPicks?: Partial<Record<Trait, Direction>>;
  /** Items appended by the last feedback's extra catalogue page. */
  newItems?: number;
  /** Debug view of the scorer's current axis positions. */
  profile?: TraitProfile | null;
  profileError?: string | null;
  onClose: () => void;
}

const TraitSheet: React.FC<TraitSheetProps> = ({
  item,
  onFeedback,
  appliedPicks,
  newItems = 0,
  profile,
  profileError,
  onClose,
}) => {
  // Last choice per trait, mirrored from what was sent. The history is append-only,
  // so tapping the opposite polarity changes the stored intent rather than removing it.
  const [picks, setPicks] = useState<Partial<Record<Trait, Direction>>>(appliedPicks ?? {});
  const [busyTrait, setBusyTrait] = useState<Trait | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAxes, setShowAxes] = useState(false);
  const sheetRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const returnFocusTo = document.activeElement as HTMLElement | null;

    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    sheetRef.current?.focus();

    return () => {
      document.removeEventListener('keydown', onKey);
      // Return focus to the Tune trigger so keyboard users do not lose their place.
      if (returnFocusTo && document.contains(returnFocusTo)) returnFocusTo.focus();
    };
  }, [onClose]);

  const pick = async (trait: Trait, direction: Direction) => {
    if (busyTrait || picks[trait] === direction) return;

    const previous = picks[trait];
    setPicks(prev => ({ ...prev, [trait]: direction }));
    setBusyTrait(trait);
    setError(null);
    try {
      await onFeedback(trait, direction);
    } catch (err: any) {
      setError(err?.message || 'Could not apply that adjustment.');
      // Restore the last applied choice, not just "nothing", since the server still
      // holds it: a failed − after a successful + must not look like a cleared trait.
      setPicks(prev => {
        const next = { ...prev };
        if (previous) next[trait] = previous;
        else delete next[trait];
        return next;
      });
    } finally {
      setBusyTrait(null);
    }
  };

  const active = Object.entries(picks) as [Trait, Direction][];
  const rawScore = item.rerank_score ?? item.similarity_score ?? 0;
  // Trait bonuses can push the blended score past 1; the badge stays a percentage.
  const matchLabel = `${(Math.min(1, Math.max(0, rawScore)) * 100).toFixed(0)}% match`;

  return (
    <div className="trait-sheet-root">
      <div className="trait-sheet-scrim" onClick={onClose} aria-hidden="true" />

      <section
        className="trait-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="trait-sheet-title"
        tabIndex={-1}
        ref={sheetRef}
      >
        <div className="trait-sheet-grabber" aria-hidden="true" />

        <div className="trait-sheet-scroll">
          <header className="trait-sheet-head">
            <img className="trait-sheet-thumb" src={item.image_url} alt="" />
            <div className="trait-sheet-heading">
              <div className="trait-sheet-title" id="trait-sheet-title">{item.title}</div>
              <div className="trait-sheet-meta">{matchLabel}</div>
            </div>
            <button className="trait-sheet-close" onClick={onClose} aria-label="Close">✕</button>
          </header>

          <p className="trait-sheet-caption">More or less of a trait on this item</p>

          <div className="trait-sheet-list">
            {TRAITS.map(trait => (
              <div className="trait-row" key={trait.key}>
                <div className="trait-row-label">
                  {trait.label}
                  {trait.beta && <span className="trait-row-tag">beta</span>}
                </div>

                <div className="trait-pair">
                  <button
                    type="button"
                    className={`tbtn plus ${picks[trait.key] === 'MORE' ? 'active' : ''}`}
                    aria-pressed={picks[trait.key] === 'MORE'}
                    aria-label={`More ${trait.label.toLowerCase()}`}
                    disabled={busyTrait !== null}
                    onClick={() => pick(trait.key, 'MORE')}
                  >
                    ＋
                  </button>
                  <button
                    type="button"
                    className={`tbtn minus ${picks[trait.key] === 'LESS' ? 'active' : ''}`}
                    aria-pressed={picks[trait.key] === 'LESS'}
                    aria-label={`Less ${trait.label.toLowerCase()}`}
                    disabled={busyTrait !== null}
                    onClick={() => pick(trait.key, 'LESS')}
                  >
                    −
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="trait-axes-toggle"
            aria-expanded={showAxes}
            onClick={() => setShowAxes(value => !value)}
          >
            <span aria-hidden="true">{showAxes ? '▾' : '▸'}</span> Trait axes <span className="trait-axes-debug">debug</span>
          </button>

          {showAxes && (
            profileError ? (
              <p className="trait-axes-error" role="status">Axes unavailable: {profileError}</p>
            ) : profile ? (
              <TraitRadar profile={profile} />
            ) : (
              <p className="trait-axes-empty" role="status">Axes appear once results are ranked.</p>
            )
          )}
        </div>

        <footer className="trait-sheet-foot">
          <div className="trait-sheet-status" role="status" aria-live="polite">
            {error ? (
              <span className="trait-sheet-error">{error}</span>
            ) : busyTrait ? (
              'Updating results…'
            ) : (
              <>
                <div>
                  {active.length ? (
                    <>
                      <b>Applying:</b>{' '}
                      {active
                        .map(([key, direction]) => `${direction === 'MORE' ? '+' : '−'} ${key}`)
                        .join(', ')}
                    </>
                  ) : (
                    'No trait selected'
                  )}
                </div>
                {newItems > 0 && (
                  <div className="trait-sheet-new">
                    +{newItems} new item{newItems === 1 ? '' : 's'} from a wider search
                  </div>
                )}
              </>
            )}
          </div>
          <button className="trait-sheet-done" onClick={onClose}>Done</button>
        </footer>
      </section>
    </div>
  );
};

export default TraitSheet;
