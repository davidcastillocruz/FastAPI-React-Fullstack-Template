import { act, render } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import { setReducedMotion } from '@/test/matchMedia';

import SplitFlap from './SplitFlap';

// The character on each cell: the first child of a cell, the second one is the flap folding away
function cells(container) {
  return [...container.firstElementChild.children].map((cell) => cell.firstElementChild.textContent).join('');
}

afterEach(() => vi.useRealTimers());

describe('SplitFlap', () => {
  test('the flaps fall until they show the text, in uppercase and padded to the length', () => {
    vi.useFakeTimers();
    const { container } = render(<SplitFlap text="Ab1" length={5} />);
    expect(cells(container)).toBe('     ');

    act(() => vi.runAllTimers());

    expect(cells(container)).toBe('AB1  ');
  });

  test('a text longer than the board is cut with an ellipsis', () => {
    vi.useFakeTimers();
    const { container } = render(<SplitFlap text="departures" length={5} />);

    act(() => vi.runAllTimers());

    expect(cells(container)).toBe('DEPA…');
  });

  test('a new text replaces the one on the board', () => {
    vi.useFakeTimers();
    const { container, rerender } = render(<SplitFlap text="ab" length={2} />);
    act(() => vi.runAllTimers());

    rerender(<SplitFlap text="cd" length={2} />);
    act(() => vi.runAllTimers());

    expect(cells(container)).toBe('CD');
  });

  test('with reduced motion the text shows at once, without flaps', () => {
    vi.useFakeTimers();
    setReducedMotion(true);
    const { container } = render(<SplitFlap text="ab" length={3} />);

    expect(cells(container)).toBe('AB ');
    // No flap is waiting to fall
    expect(vi.getTimerCount()).toBe(0);
    expect([...container.firstElementChild.children].every((cell) => cell.children.length === 1)).toBe(true);
  });

  test('the cells are hidden from screen readers, the page gives the real text', () => {
    const { container } = render(<SplitFlap text="ab" length={2} />);

    expect(container.firstElementChild.getAttribute('aria-hidden')).toBe('true');
  });
});
