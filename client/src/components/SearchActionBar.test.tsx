import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it } from 'vitest';
import SearchActionBar from './SearchActionBar';

// Uploads are single-flight: the picker must be unreachable while analysis runs, or two
// overlapping /analyze calls collapse into the one client-side session slot.

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

describe('SearchActionBar upload gating', () => {
  let container: HTMLDivElement | undefined;
  let root: Root | undefined;

  const render = (analyzing: boolean): HTMLInputElement => {
    if (!root) {
      container = document.createElement('div');
      document.body.appendChild(container);
      root = createRoot(container);
    }
    const activeRoot = root;
    act(() => {
      activeRoot.render(
        <SearchActionBar
          confirmedKeyword=""
          setConfirmedKeyword={() => {}}
          onImageUpload={() => {}}
          analyzing={analyzing}
        />,
      );
    });
    return container.querySelector('input[type="file"]') as HTMLInputElement;
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

  it('leaves the file input enabled when idle', () => {
    expect(render(false).disabled).toBe(false);
  });

  it('disables the file input only while analysis is in progress', () => {
    const input = render(false);
    expect(input.disabled).toBe(false);

    render(true);
    expect(input.disabled).toBe(true);

    render(false);
    expect(input.disabled).toBe(false);
  });
});
