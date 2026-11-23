import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import KeywordSuggestions from './KeywordSuggestions';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

describe('KeywordSuggestions', () => {
  let container: HTMLDivElement | undefined;
  let root: Root | undefined;

  const render = (keywords: string[], confirmedKeyword: string) => {
    if (!root) {
      container = document.createElement('div');
      document.body.appendChild(container);
      root = createRoot(container);
    }
    const activeRoot = root;
    act(() => {
      activeRoot.render(
        <KeywordSuggestions
          keywords={keywords}
          confirmedKeyword={confirmedKeyword}
          onSelectKeyword={vi.fn()}
        />,
      );
    });
    return Array.from(container.querySelectorAll('.chip'));
  };

  afterEach(() => {
    if (root) {
      const activeRoot = root;
      act(() => activeRoot.unmount());
    }
    container?.remove();
    container = undefined;
    root = undefined;
  });

  it('highlights the chip matching confirmedKeyword and follows prop changes', () => {
    const [first, second] = render(['striped', 'long sleeve'], 'striped');
    expect(first.className).toContain('selected');
    expect(second.className).not.toContain('selected');

    const [nextFirst, nextSecond] = render(['striped', 'long sleeve'], 'long sleeve');
    expect(nextFirst.className).not.toContain('selected');
    expect(nextSecond.className).toContain('selected');
  });
});
